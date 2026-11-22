from collections import deque


class FOPDT:
    def __init__(self, gain, tau, dead_time, initial_pv=0.0, dt=0.2):
        self.gain = float(gain)
        self.tau = max(0.1, float(tau))
        self.dead_time = max(0.0, float(dead_time))
        self.dt = float(dt)
        self.bias = float(initial_pv)
        steps = max(0, int(round(self.dead_time / self.dt)))
        self.delay = deque([0.0] * steps)
        self.pv = float(initial_pv)

    def step(self, valve_percent, disturbance=0.0, dt=None):
        dt = self.dt if dt is None else float(dt)
        self.delay.append(float(valve_percent))
        delayed = self.delay.popleft() if self.delay else 0.0
        target = self.bias + self.gain * delayed + float(disturbance)
        alpha = dt / (self.tau + dt)
        self.pv += (target - self.pv) * alpha
        return self.pv
