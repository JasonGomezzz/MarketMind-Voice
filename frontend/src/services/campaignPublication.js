// Use the saved, approved copy, never an unsaved local draft.
export function getPlatformCopy(campaign, platform) {
  return campaign?.textos_por_plataforma?.[platform] ?? campaign?.texto_generado ?? ''
}

export function getApprovedPublicationCopy(campaign, platform) {
  if (campaign?.estado !== 'aprobado') return null
  const copy = platform ? getPlatformCopy(campaign, platform) : campaign.texto_generado
  return typeof copy === 'string' && copy.trim() ? copy : null
}
