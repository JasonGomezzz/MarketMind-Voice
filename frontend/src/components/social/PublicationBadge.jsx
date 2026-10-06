import { estadoPublicacion } from '../../services/social'

const TONOS = {
  ok: 'bg-success-container text-success',
  error: 'bg-error-container text-error',
  neutral: 'bg-surface-container-high text-on-surface-variant',
}

/** Pill del estado de una publicación (esperando aprobación, publicado, fallido…). */
export default function PublicationBadge({ estado }) {
  const { texto, tono } = estadoPublicacion(estado)
  return (
    <span
      className={`inline-flex items-center whitespace-nowrap rounded-full px-3 py-1 text-xs font-semibold ${TONOS[tono]}`}
    >
      {texto}
    </span>
  )
}
