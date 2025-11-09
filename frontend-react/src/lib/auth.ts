export const setToken = (token: string): void => {
  localStorage.setItem('token', token)
}

export const getToken = (): string | null => {
  return localStorage.getItem('token')
}

export const removeToken = (): void => {
  localStorage.removeItem('token')
  localStorage.removeItem('client_id')
}

export const setClientId = (clientId: string): void => {
  localStorage.setItem('client_id', clientId)
}

export const getClientId = (): string | null => {
  return localStorage.getItem('client_id')
}

export const isAuthenticated = (): boolean => {
  return !!getToken()
}

