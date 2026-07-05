/**
 * Modelo de créditos/planes — fuente única para CreditsExhausted y PlanesModal.
 * Sin pasarela de pago en esta versión: los planes son la vista del modelo de
 * negocio y la recarga real la hace el SuperAdmin (HU24, reset-quota).
 */
export const MSG_RESET =
  'Avísale a tu SuperAdmin: él restablece tu cuota a 100 desde el panel Usuarios.'

export const PLANS = [
  { nombre: 'Básico', precio: 49, creditos: '500', popular: false },
  { nombre: 'Pro', precio: 129, creditos: '1,500', popular: true },
  { nombre: 'Elite', precio: 299, creditos: '5,000', popular: false },
]
