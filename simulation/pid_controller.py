def clamp(value, minimum, maximum):
    return max(minimum, min(maximum, value))


class PIDController:
    def __init__(self, kp=1.0, ti=10.0, td=0.0, dt=0.2, out_min=0.0, out_max=100.0):
        self.kp = float(kp)
        self.ti = float(ti)
        self.td = float(td)
        self.dt = float(dt)
        self.out_min = float(out_min)
        self.out_max = float(out_max)
        self.integral = 0.0
        self.previous_error = None
        self.auto = True
        self.manual_output = 0.0

    def configure(self, kp=None, ti=None, td=None, auto=None, manual_output=None):
        if kp is not None:
            self.kp = float(kp)
        if ti is not None:
            self.ti = max(0.0, float(ti))
        if td is not None:
            self.td = max(0.0, float(td))
        if auto is not None:
            self.auto = bool(auto)
        if manual_output is not None:
            self.manual_output = clamp(float(manual_output), self.out_min, self.out_max)

    def reset(self):
        self.integral = 0.0
        self.previous_error = None

    def compute(self, pv, setpoint=None):
        if not self.auto:
            return self.manual_output
        error = float(setpoint) - float(pv)
        if self.previous_error is None:
            derivative = 0.0
        else:
            derivative = (error - self.previous_error) / self.dt
        integral_candidate = self.integral + error * self.dt if self.ti > 0 else self.integral
        term_i = self.kp * integral_candidate / self.ti if self.ti > 0 else 0.0
        raw = self.kp * error + term_i + self.kp * self.td * derivative
        output = clamp(raw, self.out_min, self.out_max)
        saturated = raw != output
        if not saturated or error * raw <= 0:
            self.integral = integral_candidate
        self.previous_error = error
        return output
