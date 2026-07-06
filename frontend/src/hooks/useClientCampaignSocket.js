import { useEffect } from 'react'

function getWsUrl() {
  const apiUrl = import.meta.env.VITE_USER_API_URL || 'http://localhost:8080'
  const url = new URL(apiUrl)
  url.protocol = url.protocol === 'https:' ? 'wss:' : 'ws:'
  url.pathname = '/ws/client-campaigns'
  url.search = ''
  return url.toString()
}

/**
 * @param {{ onCampaignSubmitted?: (campaign: object) => void, onCampaignStatusChanged?: (campaign: object) => void }} handlers
 */
export function useClientCampaignSocket({ onCampaignSubmitted, onCampaignStatusChanged } = {}) {
  useEffect(() => {
    if (typeof WebSocket === 'undefined') return undefined

    let socket
    let reconnectTimer
    let closedByEffect = false

    function connect() {
      socket = new WebSocket(getWsUrl())

      socket.onmessage = (event) => {
        try {
          const payload = JSON.parse(event.data)
          if (!payload.campaign) return
          if (payload.type === 'campaign_submitted') {
            onCampaignSubmitted?.(payload.campaign)
          } else if (payload.type === 'campaign_status_changed') {
            onCampaignStatusChanged?.(payload.campaign)
          }
        } catch {
          // Evento inválido: se ignora sin romper el dashboard.
        }
      }

      socket.onclose = () => {
        if (!closedByEffect) {
          reconnectTimer = window.setTimeout(connect, 3000)
        }
      }
    }

    connect()

    return () => {
      closedByEffect = true
      window.clearTimeout(reconnectTimer)
      if (socket && socket.readyState <= WebSocket.OPEN) socket.close()
    }
  }, [onCampaignSubmitted, onCampaignStatusChanged])
}
