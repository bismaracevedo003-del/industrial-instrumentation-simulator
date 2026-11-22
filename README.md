# Industrial Instrumentation & Loop Tuning Simulator

**4-20 mA loops · FOPDT process models · PID control · Transmitter faults · Live trends**

Interactive simulator for industrial instrumentation: analog transmitters, control valves, first-order-plus-dead-time processes and PID tuning methods. Built to demonstrate practical loop analysis without requiring a physical process skid.

> **Nota (ES):** Proyecto 100 % simulado. Las curvas, fallas y respuestas son artificiales pero están modeladas con ecuaciones y documentadas.

---

## 1. Industrial problem

Instrumentation technicians and control engineers need to understand how transmitter scaling, dead time, valve behavior and PID parameters affect loop response before touching a live process.

## 2. Objectives

- Model 4-20 mA transmitters with open-circuit, short-circuit and frozen-output faults.
- Simulate self-regulating FOPDT processes for level, temperature, flow and pressure.
- Implement a PID controller with anti-windup and manual/auto transfer.
- Compare Ziegler-Nichols, Cohen-Coon and IMC tuning suggestions.
- Show live PV/SP/output trends and fault effects.

## 3. Architecture

```text
PID/controller -> valve (0-100%) -> FOPDT process -> transmitter (4-20 mA) -> PV feedback
       ^                                                                  |
       +------------------------------------------------------------------+
```

See [docs/architecture.md](docs/architecture.md), [docs/instrument-index.md](docs/instrument-index.md) and [docs/tuning-guide.md](docs/tuning-guide.md).

## 4. Components

| Layer | Technology |
| --- | --- |
| Process model | Python, FOPDT difference equations |
| Control | Python PID with anti-windup |
| Transmitter | Python 4-20 mA scaling and fault modes |
| HMI | Vanilla HTML/JS with canvas trend |
| Tests | Python `unittest` |

## 5. Run

```powershell
cd "C:\Users\Bismarck Acevedo\Documents\Github\industrial-instrumentation-simulator"
python -m unittest discover -s simulation/tests -v
python simulation/instruments_server.py
```

Test result: `Ran 33 tests ... OK`.

Open `http://127.0.0.1:4020`.

CLI demo:

```powershell
python simulation/instruments_server.py --duration 40
```

## 6. Documents

- [Architecture](docs/architecture.md)
- [Instrument index](docs/instrument-index.md)
- [Loop sheet](docs/loop-sheet.md)
- [Tuning guide](docs/tuning-guide.md)
- [Test plan](docs/test-plan.md)

## 7. Screenshots

- [Dashboard mockup](screenshots/dashboard.svg)
- [Loop diagram](screenshots/loop-diagram.svg)

## 8. Evidence matrix

| Item | Status |
| --- | --- |
| FOPDT process dynamics | Implemented and unit tested |
| 4-20 mA transmitter scaling and faults | Implemented and unit tested |
| PID anti-windup and manual/auto | Implemented and unit tested |
| Tuning methods | Implemented and unit tested |
| HMI trends | Synthetic data from Python model |

## 9. Limitations and future work

- No real transmitter, valve or process skid connected.
- FOPDT models are an approximation, not a high-fidelity hydraulic/thermal solver.
- Add integrating processes and dead-time compensation later.

## 10. Quality checklist

- [x] Industrial instrumentation problem defined
- [x] Loop diagrams and documents
- [x] Modular Python source
- [x] PID and transmitter simulation
- [x] Trend HMI
- [x] Automated tests
- [x] Screenshots
- [x] Complete README
- [x] Repository on `main`

---

**Author:** Bismarck Acevedo — Electronic Engineer, Industrial Automation & PLC Programming.
