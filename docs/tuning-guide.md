# Tuning guide

## 1. FOPDT model

```text
PV(s)/u(s) = K * exp(-theta s) / (tau s + 1)
```

- `K` = process gain
- `tau` = time constant
- `theta` = dead time

## 2. Implemented methods

### Ziegler-Nichols (open loop)

| Controller | Kp | Ti | Td |
| --- | --- | --- | --- |
| PI | `0.9*tau/(K*theta)` | `3.33*theta` | - |
| PID | `1.2*tau/(K*theta)` | `2*theta` | `0.5*theta` |

### Cohen-Coon (PI)

```text
Kp = (tau/(K*theta)) * (0.9 + theta/(12*tau))
Ti = theta * (30 + 3*theta/tau) / (9 + 20*theta/tau)
```

### IMC (lambda tuning)

```text
Kp = tau / (K * (lambda + theta))
Ti = tau
Td = theta / 2  (only for PID variant)
```

## 3. Practical notes

- Start with IMC for conservative tuning.
- Ziegler-Nichols is aggressive and useful for comparison.
- Verify anti-windup behavior after long saturation.
- Re-tune when valve stiction or sensor filtering changes.

## 4. Nota (ES)

Estas fórmulas son una introducción práctica; en planta se deben validar con pruebas de reacción y criterios de seguridad.
