# Instrumentation real I/O integration

## Default behavior (unchanged)

`MODE` defaults to `simulation`. `create_io_adapter()` returns a `LoopSimulator`, so the FOPDT
model, transmitter faults, PID tuning, HMI and all existing tests work exactly as before.

## Activating Modbus TCP real I/O

```powershell
pip install -r requirements-real.txt
$env:MODE='real'
$env:MODBUS_HOST='192.168.1.20'
python simulation/instruments_server.py
```

In `MODE=real`, `create_io_adapter()` builds `ModbusIOAdapter` and calls `connect()` before the
HTTP server starts:

- `MODBUS_HOST` is mandatory; `MODBUS_PORT`, `MODBUS_UNIT_ID` and register addresses have safe
  defaults shown in `config/real.env.example`.
- `pymodbus` is imported lazily inside `connect()`. A missing package, unreachable device or
  failed first register read raises a clear error. There is no silent simulation fallback.
- The PV is read from `MODBUS_PV_REGISTER` (`input` or `holding`) and scaled with
  `MODBUS_PV_SCALE` / `MODBUS_PV_OFFSET`. State keeps the existing HMI contract and adds
  `source: "modbus"` and `writes_enabled`.

The PID and tuning helpers are reused with the real PV. Controller output is written to
`MODBUS_OUTPUT_REGISTER` only when `ALLOW_WRITES=true`; otherwise the adapter is read-only.
Fault injection and loop switching are rejected in real mode with HTTP 400 responses.

## Real HMI/SCADA deployment

| Item | Recommendation for this repo |
| --- | --- |
| Host/port | Python serves the HMI/API on `127.0.0.1:4020`. Run it on an edge host that can reach the Modbus TCP device on port 502, but expose only the HTTP port to the plant network. |
| TLS / reverse proxy | Terminate HTTPS on nginx/Traefik (443) and proxy `/` and `/api/*` to 4020. Modbus TCP itself has no TLS here; keep it inside an isolated control VLAN or tunnel it through a secured gateway. |
| Authentication | Require SSO/basic auth at the reverse proxy. Restrict `POST /api/config`, `/api/tune` and `/api/loop` to instrumentation engineers; keep `ALLOW_WRITES=false` during commissioning. |
| Safety | E-stop, guards and two-hand controls are hardwired outside this software. A Modbus write from this adapter can never bypass a safety circuit, and real output writes remain opt-in. |

## Verification without a PLC

```powershell
python -m unittest discover -s simulation/tests -v
```

Tests leave `MODE` unset and never import `pymodbus`. To verify strict behavior, set `MODE=real`
without `MODBUS_HOST` and confirm startup fails instead of creating the simulator.
