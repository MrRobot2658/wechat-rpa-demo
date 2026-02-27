import { useState, useEffect, useRef } from 'react'
import {
  getDevices,
  getDevicesOnline,
  getApps,
  deviceScreenUrl,
  getAppContacts,
  sendAppMessage,
  readAppMessages,
} from './api/client'

function MenuItem({ active, label, onClick }) {
  return (
    <li>
      <button
        type="button"
        onClick={onClick}
        className={active ? 'active' : ''}
      >
        {label}
      </button>
    </li>
  )
}

function DevicesPanel() {
  const [devices, setDevices] = useState([])
  const [online, setOnline] = useState(new Set())
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    let cancelled = false
    async function load() {
      try {
        const [res, onRes] = await Promise.all([
          getDevices(),
          getDevicesOnline().catch(() => ({ data: [] })),
        ])
        if (cancelled) return
        const raw = res.data
        const list = Array.isArray(raw) ? raw : (raw && typeof raw === 'object' ? Object.values(raw) : [])
        setDevices(list)
        const onlineRaw = onRes.data
        setOnline(new Set(Array.isArray(onlineRaw) ? onlineRaw : []))
      } catch (e) {
        if (!cancelled) setError(e.message || '加载失败')
      } finally {
        if (!cancelled) setLoading(false)
      }
    }
    load()
    return () => { cancelled = true }
  }, [])

  if (loading) return <div className="flex items-center justify-center p-8 text-base-content/70">加载中…</div>
  if (error) return <div className="alert alert-error">{error}</div>

  return (
    <section>
      <h2 className="text-xl font-semibold mb-4">设备列表</h2>
      <div className="card bg-base-100 border border-base-300 shadow-sm">
        <div className="card-body p-4 overflow-x-auto">
          <table className="table table-zebra">
            <thead>
              <tr>
                <th>设备 ID</th>
                <th>名称</th>
                <th>API 地址</th>
                <th>状态</th>
              </tr>
            </thead>
            <tbody>
              {!Array.isArray(devices) || devices.length === 0 ? (
                <tr>
                  <td colSpan={4} className="text-base-content/60">暂无设备，请在 server/config/__init__.py 的 DEVICES 中配置</td>
                </tr>
              ) : (
                devices.map((d) => (
                  <tr key={d.id}>
                    <td><code className="font-mono text-xs bg-base-300 px-1.5 py-0.5 rounded">{d.id}</code></td>
                    <td>{d.name || d.id}</td>
                    <td><code className="font-mono text-xs bg-base-300 px-1.5 py-0.5 rounded">{d.api_base || '-'}</code></td>
                    <td>
                      <span className={`badge ${online.has(d.id) ? 'badge-success' : 'badge-error'}`}>
                        {online.has(d.id) ? '在线' : '离线'}
                      </span>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
          <p className="text-sm text-base-content/60 mt-3">在线状态通过请求设备 /api/status 判断。</p>
        </div>
      </div>
    </section>
  )
}

function AppsPanel() {
  const [apps, setApps] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    let cancelled = false
    getApps()
      .then((res) => {
        if (!cancelled) setApps(Array.isArray(res.data) ? res.data : [])
      })
      .catch((e) => {
        if (!cancelled) setError(e.message || '加载失败')
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })
    return () => { cancelled = true }
  }, [])

  if (loading) return <div className="flex items-center justify-center p-8 text-base-content/70">加载中…</div>
  if (error) return <div className="alert alert-error">{error}</div>

  return (
    <section>
      <h2 className="text-xl font-semibold mb-4">已注册应用</h2>
      <div className="card bg-base-100 border border-base-300 shadow-sm">
        <div className="card-body p-4">
          <p className="text-sm text-base-content/60 mb-4">
            每套应用对应一套 API：<code className="font-mono text-xs bg-base-300 px-1.5 py-0.5 rounded">/api/&lt;prefix&gt;/contacts</code>、<code className="font-mono text-xs bg-base-300 px-1.5 py-0.5 rounded">send_message</code>、
            <code className="font-mono text-xs bg-base-300 px-1.5 py-0.5 rounded">read_messages</code>、<code className="font-mono text-xs bg-base-300 px-1.5 py-0.5 rounded">create_group</code> 等。
          </p>
          <div className="overflow-x-auto">
            <table className="table table-zebra">
              <thead>
                <tr>
                  <th>路径前缀</th>
                  <th>app_type</th>
                  <th>展示名</th>
                </tr>
              </thead>
              <tbody>
                {!Array.isArray(apps) || apps.length === 0 ? (
                  <tr><td colSpan={3} className="text-base-content/60">暂无应用</td></tr>
                ) : (
                  (apps || []).map((a) => (
                    <tr key={a.prefix}>
                      <td><code className="font-mono text-xs bg-base-300 px-1.5 py-0.5 rounded">/api/{a.prefix}/*</code></td>
                      <td><code className="font-mono text-xs bg-base-300 px-1.5 py-0.5 rounded">{a.app_type}</code></td>
                      <td>{a.label}</td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </section>
  )
}

/** 微信 / 企业微信：联系人列表 + 聊天 */
function ImAppPanel({ prefix, label }) {
  const [devices, setDevices] = useState([])
  const [deviceId, setDeviceId] = useState('')
  const [contacts, setContacts] = useState([])
  const [contactsLoading, setContactsLoading] = useState(false)
  const [contactsError, setContactsError] = useState(null)
  const [selectedContact, setSelectedContact] = useState(null)
  const [messages, setMessages] = useState([])
  const [messagesLoading, setMessagesLoading] = useState(false)
  const [sendText, setSendText] = useState('')
  const [sending, setSending] = useState(false)
  const [sendError, setSendError] = useState(null)
  const messagesEndRef = useRef(null)

  useEffect(() => {
    getDevices()
      .then((res) => {
        const raw = res.data
        const list = Array.isArray(raw) ? raw : (raw && typeof raw === 'object' ? Object.values(raw) : [])
        setDevices(list)
        if (list.length && !deviceId) setDeviceId(list[0].id)
      })
      .catch(() => setDevices([]))
  }, [])

  useEffect(() => {
    if (!deviceId) {
      setContacts([])
      return
    }
    setContactsLoading(true)
    setContactsError(null)
    getAppContacts(deviceId, prefix)
      .then((list) => {
        setContacts(Array.isArray(list) ? list : [])
      })
      .catch((e) => {
        setContactsError(e.message || '加载联系人失败')
        setContacts([])
      })
      .finally(() => setContactsLoading(false))
  }, [deviceId, prefix])

  useEffect(() => {
    if (!selectedContact || !deviceId) {
      setMessages([])
      return
    }
    setMessagesLoading(true)
    readAppMessages(deviceId, prefix, selectedContact, 30)
      .then((res) => {
        const data = res.data
        let list = data?.data
        if (typeof list === 'string') {
          try {
            list = JSON.parse(list)
          } catch {
            list = []
          }
        }
        if (Array.isArray(list)) setMessages(list)
        else if (data && Array.isArray(data)) setMessages(data)
        else setMessages([])
      })
      .catch(() => setMessages([]))
      .finally(() => setMessagesLoading(false))
  }, [deviceId, prefix, selectedContact])

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const handleSend = async () => {
    const text = sendText.trim()
    if (!text || !deviceId || !selectedContact || sending) return
    setSending(true)
    setSendError(null)
    try {
      await sendAppMessage(deviceId, prefix, selectedContact, text)
      setSendText('')
      const res = await readAppMessages(deviceId, prefix, selectedContact, 30)
      const data = res.data
      let list = data?.data
      if (typeof list === 'string') {
        try {
          list = JSON.parse(list)
        } catch {
          list = []
        }
      }
      if (Array.isArray(list)) setMessages(list)
    } catch (e) {
      setSendError(e.message || '发送失败')
    } finally {
      setSending(false)
    }
  }

  return (
    <section>
      <h2 className="text-xl font-semibold mb-4">{label}</h2>
      <div className="card bg-base-100 border border-base-300 shadow-sm mb-4">
        <div className="card-body p-4">
          <label className="label-text mb-2">选择设备</label>
          <select
            className="select select-bordered select-sm w-48"
            value={deviceId}
            onChange={(e) => setDeviceId(e.target.value)}
          >
            <option value="">请选择设备</option>
            {(Array.isArray(devices) ? devices : []).map((d) => (
              <option key={d.id} value={d.id}>{d.name || d.id}</option>
            ))}
          </select>
        </div>
      </div>
      <div className="flex gap-4 flex-1 min-h-0">
        <div className="card bg-base-100 border border-base-300 shadow-sm w-64 shrink-0 flex flex-col">
          <div className="card-body p-2">
            <h3 className="font-medium text-sm text-base-content/80 px-2 py-1">联系人</h3>
            {contactsLoading && <div className="text-sm text-base-content/60 p-2">加载中…</div>}
            {contactsError && <div className="alert alert-error text-sm py-2">{contactsError}</div>}
            <ul className="menu menu-vertical p-0 max-h-80 overflow-y-auto">
              {!contacts.length && !contactsLoading && (
                <li className="text-base-content/60 text-sm px-2">暂无联系人</li>
              )}
              {contacts.map((name) => (
                <li key={name}>
                  <button
                    type="button"
                    className={selectedContact === name ? 'active' : ''}
                    onClick={() => setSelectedContact(name)}
                  >
                    {typeof name === 'string' ? name : (name?.name ?? String(name))}
                  </button>
                </li>
              ))}
            </ul>
          </div>
        </div>
        <div className="card bg-base-100 border border-base-300 shadow-sm flex-1 flex flex-col min-w-0">
          <div className="card-body p-4 flex flex-col flex-1 min-h-0">
            {!selectedContact ? (
              <div className="flex-1 flex items-center justify-center text-base-content/60">
                请从左侧选择联系人打开聊天
              </div>
            ) : (
              <>
                <div className="font-medium text-base-content border-b border-base-300 pb-2 mb-2">
                  {selectedContact}
                </div>
                <div className="flex-1 overflow-y-auto mb-4 space-y-2 min-h-48">
                  {messagesLoading && <div className="text-sm text-base-content/60">加载消息中…</div>}
                  {messages.map((msg, i) => {
                    const content = msg.content ?? msg.text ?? ''
                    const isSelf = msg.isSelf ?? false
                    return (
                      <div
                        key={i}
                        className={`chat ${isSelf ? 'chat-end' : 'chat-start'}`}
                      >
                        <div className={`chat-bubble ${isSelf ? 'chat-bubble-primary' : ''}`}>
                          {content}
                        </div>
                      </div>
                    )
                  })}
                  <div ref={messagesEndRef} />
                </div>
                <div className="flex gap-2">
                  <input
                    type="text"
                    placeholder="输入消息…"
                    className="input input-bordered flex-1 input-sm"
                    value={sendText}
                    onChange={(e) => setSendText(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && handleSend()}
                  />
                  <button
                    type="button"
                    className="btn btn-primary btn-sm"
                    onClick={handleSend}
                    disabled={sending || !sendText.trim()}
                  >
                    {sending ? '发送中…' : '发送'}
                  </button>
                </div>
                {sendError && <p className="text-error text-sm mt-1">{sendError}</p>}
              </>
            )}
          </div>
        </div>
      </div>
    </section>
  )
}

function ScreenPanel() {
  const [devices, setDevices] = useState([])
  const [deviceId, setDeviceId] = useState('')
  const [streaming, setStreaming] = useState(false)
  const [status, setStatus] = useState('')
  const [imgError, setImgError] = useState('')
  const timerRef = useRef(null)
  const imgRef = useRef(null)

  useEffect(() => {
    getDevices()
      .then((res) => {
        const raw = res.data
        const list = Array.isArray(raw) ? raw : (raw && typeof raw === 'object' ? Object.values(raw) : [])
        setDevices(list)
        if (list.length && !deviceId) setDeviceId(list[0].id)
      })
      .catch(() => setDevices([]))
  }, [])

  useEffect(() => {
    if (!streaming || !deviceId) return
    setImgError('')
    const url = deviceScreenUrl(deviceId)
    function poll() {
      const u = url + Date.now()
      fetch(u)
        .then(async (r) => {
          if (!r.ok) {
            const text = await r.text()
            let msg = text
            try {
              const j = JSON.parse(text)
              if (j.detail) msg = typeof j.detail === 'string' ? j.detail : JSON.stringify(j.detail)
            } catch (_) {}
            throw new Error(msg || (r.status === 503 ? 'ADB 未配置或设备未连接' : r.statusText))
          }
          return r.blob()
        })
        .then((blob) => {
          if (imgRef.current) {
            const old = imgRef.current.src
            imgRef.current.src = URL.createObjectURL(blob)
            if (old && old.startsWith('blob:')) URL.revokeObjectURL(old)
          }
          setStatus('实时画面中…')
        })
        .catch((e) => {
          setImgError(e.message || '获取画面失败')
          setStatus('获取失败')
        })
    }
    poll()
    timerRef.current = setInterval(poll, 1200)
    return () => {
      if (timerRef.current) clearInterval(timerRef.current)
    }
  }, [streaming, deviceId])

  const toggle = () => {
    if (streaming) {
      setStreaming(false)
      setStatus('已停止')
      setImgError('')
    } else {
      if (!deviceId) {
        setStatus('请先选择设备')
        return
      }
      setStreaming(true)
    }
  }

  return (
    <section>
      <h2 className="text-xl font-semibold mb-4">设备实时画面</h2>
      <div className="card bg-base-100 border border-base-300 shadow-sm">
        <div className="card-body p-4">
          <p className="text-sm text-base-content/60 mb-3">
            未配置 ADB 时实时画面不可用。请在服务端 <code className="font-mono text-xs bg-base-300 px-1.5 py-0.5 rounded">config</code> 中配置 <code className="font-mono text-xs bg-base-300 px-1.5 py-0.5 rounded">ADB_PATH</code>，且设备通过 USB 连接本机。
          </p>
          <div className="flex flex-wrap items-center gap-3 mb-4">
            <label className="label-text">选择设备：</label>
            <select
              className="select select-bordered select-sm w-48"
              value={deviceId}
              onChange={(e) => setDeviceId(e.target.value)}
              disabled={streaming}
            >
              <option value="">请选择设备</option>
              {(Array.isArray(devices) ? devices : []).map((d) => (
                <option key={d.id} value={d.id}>{d.name || d.id}</option>
              ))}
            </select>
            <button type="button" className="btn btn-primary btn-sm" onClick={toggle}>
              {streaming ? '停止' : '开始'}
            </button>
            <span className="text-sm text-base-content/60">{status}</span>
          </div>
          <div className="relative bg-base-200 rounded-lg min-h-[400px] flex items-center justify-center overflow-hidden">
            <img
              ref={imgRef}
              alt="设备画面"
              className={`max-w-full max-h-[70vh] object-contain ${streaming && !imgError ? '' : 'hidden'}`}
            />
            {!streaming && (
              <div className="absolute text-base-content/60 text-sm">选择设备并点击「开始」查看实时画面</div>
            )}
            {imgError && (
              <div className="absolute text-error text-sm p-4 text-center">{imgError}</div>
            )}
          </div>
        </div>
      </div>
    </section>
  )
}

export default function App() {
  const [tab, setTab] = useState('devices')

  return (
    <div className="min-h-screen bg-base-200 flex">
      {/* 左侧菜单 */}
      <aside className="w-56 min-h-screen bg-base-100 border-r border-base-300 flex flex-col shrink-0">
        <div className="p-4 border-b border-base-300">
          <h1 className="font-bold text-lg text-base-content">Android RPA</h1>
          <p className="text-xs text-base-content/60 mt-0.5">设备 · 应用 · 实时画面</p>
        </div>
        <ul className="menu menu-vertical w-full p-2 flex-1">
          <MenuItem active={tab === 'devices'} label="设备管理" onClick={() => setTab('devices')} />
          <li className="menu-title pt-2 pb-0 text-base-content/60 text-xs">应用管理</li>
          <MenuItem active={tab === 'apps'} label="已注册应用" onClick={() => setTab('apps')} />
          <MenuItem active={tab === 'wechat'} label="微信" onClick={() => setTab('wechat')} />
          <MenuItem active={tab === 'wework'} label="企业微信" onClick={() => setTab('wework')} />
          <li className="menu-title pt-2 pb-0 text-base-content/60 text-xs mt-2">设备</li>
          <MenuItem active={tab === 'screen'} label="实时画面" onClick={() => setTab('screen')} />
        </ul>
      </aside>

      {/* 主内容区 */}
      <main className="flex-1 overflow-auto p-6">
        {tab === 'devices' && <DevicesPanel />}
        {tab === 'apps' && <AppsPanel />}
        {tab === 'wechat' && <ImAppPanel prefix="wechat" label="微信" />}
        {tab === 'wework' && <ImAppPanel prefix="wework" label="企业微信" />}
        {tab === 'screen' && <ScreenPanel />}
      </main>
    </div>
  )
}
