import { useEffect, useState } from 'react'
import api from '../services/api'

const FALLBACKS = {
  login: {
    quote: 'Revisamos propuestas con contexto, dejamos feedback claro y el equipo creativo avanza sin perseguir aprobaciones por correo.',
    person_name: 'Elena Rodríguez',
    person_role: 'Directora de Marketing, Global Creative Co.',
    person_image: '/src/assets/landing/testimonial.png',
  },
  register: {
    quote: 'Pasamos del brief a una campaña lista para revisar en minutos. La IA nos da velocidad sin perder control creativo.',
    person_name: 'Camila Torres',
    person_role: 'Creative Lead, Prisma Studio',
    person_image: '/src/assets/landing/testimonial.png',
  },
}

export function useAuthBrandContent(screen) {
  const [content, setContent] = useState(FALLBACKS[screen] ?? FALLBACKS.login)

  useEffect(() => {
    let cancelled = false
    api
      .get('/api/auth/brand-content/', { params: { screen } })
      .then(({ data }) => {
        const next = data?.data?.content
        if (!cancelled && next) setContent(next)
      })
      .catch(() => {
        if (!cancelled) setContent(FALLBACKS[screen] ?? FALLBACKS.login)
      })
    return () => {
      cancelled = true
    }
  }, [screen])

  return content
}
