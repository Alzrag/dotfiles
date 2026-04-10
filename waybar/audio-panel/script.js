async function update() {
  const res = await fetch('/api/audio');
  const data = await res.json();
  document.getElementById('current-device').textContent = data.default_device;
  // Populate streams and visualizer
}
setInterval(update, 200);

