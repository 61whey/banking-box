import { create } from 'zustand'

interface AppState {
  theme: 'light' | 'dark'
  bankName: string
  toggleTheme: () => void
  setTheme: (theme: 'light' | 'dark') => void
  setBankName: (name: string) => void
}

export const useAppStore = create<AppState>()((set) => ({
  theme: 'light',
  bankName: 'Banking Box',
  toggleTheme: () =>
    set((state) => {
      const newTheme = state.theme === 'light' ? 'dark' : 'light'
      document.documentElement.classList.toggle('dark', newTheme === 'dark')
      return { theme: newTheme }
    }),
  setTheme: (theme) => {
    document.documentElement.classList.toggle('dark', theme === 'dark')
    set({ theme })
  },
  setBankName: (name: string) => {
    set({ bankName: name })
    // Обновляем title страницы
    document.title = name
  },
}))

