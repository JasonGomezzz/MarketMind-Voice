// Use the saved, approved copy, never an unsaved local draft.
export function getApprovedPublicationCopy(campaign) {
  if (campaign?.estado !== 'aprobado') return null
  const copy = campaign.texto_generado
  return typeof copy === 'string' && copy.trim() ? copy : null
}
