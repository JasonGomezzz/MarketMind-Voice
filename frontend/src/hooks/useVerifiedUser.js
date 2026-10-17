import { createContext, useContext } from 'react'

/**
 * Usuario confirmado por el servidor (GET /api/auth/me/) al entrar al panel.
 * Lo provee PrivateRoute; RoleRoute y los enrutadores por rol lo leen de aquí
 * en vez de confiar en lo que haya quedado guardado en el navegador.
 */
export const VerifiedUserContext = createContext(null)

export const ROLES = ['superadmin', 'marketero', 'cliente']

export function useVerifiedUser() {
  return useContext(VerifiedUserContext)
}
