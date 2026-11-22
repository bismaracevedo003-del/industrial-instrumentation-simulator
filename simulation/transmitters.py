FAULT_NONE = 'NONE'
FAULT_OPEN = 'OPEN_CIRCUIT'
FAULT_SHORT = 'SHORT_CIRCUIT'
FAULT_FROZEN = 'FROZEN'

VALID_FAULTS = (FAULT_NONE, FAULT_OPEN, FAULT_SHORT, FAULT_FROZEN)


def current_to_pv(current_ma, lrv, urv):
    return lrv + (float(current_ma) - 4.0) / 16.0 * (urv - lrv)


def pv_to_current(pv, lrv, urv):
    return 4.0 + (float(pv) - lrv) / (urv - lrv) * 16.0


class Transmitter:
    def __init__(self, lrv, urv, low_fault_ma=3.6, high_fault_ma=20.5):
        self.lrv = float(lrv)
        self.urv = float(urv)
        self.low_fault_ma = low_fault_ma
        self.high_fault_ma = high_fault_ma
        self.fault = FAULT_NONE
        self.fault_detected = False
        self.last_current = 4.0
        self.current_ma = 4.0
        self.pv = self.lrv

    def update(self, true_pv, fault=FAULT_NONE):
        if fault not in VALID_FAULTS:
            raise ValueError(f'unknown fault: {fault}')
        self.fault = fault
        normal_current = pv_to_current(true_pv, self.lrv, self.urv)
        if fault == FAULT_OPEN:
            self.current_ma = 0.0
        elif fault == FAULT_SHORT:
            self.current_ma = 22.0
        elif fault == FAULT_FROZEN:
            self.current_ma = self.last_current
        else:
            self.current_ma = normal_current
            self.last_current = normal_current
        self.pv = current_to_pv(self.current_ma, self.lrv, self.urv)
        self.fault_detected = (
            self.current_ma < self.low_fault_ma or self.current_ma > self.high_fault_ma
        )
        return self.read()

    def read(self):
        return {
            'pv': round(self.pv, 3),
            'current_ma': round(self.current_ma, 3),
            'fault': self.fault,
            'fault_detected': self.fault_detected,
        }
