# Instrument index

| Tag | Service | Range | Signal | Notes |
| --- | --- | --- | --- | --- |
| `LT-101` | Tank level | 0-100 % | 4-20 mA | Self-regulating, tau 12 s |
| `TT-201` | Heat exchanger outlet temperature | 20-120 °C | 4-20 mA | tau 25 s, dead time 4 s |
| `FT-301` | Pipeline flow | 0-200 m3/h | 4-20 mA | Fast loop, tau 3 s |
| `PT-401` | Vessel pressure | 0-10 bar | 4-20 mA | tau 8 s |
| `FV-301` | Flow control valve | 0-100 % | Analog command | Fail-close |
| `TV-201` | Steam valve | 0-100 % | Analog command | Fail-close |

## Transmitter fault modes

| Mode | Effect |
| --- | --- |
| `NONE` | Normal 4-20 mA output |
| `OPEN_CIRCUIT` | Loop current near 0 mA |
| `SHORT_CIRCUIT` | Loop current above 20 mA |
| `FROZEN` | Last valid current held |

## Nota (ES)

Los rangos son representativos y sirven para demostrar escalamiento y fallas; no corresponden a una planta real.
