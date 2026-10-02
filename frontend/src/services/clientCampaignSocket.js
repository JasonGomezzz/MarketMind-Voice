/** Browser-compatible authentication: only the first frame contains an access JWT.
 * No credential is included in URLs/subprotocols or persisted in server logs.
 */
export function connectClientCampaignSocket({
  url, getToken, refreshToken, endSession, onConnected, onNotification,
  createSocket = (address) => new WebSocket(address),
  schedule = (callback, delay) => window.setTimeout(callback, delay),
  cancel = (timer) => window.clearTimeout(timer),
}) {
  let socket
  let timer
  let stopped = false
  let attempts = 0
  let lastRefreshedToken = null
  let generation = 0

  function retry() {
    if (stopped || !getToken()) return
    cancel(timer)
    const delay = Math.min(30000, 1000 * 2 ** Math.min(attempts++, 5))
    timer = schedule(connect, delay + Math.random() * 300)
  }

  async function connect() {
    const accessToken = getToken()
    if (stopped || !accessToken) return
    const currentGeneration = ++generation
    try {
      socket = createSocket(url)
    } catch {
      retry()
      return
    }
    const currentSocket = socket
    const isCurrent = () => !stopped && currentGeneration === generation
    currentSocket.onopen = () => {
      if (isCurrent()) currentSocket.send(JSON.stringify({ type: 'authenticate', accessToken }))
    }
    currentSocket.onmessage = (event) => {
      if (!isCurrent()) return
      try {
        const message = JSON.parse(event.data)
        if (message.type === 'authenticated') {
          attempts = 0
          lastRefreshedToken = null
          onConnected?.()
        } else if (['campaign_submitted', 'campaign_status_changed'].includes(message.type)
                   && Number.isSafeInteger(message.campaignId) && message.campaignId > 0) {
          onNotification?.(message)
        }
      } catch {
        // Malformed notification does not affect the authenticated API fallback.
      }
    }
    currentSocket.onclose = async ({ code }) => {
      if (!isCurrent()) return
      // A late close from a replaced session must never clear the new account.
      if (getToken() !== accessToken) {
        retry()
        return
      }
      if (code === 4403 || (code === 4401 && accessToken === lastRefreshedToken)) {
        stopped = true
        endSession()
        return
      }
      if (code === 4401 || code === 4408) {
        try {
          lastRefreshedToken = await refreshToken(accessToken)
        } catch {
          // Terminal refresh failures clear the session; transient ones back off.
        }
      }
      if (isCurrent()) retry()
    }
  }

  connect()
  return () => {
    stopped = true
    generation++
    cancel(timer)
    if (socket && socket.readyState <= 1) socket.close()
  }
}
