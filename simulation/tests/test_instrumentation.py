import json
import sys
import time
import unittest
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from instruments_server import InstrumentationApplication  # noqa: E402
from loop_simulator import LoopSimulator  # noqa: E402
from pid_controller import PIDController  # noqa: E402
from process_models import FOPDT  # noqa: E402
from transmitters import (  # noqa: E402
    FAULT_FROZEN,
    FAULT_OPEN,
    FAULT_SHORT,
    Transmitter,
    current_to_pv,
    pv_to_current,
)
from tuning import cohen_coon, imc, suggest_tuning, ziegler_nichols  # noqa: E402


class TransmitterTests(unittest.TestCase):
    def test_four_ma_is_lrv(self):
        self.assertEqual(current_to_pv(4, 20, 120), 20)

    def test_twenty_ma_is_urv(self):
        self.assertEqual(current_to_pv(20, 20, 120), 120)

    def test_twelve_ma_is_midpoint(self):
        self.assertEqual(current_to_pv(12, 20, 120), 70)

    def test_pv_to_current_round_trip(self):
        current = pv_to_current(70, 20, 120)
        self.assertAlmostEqual(current, 12)
        self.assertAlmostEqual(current_to_pv(current, 20, 120), 70)

    def test_open_circuit_fault(self):
        transmitter = Transmitter(0, 100)
        reading = transmitter.update(50, FAULT_OPEN)
        self.assertEqual(reading['current_ma'], 0)
        self.assertTrue(reading['fault_detected'])
        self.assertLess(reading['pv'], 0)

    def test_short_circuit_fault(self):
        transmitter = Transmitter(0, 100)
        reading = transmitter.update(50, FAULT_SHORT)
        self.assertEqual(reading['current_ma'], 22)
        self.assertTrue(reading['fault_detected'])
        self.assertGreater(reading['pv'], 100)

    def test_frozen_fault_holds_last_value(self):
        transmitter = Transmitter(0, 100)
        transmitter.update(50)
        frozen = transmitter.update(90, FAULT_FROZEN)
        self.assertAlmostEqual(frozen['pv'], 50)
        self.assertFalse(frozen['fault_detected'])

    def test_invalid_fault_raises(self):
        with self.assertRaises(ValueError):
            Transmitter(0, 100).update(50, 'BAD')


class ProcessTests(unittest.TestCase):
    def test_first_order_response_moves_toward_target(self):
        process = FOPDT(gain=1, tau=2, dead_time=0)
        for _ in range(10):
            value = process.step(100)
        self.assertGreater(value, 0)
        self.assertLess(value, 100)

    def test_dead_time_delays_response(self):
        process = FOPDT(gain=1, tau=1, dead_time=1, dt=0.2)
        for _ in range(3):
            early = process.step(100)
        self.assertAlmostEqual(early, 0, places=6)
        for _ in range(7):
            late = process.step(100)
        self.assertGreater(late, 0)

    def test_disturbance_shifts_steady_state(self):
        process = FOPDT(gain=1, tau=1, dead_time=0)
        with_disturbance = FOPDT(gain=1, tau=1, dead_time=0)
        for _ in range(30):
            baseline = process.step(0)
            shifted = with_disturbance.step(0, disturbance=20)
        self.assertGreater(shifted, baseline)


class PIDTests(unittest.TestCase):
    def test_pi_step_response_approaches_setpoint(self):
        controller = PIDController(kp=1.8, ti=4)
        pv = 20.0
        for _ in range(200):
            output = controller.compute(pv, 120)
            pv += (20 + 1.2 * output - pv) * 0.2 / 3.2
        self.assertGreater(pv, 100)

    def test_anti_windup_limits_integral(self):
        controller = PIDController(kp=10, ti=1)
        for _ in range(100):
            controller.compute(0, 1000)
        self.assertLessEqual(controller.integral, 20)

    def test_manual_mode_returns_manual_output(self):
        controller = PIDController()
        controller.configure(auto=False, manual_output=37)
        self.assertEqual(controller.compute(50, 100), 37)

    def test_auto_after_manual_resumes_pid(self):
        controller = PIDController(kp=2, ti=5)
        controller.configure(auto=False, manual_output=80)
        controller.compute(50, 100)
        controller.configure(auto=True)
        self.assertGreater(controller.compute(50, 100), 0)

    def test_reset_clears_integral(self):
        controller = PIDController(kp=2, ti=5)
        controller.compute(0, 100)
        controller.reset()
        self.assertEqual(controller.integral, 0)


class TuningTests(unittest.TestCase):
    def test_ziegler_nichols_pi(self):
        result = ziegler_nichols(1.2, 3.0, 0.5, 'PI')
        self.assertGreater(result['Kp'], 0)
        self.assertGreater(result['Ti'], 0)
        self.assertEqual(result['Td'], 0)

    def test_ziegler_nichols_pid(self):
        result = ziegler_nichols(1.2, 3.0, 0.5, 'PID')
        self.assertGreater(result['Td'], 0)

    def test_cohen_coon(self):
        result = cohen_coon(1.2, 3.0, 0.5)
        self.assertGreater(result['Kp'], 0)
        self.assertGreater(result['Ti'], 0)

    def test_imc_pi(self):
        result = imc(1.2, 3.0, 0.5)
        self.assertGreater(result['Kp'], 0)
        self.assertEqual(result['Ti'], 3.0)

    def test_imc_pid(self):
        result = imc(1.2, 3.0, 0.5, controller='PID')
        self.assertGreater(result['Td'], 0)

    def test_suggest_tuning_unknown_method(self):
        with self.assertRaises(ValueError):
            suggest_tuning('XYZ', 1, 2, 0.5)

    def test_invalid_process_parameters(self):
        with self.assertRaises(ValueError):
            ziegler_nichols(0, 2, 0.5)


class LoopTests(unittest.TestCase):
    def test_loop_state_contract(self):
        state = LoopSimulator().state()
        for key in ('pv', 'setpoint', 'output', 'current_ma', 'trend', 'auto'):
            self.assertIn(key, state)

    def test_configure_setpoint_and_disturbance(self):
        loop = LoopSimulator()
        loop.configure({'setpoint': 90, 'disturbance': 10, 'kp': 2.5})
        self.assertEqual(loop.setpoint, 90)
        self.assertEqual(loop.disturbance, 10)
        self.assertEqual(loop.pid.kp, 2.5)

    def test_apply_tuning_changes_pid(self):
        loop = LoopSimulator()
        original = loop.pid.kp
        loop.tune('ZN-PI')
        self.assertNotEqual(loop.pid.kp, original)

    def test_unknown_loop_raises(self):
        with self.assertRaises(ValueError):
            LoopSimulator('XX-999')

    def test_trend_grows(self):
        loop = LoopSimulator()
        for _ in range(10):
            loop.tick()
        self.assertEqual(len(loop.trend), 10)

    def test_fault_reaches_state(self):
        loop = LoopSimulator()
        loop.configure({'fault': FAULT_OPEN})
        self.assertEqual(loop.state()['fault'], FAULT_OPEN)
        self.assertTrue(loop.state()['fault_detected'])


class HttpTests(unittest.TestCase):
    def setUp(self):
        self.app = InstrumentationApplication(port=0).start()
        time.sleep(0.4)

    def tearDown(self):
        self.app.stop()

    def get(self, path):
        with urllib.request.urlopen(f'http://127.0.0.1:{self.app.port}{path}') as response:
            return response.status, json.loads(response.read())

    def post(self, path, payload):
        request = urllib.request.Request(
            f'http://127.0.0.1:{self.app.port}{path}',
            data=json.dumps(payload).encode(),
            headers={'Content-Type': 'application/json'},
            method='POST',
        )
        with urllib.request.urlopen(request) as response:
            return json.loads(response.read())

    def test_hmi_page(self):
        with urllib.request.urlopen(f'http://127.0.0.1:{self.app.port}/') as response:
            self.assertEqual(response.status, 200)
            self.assertIn(b'Instrumentation', response.read())

    def test_api_state_and_loops(self):
        status, state = self.get('/api/state')
        self.assertEqual(status, 200)
        self.assertEqual(state['loop'], 'FT-301')
        _, loops = self.get('/api/loops')
        self.assertIn('TT-201', loops['loops'])

    def test_api_config_and_tune(self):
        self.post('/api/config', {'setpoint': 150, 'auto': False})
        state = self.post('/api/tune', {'method': 'IMC-PI'})
        self.assertEqual(state['setpoint'], 150)
        self.assertGreater(state['kp'], 0)

    def test_api_invalid_tuning_returns_400(self):
        request = urllib.request.Request(
            f'http://127.0.0.1:{self.app.port}/api/tune',
            data=json.dumps({'method': 'BAD'}).encode(),
            headers={'Content-Type': 'application/json'},
            method='POST',
        )
        with self.assertRaises(urllib.error.HTTPError) as context:
            urllib.request.urlopen(request)
        context.exception.close()


if __name__ == '__main__':
    unittest.main()
