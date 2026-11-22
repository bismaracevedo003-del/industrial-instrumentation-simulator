def ziegler_nichols(gain, tau, dead_time, controller='PI'):
    k = float(gain)
    tau = float(tau)
    theta = float(dead_time)
    if k <= 0 or tau <= 0 or theta <= 0:
        raise ValueError('K, tau and dead time must be positive')
    if controller == 'PI':
        return {'Kp': 0.9 * tau / (k * theta), 'Ti': 3.33 * theta, 'Td': 0.0}
    if controller == 'PID':
        return {'Kp': 1.2 * tau / (k * theta), 'Ti': 2.0 * theta, 'Td': 0.5 * theta}
    raise ValueError(f'unknown controller: {controller}')


def cohen_coon(gain, tau, dead_time):
    k = float(gain)
    tau = float(tau)
    theta = float(dead_time)
    if k <= 0 or tau <= 0 or theta <= 0:
        raise ValueError('K, tau and dead time must be positive')
    ratio = theta / tau
    kp = (tau / (k * theta)) * (0.9 + ratio / 12.0)
    ti = theta * (30.0 + 3.0 * ratio) / (9.0 + 20.0 * ratio)
    return {'Kp': kp, 'Ti': ti, 'Td': 0.0}


def imc(gain, tau, dead_time, lambda_factor=1.0, controller='PI'):
    k = float(gain)
    tau = float(tau)
    theta = float(dead_time)
    lam = max(0.1, float(lambda_factor) * tau)
    if k <= 0 or tau <= 0:
        raise ValueError('K and tau must be positive')
    if controller == 'PI':
        return {'Kp': tau / (k * (lam + theta)), 'Ti': tau, 'Td': 0.0}
    if controller == 'PID':
        return {'Kp': tau / (k * (lam + theta)), 'Ti': tau, 'Td': theta / 2.0}
    raise ValueError(f'unknown controller: {controller}')


METHODS = {
    'ZN-PI': lambda k, tau, theta: ziegler_nichols(k, tau, theta, 'PI'),
    'ZN-PID': lambda k, tau, theta: ziegler_nichols(k, tau, theta, 'PID'),
    'COHEN-COON': cohen_coon,
    'IMC-PI': lambda k, tau, theta: imc(k, tau, theta, 1.0, 'PI'),
    'IMC-PID': lambda k, tau, theta: imc(k, tau, theta, 1.0, 'PID'),
}


def suggest_tuning(method, gain, tau, dead_time):
    key = str(method).upper()
    if key not in METHODS:
        raise ValueError(f'unknown tuning method: {method}')
    values = METHODS[key](gain, tau, dead_time)
    return {name: round(value, 3) for name, value in values.items()}
