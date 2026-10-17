/**
 * Modelo de créditos/planes — fuente única para CreditsExhausted y PlanesModal.
 * Pasarela de pago simulada: PlanesModal compra créditos vía
 * POST /api/campaigns/credits/purchase/ (siempre aprueba, sin procesador
 * real). `key` debe coincidir con CREDIT_PLAN_MAP en
 * backend/apps/campaigns/views.py — mantener ambos en sincronía manual.
 * Vías alternativas: solicitud de créditos que aprueba el SuperAdmin
 * (CreditRequestButton) y la recarga manual reset-quota (HU24).
 */

export const PLANS = [
  { key: 'basico', nombre: 'Básico', precio: 49, creditos: '500', popular: false },
  { key: 'pro', nombre: 'Pro', precio: 129, creditos: '1,500', popular: true },
  { key: 'elite', nombre: 'Elite', precio: 299, creditos: '5,000', popular: false },
]
