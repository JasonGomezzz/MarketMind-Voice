import userApi from './userApi'

/**
 * Servicios de campañas para el rol CLIENTE (Spring Boot :8080).
 * El cliente solo LEE y cambia el estado (aprobar/rechazar) — nunca crea.
 *
 * La API de Spring envuelve las respuestas en {success, message, data}.
 * Aquí devolvemos ya el `data` desempaquetado para que los componentes
 * trabajen con los datos directamente.
 */

/**
 * Feed de campañas pendientes de revisión (paginado DRF-like de Spring).
 * @param {object} [params] - { page, size } opcionales.
 * @returns {Promise<{content: object[], totalElements: number}>}
 */
export async function getPendingCampaigns(params = {}) {
  const { data } = await userApi.get('/api/v1/campaigns/pending', { params })
  // Spring devuelve Page<...> dentro de data: { content, totalElements, ... }
  return data.data
}

export async function getMyCampaigns(params = {}) {
  const { data } = await userApi.get('/api/v1/campaigns/mine', { params })
  return data.data
}

/**
 * Conteos de campañas por estado para las stat cards del dashboard cliente.
 * @returns {Promise<{pendientes: number, aprobadas: number, rechazadas: number}>}
 */
export async function getCampaignSummary() {
  const { data } = await userApi.get('/api/v1/campaigns/summary')
  return data.data
}

/**
 * Detalle de una campaña por id.
 * @param {number|string} id
 * @returns {Promise<object>} campaña
 */
export async function getCampaignById(id) {
  const { data } = await userApi.get(`/api/v1/campaigns/${id}`)
  return data.data
}

/**
 * Aprobar una campaña (pendiente_aprobacion → aprobado).
 * @param {number|string} id
 * @param {number} version - versión actual de la campaña (optimistic locking @Version
 *   de JPA; Spring la exige @NotNull para prevenir conflictos concurrentes)
 * @returns {Promise<object>} campaña actualizada
 */
export async function approveCampaign(id, version, valoracion) {
  const { data } = await userApi.patch(`/api/v1/campaigns/${id}/status`, {
    estado: 'aprobado',
    version,
    valoracion,
  })
  return data.data
}

/**
 * Rechazar una campaña con feedback OBLIGATORIO (HU15).
 * pendiente_aprobacion → rechazado. El feedback dispara email al marketero (n8n).
 * Spring valida feedback de 10 a 500 caracteres.
 * @param {number|string} id
 * @param {string} feedback - motivo del rechazo (requerido, 10-500 chars)
 * @param {number} version - versión actual de la campaña (optimistic locking)
 * @returns {Promise<object>} campaña actualizada
 */
export async function rejectCampaign(id, feedback, version, valoracion) {
  const { data } = await userApi.patch(`/api/v1/campaigns/${id}/status`, {
    estado: 'rechazado',
    feedback,
    version,
    valoracion,
  })
  return data.data
}
