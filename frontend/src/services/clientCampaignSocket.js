// First-frame authentication keeps tokens out of URLs and access logs.
export function createClientCampaignSocket({ url, ensureSession, getToken, onEvent, WebSocketImpl = WebSocket, setTimer = setTimeout, clearTimer = clearTimeout }) {
  let socket
  let timer
  let stopped = false
  let attempts = 0

  function retry() {
    if (stopped || attempts >= 5) return
    timer = setTimer(connect, Math.min(30000, 1000 * 2 ** attempts++))
  }

  async function connect() {
    if (stopped) return
    try {
      // The Django HTTP client refreshes expired access tokens before connecting.
      await ensureSession()
      if (stopped) return
      const token = getToken()
      if (!token) return
      const current = new WebSocketImpl(url)
      socket = current
      let authenticated = false
      current.onopen = () => {
        if (!stopped) current.send(JSON.stringify({ type: 'authenticate', token }))
      }
      current.onmessage = event => {
        if (stopped || current !== socket) return
        try {
          const payload = JSON.parse(event.data)
          if (payload.type === 'authenticated') {
            authenticated = true
            attempts = 0
          } else if (authenticated && payload.campaign && ['campaign_submitted', 'campaign_status_changed'].includes(payload.type)) {
            onEvent(payload)
          }
        } catch { /* Malformed messages must not update the dashboard. */ }
      }
      current.onclose = event => {
        if (stopped || current !== socket) return
        // Do not repeatedly submit a token rejected during authentication.
        if (event.code === 1008 && !authenticated) return
        retry()
      }
    } catch { retry() }
  }

  void connect()
  return () => {
    stopped = true
    clearTimer(timer)
    if (socket && socket.readyState <= 1) socket.close()
  }
}
