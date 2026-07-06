import { clsx } from 'clsx'
import { twMerge } from 'tailwind-merge'

/**
 * Combina clases de Tailwind resolviendo conflictos (patrón shadcn/ui).
 * @param {...any} inputs - listas de clases condicionales
 * @returns {string} cadena de clases fusionada
 */
export function cn(...inputs) {
  return twMerge(clsx(inputs))
}
