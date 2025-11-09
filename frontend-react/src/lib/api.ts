import axios, { AxiosInstance, AxiosResponse } from 'axios'
import type {
  LoginRequest,
  LoginResponse,
  BankerLoginRequest,
  BankerLoginResponse,
  Account,
  Transaction,
  Consent,
  PaymentRequest,
  PaymentResponse,
  Client,
  Product,
  BankStats,
  APILog
} from '@/types/api'

// Create axios instance with default config
const createApiInstance = (): AxiosInstance => {
  // Use relative URL in development to leverage Vite proxy, absolute URL in production
  const isDev = import.meta.env.DEV
  const instance = axios.create({
    baseURL: isDev ? '' : (import.meta.env.VITE_API_URL || 'http://localhost:54080'),
    timeout: 10000,
    headers: {
      'Content-Type': 'application/json',
    },
  })

  // Add request interceptor to include auth token
  instance.interceptors.request.use(
    (config) => {
      const token = localStorage.getItem('token')
      if (token) {
        config.headers.Authorization = `Bearer ${token}`
      }
      return config
    },
    (error) => Promise.reject(error)
  )

  // Add response interceptor to handle errors
  instance.interceptors.response.use(
    (response: AxiosResponse) => response,
    (error) => {
      if (error.response?.status === 401) {
        // Clear auth and redirect to login
        localStorage.removeItem('token')
        localStorage.removeItem('client_id')
        window.location.href = '/app/client/login'
      }
      return Promise.reject(error)
    }
  )

  return instance
}

const api = createApiInstance()

// Authentication API
export const authAPI = {
  login: async (data: LoginRequest): Promise<LoginResponse> => {
    const response = await api.post('/auth/login', data)
    return response.data
  },

  bankerLogin: async (data: BankerLoginRequest): Promise<BankerLoginResponse> => {
    const response = await api.post('/auth/banker/token', data)
    return response.data
  },

  logout: async (): Promise<void> => {
    await api.post('/auth/logout')
  },

  registerTeam: async (data: any): Promise<any> => {
    const response = await api.post('/developer/register', data)
    return response.data
  },
}

// Bank API
export const bankAPI = {
  getBankInfo: async (): Promise<{ bank: string; description: string }> => {
    const response = await api.get('/')
    return response.data
  },
}

// Banker API (for banker-specific operations)
export const bankerAPI = {
  getClients: async (): Promise<Client[]> => {
    const response = await api.get('/admin/clients')
    return response.data
  },

  getClient: async (clientId: string): Promise<Client> => {
    const response = await api.get(`/admin/clients/${clientId}`)
    return response.data
  },

  getProducts: async (): Promise<Product[]> => {
    const response = await api.get('/admin/products')
    return response.data
  },

  getStats: async (): Promise<BankStats> => {
    const response = await api.get('/admin/stats')
    return response.data
  },

  getLogs: async (): Promise<APILog[]> => {
    const response = await api.get('/admin/logs')
    return response.data
  },

  getAllConsents: async (): Promise<any[]> => {
    const response = await api.get('/admin/consents')
    return response.data
  },

  approveConsent: async (requestId: string): Promise<void> => {
    await api.post(`/admin/consents/${requestId}/approve`)
  },

  rejectConsent: async (requestId: string): Promise<void> => {
    await api.post(`/admin/consents/${requestId}/reject`)
  },

  getAPILogs: async (): Promise<APILog[]> => {
    const response = await api.get('/admin/logs')
    return response.data
  },

  getTransactions: async (): Promise<Transaction[]> => {
    const response = await api.get('/admin/transactions')
    return response.data
  },
}

// Admin API (for team management)
export const adminAPI = {
  getTeams: async (): Promise<any[]> => {
    const response = await api.get('/admin/teams')
    return response.data
  },

  suspendTeam: async (clientId: string): Promise<void> => {
    await api.post(`/admin/teams/${clientId}/suspend`)
  },

  activateTeam: async (clientId: string): Promise<void> => {
    await api.post(`/admin/teams/${clientId}/activate`)
  },
}

// Accounts API
export const accountsAPI = {
  getAccounts: async (): Promise<Account[]> => {
    const response = await api.get('/accounts')
    return response.data
  },

  getAccount: async (accountId: string): Promise<Account> => {
    const response = await api.get(`/accounts/${accountId}`)
    return response.data
  },

  getAccountTransactions: async (accountId: string): Promise<Transaction[]> => {
    const response = await api.get(`/accounts/${accountId}/transactions`)
    return response.data
  },

  getTransactions: async (accountId: string): Promise<Transaction[]> => {
    const response = await api.get(`/accounts/${accountId}/transactions`)
    return response.data
  },

  getExternalAccounts: async (): Promise<any[]> => {
    const response = await api.get('/accounts/external')
    return response.data
  },
}

// Consents API
export const consentsAPI = {
  getConsents: async (): Promise<Consent[]> => {
    const response = await api.get('/consents')
    return response.data
  },

  createConsent: async (data: any): Promise<Consent> => {
    const response = await api.post('/consents', data)
    return response.data
  },

  revokeConsent: async (consentId: string): Promise<void> => {
    await api.delete(`/consents/${consentId}`)
  },

  deleteConsent: async (consentId: string): Promise<void> => {
    await api.delete(`/consents/${consentId}`)
  },
}

// Payments API
export const paymentsAPI = {
  createPayment: async (data: PaymentRequest): Promise<PaymentResponse> => {
    const response = await api.post('/payments', data)
    return response.data
  },

  getPayments: async (): Promise<PaymentResponse[]> => {
    const response = await api.get('/payments')
    return response.data
  },

  getPayment: async (paymentId: string): Promise<PaymentResponse> => {
    const response = await api.get(`/payments/${paymentId}`)
    return response.data
  },
}

// Products API
export const productsAPI = {
  getProducts: async (): Promise<Product[]> => {
    const response = await api.get('/products')
    return response.data
  },

  getProduct: async (productId: string): Promise<Product> => {
    const response = await api.get(`/products/${productId}`)
    return response.data
  },

  createProduct: async (data: any): Promise<Product> => {
    const response = await api.post('/admin/products', data)
    return response.data
  },
}

// Teams API
export const teamsAPI = {
  getTeams: async (): Promise<any[]> => {
    const response = await api.get('/admin/teams')
    return response.data
  },

  createTeam: async (data: any): Promise<any> => {
    const response = await api.post('/admin/teams', data)
    return response.data
  },
}

// Developer API
export const developerAPI = {
  registerBank: async (data: any): Promise<any> => {
    const response = await api.post('/developer/register', data)
    return response.data
  },
}