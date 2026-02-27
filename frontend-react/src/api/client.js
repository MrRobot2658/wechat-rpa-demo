const BASE = import.meta.env.VITE_API_BASE || '';

function api(path) {
  const p = (BASE.replace(/\/$/, '') + '/api' + path);
  return p;
}

export async function getDevices() {
  const r = await fetch(api('/devices'));
  if (!r.ok) throw new Error(r.statusText || '请求失败');
  return r.json();
}

export async function getDevicesOnline() {
  const r = await fetch(api('/devices/online'));
  if (!r.ok) throw new Error(r.statusText || '请求失败');
  return r.json();
}

export async function getApps() {
  const r = await fetch(api('/apps'));
  if (!r.ok) throw new Error(r.statusText || '请求失败');
  return r.json();
}

export function deviceScreenUrl(deviceId) {
  return api(`/devices/${encodeURIComponent(deviceId)}/screen`) + '?t=';
}

/** 应用前缀: wechat | wework */
export async function getAppContacts(deviceId, prefix) {
  const r = await fetch(api(`/${prefix}/contacts`), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ device_id: deviceId }),
  })
  if (!r.ok) throw new Error(r.statusText || '请求失败')
  const json = await r.json()
  const list = json.data
  return Array.isArray(list) ? list : (list && typeof list === 'object' ? Object.values(list) : [])
}

export async function sendAppMessage(deviceId, prefix, contact, message) {
  const r = await fetch(api(`/${prefix}/send_message`), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ device_id: deviceId, contact, message }),
  })
  if (!r.ok) throw new Error(r.statusText || '请求失败')
  return r.json()
}

export async function readAppMessages(deviceId, prefix, contact, count = 20) {
  const r = await fetch(api(`/${prefix}/read_messages`), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ device_id: deviceId, contact, count }),
  })
  if (!r.ok) throw new Error(r.statusText || '请求失败')
  return r.json()
}
