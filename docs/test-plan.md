# Test plan

## 1. Cases

| ID | Case | Expected | Status |
| --- | --- | --- | --- |
| T-01 | 4 mA → LRV | Minimum engineering value | Pass |
| T-02 | 20 mA → URV | Maximum engineering value | Pass |
| T-03 | 12 mA → midpoint | Mid-scale value | Pass |
| T-04 | PV → current round trip | Returns original value within tolerance | Pass |
| T-05 | Open circuit | Fault flag and current near 0 | Pass |
| T-06 | Short circuit | Fault flag and current above 20 mA | Pass |
| T-07 | Frozen transmitter | Output held while process changes | Pass |
| T-08 | FOPDT first-order response | PV moves toward steady state | Pass |
| T-09 | Dead time | No response before dead time elapses | Pass |
| T-10 | Disturbance | PV deviates then recovers with PID | Pass |
| T-11 | PI step response | PV approaches setpoint | Pass |
| T-12 | Anti-windup | Integral does not explode while saturated | Pass |
| T-13 | Manual/auto | Manual output respected; auto returns to PID | Pass |
| T-14 | Ziegler-Nichols PI | Positive Kp/Ti | Pass |
| T-15 | Ziegler-Nichols PID | Positive Kp/Ti/Td | Pass |
| T-16 | Cohen-Coon PI | Positive Kp/Ti | Pass |
| T-17 | IMC PI | Positive Kp/Ti | Pass |
| T-18 | Invalid method | Raises ValueError | Pass |
| T-19 | REST state | HMI contract present | Pass |
| T-20 | REST config/tune | Config and tuning endpoints update state | Pass |

## 2. Command

```powershell
python -m unittest discover -s simulation/tests -v
```

## 3. Pending

- Connect real 4-20 mA loop and signal generator.
- Validate tuning formulas against a physical skid.
- Add integrating and interacting processes.

## 4. Ejecución real

```text
Ran 33 tests in 3.731s
OK
```

## 5. Nota (ES)

Todas las pruebas son automatizadas y usan datos simulados; no se presenta evidencia de hardware real.
