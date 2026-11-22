const $ = (id) => document.getElementById(id);
let current = null;

async function api(path, options = {}) {
  const response = await fetch(path, {
    method: options.method || 'GET',
    headers: { 'Content-Type': 'application/json' },
    body: options.body ? JSON.stringify(options.body) : undefined,
  });
  return response.json();
}

function setValue(id, value) {
  const element = $(id);
  if (document.activeElement !== element) element.value = value;
}

function render(state) {
  current = state;
  $('pv').textContent = state.pv;
  $('spDisplay').textContent = state.setpoint;
  $('output').textContent = `${state.output} %`;
  $('ma').textContent = `${state.current_ma.toFixed(2)} mA`;
  $('unit').textContent = state.unit;
  $('alarm').textContent = state.fault_detected ? `FAULT: ${state.fault}` : 'NO FAULT';
  $('alarm').className = state.fault_detected ? 'alarm active' : 'alarm';
  $('tuningResult').textContent =
    `Process: K=${state.process_gain} tau=${state.tau} theta=${state.dead_time} · PID ${state.kp}/${state.ti}/${state.td}`;
  setValue('loop', state.loop);
  setValue('fault', state.fault);
  setValue('setpoint', state.setpoint);
  setValue('kp', state.kp);
  setValue('ti', state.ti);
  setValue('td', state.td);
  setValue('manual', Math.round(state.output));
  $('auto').checked = state.auto;
  drawTrend(state.trend);
}

function drawTrend(trend) {
  const canvas = $('trend');
  const ctx = canvas.getContext('2d');
  const w = canvas.width;
  const h = canvas.height;
  ctx.fillStyle = '#0b1220';
  ctx.fillRect(0, 0, w, h);
  if (!trend.length) return;
  const values = trend.flatMap((p) => [p.pv, p.sp]);
  const min = Math.min(...values);
  const max = Math.max(...values);
  const span = Math.max(1, max - min);
  const x = (index) => (index / Math.max(1, trend.length - 1)) * (w - 40) + 30;
  const y = (value) => h - 25 - ((value - min) / span) * (h - 50);
  ctx.strokeStyle = '#243650';
  ctx.lineWidth = 1;
  for (let i = 0; i <= 4; i += 1) {
    const gy = 25 + (i / 4) * (h - 50);
    ctx.beginPath(); ctx.moveTo(30, gy); ctx.lineTo(w - 10, gy); ctx.stroke();
  }
  const line = (key, color) => {
    ctx.strokeStyle = color;
    ctx.lineWidth = 2;
    ctx.beginPath();
    trend.forEach((point, index) => {
      const px = x(index);
      const py = key === 'out' ? h - 25 - (point.out / 100) * (h - 50) : y(point[key]);
      if (index === 0) ctx.moveTo(px, py); else ctx.lineTo(px, py);
    });
    ctx.stroke();
  };
  line('out', '#6c757d');
  line('sp', '#ffd166');
  line('pv', '#4cc9f0');
}

async function refresh() {
  render(await api('/api/state'));
}

async function configure(payload) {
  render(await api('/api/config', { method: 'POST', body: payload }));
}

['setpoint', 'kp', 'ti', 'td', 'manual', 'disturbance', 'fault'].forEach((id) => {
  $(id).onchange = () => {
    const value = id === 'fault' ? $(id).value : Number($(id).value);
    configure({ [id]: value });
  };
});

$('auto').onchange = () => configure({ auto: $('auto').checked });
$('loop').onchange = () => api('/api/loop', { method: 'POST', body: { loop: $('loop').value } }).then(render);
$('tune').onclick = () => api('/api/tune', { method: 'POST', body: { method: $('method').value } }).then(render);
$('reset').onclick = () => api('/api/reset', { method: 'POST', body: { loop: $('loop').value } }).then(render);

refresh();
setInterval(refresh, 500);
