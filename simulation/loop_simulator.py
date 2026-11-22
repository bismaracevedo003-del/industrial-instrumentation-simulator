from pid_controller import PIDController
from process_models import FOPDT
from transmitters import Transmitter
from tuning import suggest_tuning

LOOPS = {
    'FT-301': {
        'description': 'Pipeline flow',
        'unit': 'm3/h',
        'gain': 1.2,
        'tau': 3.0,
        'dead_time': 0.5,
        'lrv': 0.0,
        'urv': 200.0,
        'initial_pv': 20.0,
        'setpoint': 120.0,
        'kp': 1.8,
        'ti': 4.0,
        'td': 0.0,
    },
    'LT-101': {
        'description': 'Tank level',
        'unit': '%',
        'gain': 0.8,
        'tau': 12.0,
        'dead_time': 1.0,
        'lrv': 0.0,
        'urv': 100.0,
        'initial_pv': 25.0,
        'setpoint': 60.0,
        'kp': 2.2,
        'ti': 18.0,
        'td': 0.0,
    },
    'TT-201': {
        'description': 'Heat exchanger temperature',
        'unit': 'degC',
        'gain': 0.6,
        'tau': 25.0,
        'dead_time': 4.0,
        'lrv': 20.0,
        'urv': 120.0,
        'initial_pv': 35.0,
        'setpoint': 80.0,
        'kp': 3.0,
        'ti': 40.0,
        'td': 6.0,
    },
    'PT-401': {
        'description': 'Vessel pressure',
        'unit': 'bar',
        'gain': 0.5,
        'tau': 8.0,
        'dead_time': 1.5,
        'lrv': 0.0,
        'urv': 10.0,
        'initial_pv': 1.5,
        'setpoint': 6.0,
        'kp': 4.0,
        'ti': 12.0,
        'td': 0.0,
    },
}


def clamp(value, minimum, maximum):
    return max(minimum, min(maximum, float(value)))


class LoopSimulator:
    def __init__(self, name='FT-301'):
        self.set_loop(name)

    def set_loop(self, name):
        if name not in LOOPS:
            raise ValueError(f'unknown loop: {name}')
        cfg = LOOPS[name]
        self.name = name
        self.cfg = cfg
        self.process = FOPDT(cfg['gain'], cfg['tau'], cfg['dead_time'], cfg['initial_pv'])
        self.transmitter = Transmitter(cfg['lrv'], cfg['urv'])
        self.pid = PIDController(cfg['kp'], cfg['ti'], cfg['td'])
        self.setpoint = cfg['setpoint']
        self.manual_output = 0.0
        self.disturbance = 0.0
        self.fault = 'NONE'
        self.true_pv = cfg['initial_pv']
        self.output = 0.0
        self.time_s = 0.0
        self.trend = []
        self.transmitter.update(self.true_pv, self.fault)

    def configure(self, data):
        if 'setpoint' in data:
            self.setpoint = clamp(data['setpoint'], self.cfg['lrv'], self.cfg['urv'])
        if 'manual_output' in data:
            self.manual_output = clamp(data['manual_output'], 0, 100)
        if 'disturbance' in data:
            self.disturbance = clamp(data['disturbance'], -50, 50)
        if 'fault' in data:
            fault = str(data['fault']).upper()
            self.transmitter.update(self.true_pv, fault)
            self.fault = fault
        self.pid.configure(
            kp=data.get('kp'),
            ti=data.get('ti'),
            td=data.get('td'),
            auto=data.get('auto'),
            manual_output=data.get('manual_output'),
        )

    def tune(self, method):
        suggestion = suggest_tuning(method, self.cfg['gain'], self.cfg['tau'], self.cfg['dead_time'])
        self.pid.configure(kp=suggestion['Kp'], ti=suggestion['Ti'], td=suggestion['Td'])
        return suggestion

    def tick(self, dt=0.2):
        measured = self.transmitter.pv
        self.output = self.pid.compute(measured, self.setpoint) if self.pid.auto else self.manual_output
        self.true_pv = self.process.step(self.output, self.disturbance, dt)
        reading = self.transmitter.update(self.true_pv, self.fault)
        self.time_s += dt
        self.trend.append({
            't': round(self.time_s, 1),
            'pv': round(reading['pv'], 3),
            'sp': round(self.setpoint, 3),
            'out': round(self.output, 3),
            'ma': reading['current_ma'],
        })
        if len(self.trend) > 200:
            self.trend.pop(0)

    def state(self):
        return {
            'loop': self.name,
            'description': self.cfg['description'],
            'unit': self.cfg['unit'],
            'lrv': self.cfg['lrv'],
            'urv': self.cfg['urv'],
            'process_gain': self.cfg['gain'],
            'tau': self.cfg['tau'],
            'dead_time': self.cfg['dead_time'],
            'setpoint': round(self.setpoint, 3),
            'pv': round(self.transmitter.pv, 3),
            'true_pv': round(self.true_pv, 3),
            'output': round(self.output, 3),
            'current_ma': self.transmitter.current_ma,
            'fault': self.fault,
            'fault_detected': self.transmitter.fault_detected,
            'auto': self.pid.auto,
            'kp': round(self.pid.kp, 3),
            'ti': round(self.pid.ti, 3),
            'td': round(self.pid.td, 3),
            'disturbance': self.disturbance,
            'time_s': round(self.time_s, 1),
            'trend': self.trend,
            'source': 'simulator',
        }
