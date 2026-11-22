import argparse
import json
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from loop_simulator import LOOPS, LoopSimulator
from real_io_adapter import create_io_adapter

HMI_ROOT = Path(__file__).resolve().parent.parent / 'hmi'


class InstrumentationApplication:
    def __init__(self, port=4020, loop='FT-301'):
        self.simulator = create_io_adapter(loop)
        self.http = ThreadingHTTPServer(('127.0.0.1', port), InstrumentationHandler)
        self.http.app = self
        self.stop_event = threading.Event()
        self.thread = None

    @property
    def port(self):
        return self.http.server_address[1]

    def start(self):
        self.thread = threading.Thread(target=self.http.serve_forever, daemon=True)
        self.thread.start()
        simulation = threading.Thread(target=self._simulation_loop, daemon=True)
        simulation.start()
        return self

    def stop(self):
        self.stop_event.set()
        close = getattr(self.simulator, 'close', None)
        if close is not None:
            close()
        self.http.shutdown()
        self.http.server_close()

    def _simulation_loop(self):
        while not self.stop_event.is_set():
            self.simulator.tick(0.2)
            time.sleep(0.2)


class InstrumentationHandler(BaseHTTPRequestHandler):
    def log_message(self, *_args):
        pass

    def _send_json(self, payload, status=200):
        body = json.dumps(payload).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(body)

    def _send_file(self, filename):
        path = HMI_ROOT / filename
        if not path.is_file():
            self.send_error(404)
            return
        content = path.read_bytes()
        content_type = {
            '.html': 'text/html; charset=utf-8',
            '.js': 'text/javascript; charset=utf-8',
            '.css': 'text/css; charset=utf-8',
        }.get(path.suffix, 'application/octet-stream')
        self.send_response(200)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def do_GET(self):
        simulator = self.server.app.simulator
        if self.path == '/api/state':
            self._send_json(simulator.state())
            return
        if self.path == '/api/loops':
            self._send_json({'loops': list(LOOPS.keys())})
            return
        if self.path in ('/', '/index.html'):
            self._send_file('index.html')
            return
        if self.path == '/app.js':
            self._send_file('app.js')
            return
        if self.path == '/styles.css':
            self._send_file('styles.css')
            return
        self.send_error(404)

    def do_POST(self):
        length = int(self.headers.get('Content-Length', 0))
        try:
            body = json.loads(self.rfile.read(length) or b'{}')
        except json.JSONDecodeError:
            self._send_json({'error': 'invalid JSON'}, 400)
            return
        simulator = self.server.app.simulator
        try:
            if self.path == '/api/config':
                simulator.configure(body)
            elif self.path == '/api/tune':
                result = simulator.tune(body.get('method', 'IMC-PI'))
                self._send_json({'tuning': result, **simulator.state()})
                return
            elif self.path == '/api/reset':
                simulator.set_loop(body.get('loop', simulator.name))
            elif self.path == '/api/loop':
                simulator.set_loop(body.get('loop', simulator.name))
            else:
                self.send_error(404)
                return
        except (ValueError, TypeError) as error:
            self._send_json({'error': str(error)}, 400)
            return
        self._send_json(simulator.state())


def run_demo(duration, loop):
    simulator = LoopSimulator(loop)
    for step in range(int(duration / 0.2)):
        simulator.tick(0.2)
        if step % 25 == 0:
            state = simulator.state()
            print(json.dumps({
                't': state['time_s'],
                'sp': state['setpoint'],
                'pv': state['pv'],
                'out': state['output'],
                'ma': state['current_ma'],
            }))


def main():
    parser = argparse.ArgumentParser(description='Instrumentation and PID loop simulator')
    parser.add_argument('--port', type=int, default=4020)
    parser.add_argument('--loop', default='FT-301', choices=list(LOOPS.keys()))
    parser.add_argument('--duration', type=float, default=0.0)
    args = parser.parse_args()
    if args.duration > 0:
        run_demo(args.duration, args.loop)
        return
    app = InstrumentationApplication(port=args.port, loop=args.loop).start()
    print(f'Instrumentation HMI: http://127.0.0.1:{app.port}')
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        app.stop()


if __name__ == '__main__':
    main()
