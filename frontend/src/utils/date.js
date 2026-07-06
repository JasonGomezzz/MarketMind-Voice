export function relativeTimeFrom(value) {
  if (!value) return 'sin fecha'

  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return 'sin fecha'

  const diffMs = Date.now() - date.getTime()
  if (diffMs < 0) return 'recién enviada'

  const minutes = Math.floor(diffMs / 60000)
  if (minutes < 1) return 'recién enviada'
  if (minutes < 60) return `hace ${minutes} min`

  const hours = Math.floor(minutes / 60)
  if (hours < 24) return `hace ${hours} h`

  const days = Math.floor(hours / 24)
  if (days < 30) return `hace ${days} ${days === 1 ? 'día' : 'días'}`

  return date.toLocaleDateString('es-PE', {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
  })
}

export function campaignSentAt(campaign) {
  return campaign?.enviadoClienteAt || campaign?.fechaActualizacion || campaign?.fechaCreacion
}
