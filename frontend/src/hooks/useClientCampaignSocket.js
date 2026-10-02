import { useEffect } from 'react'
import { getCampaignById } from '../services/clientCampaigns'
import { connectClientCampaignSocket } from '../services/clientCampaignSocket'
import { clearSession, refreshAccessToken, SESSION_CHANGED } from '../services/session'

function getWsUrl() {
  const url = new URL(import.meta.env.VITE_USER_API_URL || 'http://localhost:8080', window.location.origin)
  url.protocol = url.protocol === 'https:' ? 'wss:' : 'ws:'
  url.pathname = '/ws/client-campaigns'
  url.search = ''
  url.hash = ''
  return url.toString()
}

/** Notifications contain IDs only. Campaign contents always come from the authorized API. */
export function useClientCampaignSocket({ onCampaignSubmitted, onCampaignStatusChanged, onConnected } = {}) {
  useEffect(() => {
    if (typeof WebSocket === 'undefined') return undefined
    let cancelled = false
    let generation = 0
    let accessToken = localStorage.getItem('access_token')
    let disconnect = () => {}

    function connect() {
      const currentGeneration = ++generation
      return connectClientCampaignSocket({
        url: getWsUrl(),
        getToken: () => localStorage.getItem('access_token'),
        refreshToken: refreshAccessToken,
        endSession: clearSession,
        onConnected,
        onNotification: async ({ type, campaignId }) => {
          try {
            const campaign = await getCampaignById(campaignId)
            if (cancelled || currentGeneration !== generation || !localStorage.getItem('access_token')) return
            if (type === 'campaign_submitted') onCampaignSubmitted?.(campaign)
            else onCampaignStatusChanged?.(campaign)
          } catch {
            // Deleted/reassigned campaign or failed connection: keep the REST retry controls.
          }
        },
      })
    }

    const sessionChanged = () => {
      const current = localStorage.getItem('access_token')
      if (accessToken === current) return
      accessToken = current
      generation++
      disconnect()
      if (current) disconnect = connect()
    }
    disconnect = connect()
    window.addEventListener(SESSION_CHANGED, sessionChanged)
    window.addEventListener('storage', sessionChanged)
    return () => {
      cancelled = true
      generation++
      window.removeEventListener(SESSION_CHANGED, sessionChanged)
      window.removeEventListener('storage', sessionChanged)
      disconnect()
    }
  }, [onCampaignSubmitted, onCampaignStatusChanged, onConnected])
}
