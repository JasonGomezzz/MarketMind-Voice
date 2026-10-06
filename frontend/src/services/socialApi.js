/** Llamadas a /api/social/ de Django. */
import api from './api'

export const socialApi = {
  conexiones: () => api.get('/api/social/connections/').then((r) => r.data.data.conexiones),
  destinos: (clienteEmail) =>
    api
      .get('/api/social/connections/destinos/', { params: { cliente_email: clienteEmail } })
      .then((r) => r.data.data.conexiones),
  urlConexion: () => api.get('/api/social/meta/connect/').then((r) => r.data.data.url),
  desconectar: (id) => api.delete(`/api/social/connections/${id}/`),
  publicaciones: (campaignId) =>
    api
      .get('/api/social/publications/', { params: { campaign: campaignId } })
      .then((r) => r.data.data.publicaciones),
  publicar: (id) => api.post(`/api/social/publications/${id}/publish/`),
}
