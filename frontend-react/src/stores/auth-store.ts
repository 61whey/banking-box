import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface AuthState {
  token: string | null
  clientId: string | null
  isAuthenticated: boolean
  setAuth: (token: string, clientId: string) => void
  clearAuth: () => void
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      token: null,
      clientId: null,
      isAuthenticated: false,
      setAuth: (token: string, clientId: string) => {
        localStorage.setItem('token', token)
        localStorage.setItem('client_id', clientId)
        set({ token, clientId, isAuthenticated: true })
      },
      clearAuth: () => {
        localStorage.removeItem('token')
        localStorage.removeItem('client_id')
        set({ token: null, clientId: null, isAuthenticated: false })
      },
    }),
    {
      name: 'auth-storage',
    }
  )
)

