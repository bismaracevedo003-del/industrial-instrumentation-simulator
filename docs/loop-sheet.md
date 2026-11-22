# Loop sheet — FT-301 flow loop

| Field | Value |
| --- | --- |
| Loop | FT-301 / FV-301 |
| Controlled variable | Pipeline flow |
| Range | 0-200 m3/h |
| Transmitter output | 4-20 mA |
| Valve | Fail-close, 0-100 % |
| Process gain | 1.2 (m3/h)/% |
| Time constant | 3 s |
| Dead time | 0.5 s |
| Initial tuning | PI, Kp 1.8, Ti 4 s |

## Wiring summary

```text
AI+ --- 250 ohm --- AI- (current loop)
AO+ --- valve positioner --- AO-
```

## Failure behavior

- Open circuit → PV below LRV, controller sees low flow.
- Short circuit → PV above URV, controller sees high flow.
- Frozen transmitter → PV stale while the real process keeps changing.

## Nota (ES)

La hoja de lazo se usa como ejemplo de documentación; en planta se completaría con tag de cable, Interruptor, fuente y sketch de loop.
