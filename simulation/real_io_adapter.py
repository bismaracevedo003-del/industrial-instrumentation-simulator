import os

from loop_simulator import LoopSimulator
from transmitters import pv_to_current

SETTING_DEFAULTS = {
    'MODBUS_PORT': '502',
    'MODBUS_UNIT_ID': '1',
    'MODBUS_PV_REGISTER': '0',
    'MODBUS_OUTPUT_REGISTER': '1',
    'MODBUS_PV_SCALE': '0.1',
    'MODBUS_PV_OFFSET': '0',
    'MODBUS_OUTPUT_SCALE': '10',
    'MODBUS_TIMEOUT': '3',
    'MODBUS_REGISTER_TYPE': 'input',
}


def _boolean(name, default=False):
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in ('true', '1', 'yes', 'on')


def read_settings():
    settings = {}
    for name, default in SETTING_DEFAULTS.items():
        settings[name] = os.environ.get(name, default)
    settings['MODBUS_HOST'] = os.environ.get('MODBUS_HOST')
    settings['ALLOW_WRITES'] = _boolean('ALLOW_WRITES', False)
    return {
        'host': settings['MODBUS_HOST'],
        'port': int(settings['MODBUS_PORT']),
        'unit_id': int(settings['MODBUS_UNIT_ID']),
        'pv_register': int(settings['MODBUS_PV_REGISTER']),
        'output_register': int(settings['MODBUS_OUTPUT_REGISTER']),
        'pv_scale': float(settings['MODBUS_PV_SCALE']),
        'pv_offset': float(settings['MODBUS_PV_OFFSET']),
        'output_scale': float(settings['MODBUS_OUTPUT_SCALE']),
        'timeout': float(settings['MODBUS_TIMEOUT']),
        'register_type': settings['MODBUS_REGISTER_TYPE'].strip().lower(),
        'allow_writes': settings['ALLOW_WRITES'],
    }


class ModbusIOAdapter:
    def __init__(self, loop='FT-301', settings=None):
        self.simulator = LoopSimulator(loop)
        self.settings = settings or read_settings()
        self.client = None
        self.pv = self.simulator.true_pv
        self.output = 0.0
        self.time_s = 0.0
        self.trend = []

    def connect(self):
        if not self.settings['host']:
            raise RuntimeError('MODE=real requires MODBUS_HOST; real mode never uses the simulator')
        if self.settings['register_type'] not in ('input', 'holding'):
            raise RuntimeError(
                f"MODE=real invalid MODBUS_REGISTER_TYPE: {self.settings['register_type']}"
            )
        try:
            from pymodbus.client import ModbusTcpClient
        except ImportError as error:
            raise RuntimeError(
                'MODE=real Modbus I/O requires pymodbus; install it with: '
                'pip install -r requirements-real.txt'
            ) from error

        self.client = ModbusTcpClient(
            self.settings['host'],
            port=self.settings['port'],
            timeout=self.settings['timeout'],
        )
        if not self.client.connect():
            raise RuntimeError(
                f"MODE=real Modbus connection failed: {self.settings['host']}:{self.settings['port']}"
            )
        self.pv = self._read_pv()
        return self

    def tick(self, dt=0.2):
        self.pv = self._read_pv()
        reading = self._reading()
        self.output = (
            self.simulator.pid.compute(reading['pv'], self.simulator.setpoint)
            if self.simulator.pid.auto
            else self.simulator.manual_output
        )
        self.output = max(0.0, min(100.0, float(self.output)))
        if self.settings['allow_writes']:
            self._write_output()
        self.time_s += dt
        self.trend.append({
            't': round(self.time_s, 1),
            'pv': round(self.pv, 3),
            'sp': round(self.simulator.setpoint, 3),
            'out': round(self.output, 3),
            'ma': reading['current_ma'],
        })
        if len(self.trend) > 200:
            self.trend.pop(0)

    def configure(self, data):
        fault = data.get('fault')
        if fault is not None and str(fault).upper() != 'NONE':
            raise ValueError('fault injection is not available in real mode')
        self.simulator.configure(data)

    def tune(self, method):
        return self.simulator.tune(method)

    def set_loop(self, name):
        if name != self.simulator.name:
            raise ValueError('loop switching is not available in real mode; set MODBUS_LOOP')
        return self

    def state(self):
        state = self.simulator.state()
        reading = self._reading()
        state.update({
            'pv': round(self.pv, 3),
            'true_pv': round(self.pv, 3),
            'current_ma': reading['current_ma'],
            'fault': reading['fault'],
            'fault_detected': reading['fault_detected'],
            'output': round(self.output, 3),
            'time_s': round(self.time_s, 1),
            'trend': list(self.trend),
            'source': 'modbus',
            'writes_enabled': self.settings['allow_writes'],
        })
        return state

    def close(self):
        if self.client is not None:
            self.client.close()
            self.client = None

    def _reading(self):
        cfg = self.simulator.cfg
        current = pv_to_current(self.pv, cfg['lrv'], cfg['urv'])
        detected = current < 3.6 or current > 20.5
        return {
            'pv': round(self.pv, 3),
            'current_ma': round(current, 3),
            'fault': 'NONE',
            'fault_detected': detected,
        }

    def _read_pv(self):
        result = self._read_register(self.settings['pv_register'])
        return float(result.registers[0]) * self.settings['pv_scale'] + self.settings['pv_offset']

    def _read_register(self, address):
        method = (
            self.client.read_input_registers
            if self.settings['register_type'] == 'input'
            else self.client.read_holding_registers
        )
        result = method(address, count=1, slave=self.settings['unit_id'])
        if result.isError():
            raise RuntimeError(f'MODE=real Modbus read failed at register {address}: {result}')
        return result

    def _write_output(self):
        value = int(round(self.output * self.settings['output_scale']))
        result = self.client.write_register(
            self.settings['output_register'], value, slave=self.settings['unit_id']
        )
        if result.isError():
            raise RuntimeError(
                f"MODE=real Modbus write failed at register {self.settings['output_register']}: {result}"
            )


def create_io_adapter(loop='FT-301'):
    mode = (os.environ.get('MODE') or 'simulation').strip().lower()
    if mode == 'simulation':
        return LoopSimulator(loop)
    if mode != 'real':
        raise RuntimeError(f'Unsupported MODE: {mode} (use simulation or real)')

    name = os.environ.get('MODBUS_LOOP') or loop
    return ModbusIOAdapter(name, read_settings()).connect()
