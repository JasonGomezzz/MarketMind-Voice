import { getApprovedPublicationCopy } from './campaignPublication.js'

export function canConfirmFacebookPublication(campaign, pageId, state = {}) {
  const copy = getApprovedPublicationCopy(campaign, 'facebook')
  return copy !== null && copy.length <= 60000 && !!campaign.imagen_b64 && !!pageId
    && (campaign.plataformas?.length ? campaign.plataformas : [campaign.plataforma]).includes('facebook')
    && !state.loading && !state.checking && !state.busy && !state.error
    && (!state.outcome || state.outcome.status === 'not_published')
}
