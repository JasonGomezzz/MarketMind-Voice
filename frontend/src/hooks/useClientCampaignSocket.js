import { useEffect } from 'react'
import api from '@/services/api'
import { getAuthItem } from '@/lib/authStorage'
import { createClientCampaignSocket } from '@/services/clientCampaignSocket'

function getWsUrl() {
  const apiUrl = import.meta.env.VITE_USER_API_URL || 'http://localhost:8081'
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

    return createClientCampaignSocket({
      url: getWsUrl(),
      ensureSession: () => api.get('/api/auth/me/'),
      getToken: () => getAuthItem('access_token'),
      onEvent: payload => {
        if (payload.type === 'campaign_submitted') onCampaignSubmitted?.(payload.campaign)
        else if (payload.type === 'campaign_status_changed') onCampaignStatusChanged?.(payload.campaign)
      },
    })
  }, [onCampaignSubmitted, onCampaignStatusChanged])
}
