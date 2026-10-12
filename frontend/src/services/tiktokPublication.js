import { getApprovedPublicationCopy } from './campaignPublication.js'

export function shouldPollTikTok(status) {
  return ['sending', 'processing', 'inbox', 'uncertain'].includes(status)
}

export function canSendTikTok(campaign, accountId, state) {
  const copy = getApprovedPublicationCopy(campaign, 'tiktok')
  return !!(copy?.trim() && copy.length <= 4000 && campaign.imagen_b64 && accountId
    && (campaign.plataformas?.length ? campaign.plataformas : [campaign.plataforma]).includes('tiktok')
    && state.outcome?.status === 'not_sent' && state.outcome.media_ready && state.configured
    && !state.loading && !state.busy && !state.checking && !state.error)
}
