import { getApprovedPublicationCopy } from './campaignPublication.js'

export function canConfirmXPublication(campaign, accountId, state = {}) {
  return getApprovedPublicationCopy(campaign) !== null && !!campaign.imagen_b64 && !!accountId
    && (campaign.plataformas?.length ? campaign.plataformas : [campaign.plataforma]).includes('twitter')
    && !state.loading && !state.checking && !state.busy && !state.error
    && !!state.outcome?.text_validation?.valid
    && state.outcome.accountId === String(accountId)
    && ['not_published', 'failed'].includes(state.outcome.status)
}
