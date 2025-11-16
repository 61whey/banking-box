import axios, { AxiosError } from 'axios'
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
  APILog,
  VirtualAccount,
  VirtualAccountCreate,
  VirtualAccountUpdate,
  VirtualAccountListResponse,
  BalanceAllocation,
  BalanceAllocationCreate,
  BalanceAllocationUpdate,
  BalanceAllocationListResponse,
} from '@/types/api'

// Используем VITE_API_URL из переменных окружения (устанавливается во время сборки)
// Если не установлен, используем localhost:8000 для локальной разработки (python run.py)
// Для Docker используется localhost:54080 (настраивается через VITE_API_URL)
const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const api = axios.create({
  baseURL: BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

export interface BankInfo {
  bank: string
  bank_code: string
  api_version: string
  status: string
}

export const bankAPI = {
  getBankInfo: async (): Promise<BankInfo> => {
    const response = await api.get<BankInfo>('/')
    return response.data
  },
}

api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

api.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token')
      localStorage.removeItem('client_id')
      window.location.href = '/app/client/login'
    }
    return Promise.reject(error)
  }
)

export interface RegisterTeamRequest {
  team_name: string
  client_id: string
  email?: string
  telegram?: string
  contact_person?: string
}

export interface RegisterTeamResponse {
  success: boolean
  message: string
  credentials: {
    client_id: string
    client_secret: string
    team_name?: string
  }
  test_clients: string[]
  test_password?: string
  next_steps?: string
  links?: {
    ui: string
    api_docs: string
  }
}

export const authAPI = {
  login: async (data: LoginRequest): Promise<LoginResponse> => {
    const response = await api.post<LoginResponse>('/auth/login', data)
    return response.data
  },

  bankerLogin: async (data: BankerLoginRequest): Promise<BankerLoginResponse> => {
    const response = await api.post<BankerLoginResponse>('/auth/banker-login', data)
    return response.data
  },

  registerTeam: async (data: RegisterTeamRequest): Promise<RegisterTeamResponse> => {
    const response = await api.post<RegisterTeamResponse>('/auth/register-team', data)
    return response.data
  },
}

export const accountsAPI = {
  getAccounts: async (): Promise<Account[]> => {
    const response = await api.get<any>('/accounts')
    // API возвращает данные в формате OpenBanking Russia v2.1
    const accounts = response.data?.data?.account || []
    
    // Преобразуем формат OpenBanking в наш формат и получаем балансы
    const accountsWithBalances = await Promise.all(
      accounts.map(async (acc: any) => {
        const accountId = acc.accountId || acc.account_id
        let balance = 0
        
        // Получаем баланс отдельно
        try {
          const balanceResponse = await api.get<any>(`/accounts/${accountId}/balances`)
          const balances = balanceResponse.data?.data?.balance || []
          const availableBalance = balances.find((b: any) => b.type === 'InterimAvailable')
          if (availableBalance?.amount?.amount) {
            balance = parseFloat(availableBalance.amount.amount)
          }
        } catch (error) {
          console.warn(`Failed to fetch balance for account ${accountId}:`, error)
        }
        
        return {
          account_id: accountId || String(Math.random()),
          account_number: acc.account?.[0]?.identification || acc.account_number || '',
          account_type: acc.accountType || acc.account_type || acc.accountSubType || '',
          balance: balance,
          currency: acc.currency || 'RUB',
          status: acc.status === 'Enabled' ? 'active' : 'inactive',
          bank_code: acc.bank_code || 'VBANK',
          client_person_id: acc.client_person_id,
        }
      })
    )
    
    return accountsWithBalances
  },

  getAccount: async (accountId: string): Promise<Account> => {
    const response = await api.get<Account>(`/accounts/${accountId}`)
    return response.data
  },

  getTransactions: async (accountId: string): Promise<Transaction[]> => {
    const response = await api.get<any>(`/accounts/${accountId}/transactions`)
    // API возвращает данные в формате OpenBanking Russia v2.1
    const transactions = response.data?.data?.transaction || []
    // Преобразуем формат OpenBanking в наш формат
    return transactions.map((tx: any) => ({
      transaction_id: tx.transactionId || tx.transaction_id || String(Math.random()),
      account_id: tx.accountId || accountId,
      amount: parseFloat(tx.amount?.amount || '0') || 0,
      currency: tx.amount?.currency || tx.currency || 'RUB',
      transaction_type: tx.creditDebitIndicator === 'Credit' ? 'credit' : 'debit',
      description: tx.transactionInformation || tx.description || '',
      created_at: tx.bookingDateTime || tx.valueDateTime || tx.created_at || new Date().toISOString(),
      status: tx.status || 'completed',
      counterparty_name: tx.counterparty_name,
      counterparty_account: tx.counterparty_account,
    }))
  },

  getExternalAccounts: async (): Promise<any[]> => {
    const response = await api.get<any>('/accounts/external')
    // API возвращает данные в формате { data: { accounts: [...] } }
    const accounts = response.data?.data?.accounts || []
    // Фильтруем только успешные ответы
    return accounts.filter((acc: any) => acc.account !== null && acc.error === null)
  },

  refreshExternalAccounts: async (): Promise<void> => {
    // Invalidate cache first
    await api.post('/accounts/external/refresh', {}, {
      headers: {
        'Cache-Control': 'no-cache'
      }
    })
  },

  getExternalAccountsWithRefresh: async (): Promise<any[]> => {
    // First invalidate cache
    await api.post('/accounts/external/refresh', {}, {
      headers: {
        'Cache-Control': 'no-cache'
      }
    })
    
    // Then fetch fresh data with cache-busting parameters
    const timestamp = Date.now()
    const response = await api.get<any>(`/accounts/external?force_refresh=true&_t=${timestamp}`, {
      headers: {
        'Cache-Control': 'no-cache, no-store, must-revalidate',
        'Pragma': 'no-cache'
      }
    })
    
    const accounts = response.data?.data?.accounts || []
    return accounts.filter((acc: any) => acc.account !== null && acc.error === null)
  },
}

export const consentsAPI = {
  getConsents: async (): Promise<Consent[]> => {
    const response = await api.get<any>('/account-consents/my-consents')
    // API возвращает данные в формате { "consents": [...] }
    const consents = response.data?.consents || (Array.isArray(response.data) ? response.data : [])
    // Преобразуем формат если нужно
    return consents.map((c: any) => ({
      consent_id: c.consent_id || String(c.id || Math.random()),
      status: c.status || 'pending',
      permissions: Array.isArray(c.permissions) ? c.permissions : [],
      expiration_date: c.expires_at || c.expiration_date_time || c.expirationDateTime || new Date(Date.now() + 90 * 24 * 60 * 60 * 1000).toISOString(),
      created_at: c.signed_at || c.created_at || c.creationDateTime || new Date().toISOString(),
      team_name: c.team_name || c.bank_name || c.granted_to,
      team_client_id: c.team_client_id || c.bank_code || c.granted_to,
    }))
  },

  deleteConsent: async (consentId: string): Promise<void> => {
    await api.delete(`/account-consents/my-consents/${consentId}`)
  },
}

export interface ExternalPaymentRequest {
  from_account: string  // Format: "bank_code:account_number"
  to_account: string    // Format: "bank_code:account_number"
  amount: number
  description: string
}

export interface ExternalPaymentResponse {
  payment_id: string
  status: string
  message?: string
  error?: string
}

export interface ExternalPaymentHistoryItem {
  payment_id: string
  amount: number
  currency: string
  source_bank: string
  source_account: string
  destination_bank: string
  destination_account: string
  description: string
  status: string
  creation_date_time: string
  external_payment_id?: string
}

export const paymentsAPI = {
  createPayment: async (data: PaymentRequest): Promise<PaymentResponse> => {
    // Преобразуем упрощенный формат в формат OpenBanking Russia v2.1
    // Используем переданный account_number или получаем из account_id
    let fromAccountNumber = data.from_account_number || data.from_account_id
    
    // Если account_number не передан, пытаемся получить из API
    if (!data.from_account_number) {
      try {
        const accountResponse = await api.get<any>(`/accounts/${data.from_account_id}`)
        const account = accountResponse.data?.data?.account?.[0]
        if (account?.account?.[0]?.identification) {
          fromAccountNumber = account.account[0].identification
        } else if (account?.accountNumber) {
          fromAccountNumber = account.accountNumber
        }
      } catch (error) {
        // Если account_id это уже номер счета (только цифры), используем его напрямую
        if (data.from_account_id.match(/^\d+$/)) {
          fromAccountNumber = data.from_account_id
        } else {
          console.warn('Failed to get account number, using account_id:', error)
        }
      }
    }

    // Формируем запрос в формате OpenBanking Russia v2.1
    const openBankingRequest = {
      data: {
        initiation: {
          instructedAmount: {
            amount: data.amount.toFixed(2),
            currency: data.currency || 'RUB',
          },
          debtorAccount: {
            schemeName: 'RU.CBR.PAN',
            identification: fromAccountNumber,
          },
          creditorAccount: {
            schemeName: 'RU.CBR.PAN',
            identification: data.to_account_number,
            ...(data.to_bank_code && { bank_code: data.to_bank_code }),
          },
          remittanceInformation: {
            unstructured: data.description || '',
          },
        },
      },
      risk: {},
    }

    const response = await api.post<any>('/payments', openBankingRequest)
    
    // Преобразуем ответ OpenBanking в наш формат
    const paymentData = response.data?.data
    return {
      payment_id: paymentData?.paymentId || '',
      status: paymentData?.status || 'pending',
      created_at: paymentData?.creationDateTime || new Date().toISOString(),
      from_account_id: data.from_account_id,
      to_account_number: data.to_account_number,
      amount: data.amount,
      currency: data.currency || 'RUB',
    }
  },

  getPaymentStatus: async (paymentId: string): Promise<PaymentResponse> => {
    const response = await api.get<PaymentResponse>(`/payments/${paymentId}`)
    return response.data
  },

  createExternalPayment: async (data: ExternalPaymentRequest): Promise<ExternalPaymentResponse> => {
    const response = await api.post<any>('/payments/external', data)
    return {
      payment_id: response.data?.payment_id || '',
      status: response.data?.status || 'pending',
      message: response.data?.message,
      error: response.data?.error,
    }
  },

  getExternalPaymentHistory: async (page: number = 1): Promise<{ payments: ExternalPaymentHistoryItem[], meta: any }> => {
    const response = await api.get<any>(`/payments/external/history?page=${page}`)
    return {
      payments: response.data?.data?.payments || [],
      meta: response.data?.meta || {},
    }
  },

  refreshExternalPaymentHistory: async (page: number = 1): Promise<{ payments: ExternalPaymentHistoryItem[], meta: any }> => {
    // First invalidate the cache
    await api.post('/payments/external/history/refresh')

    // Then fetch fresh data with cache-busting parameters
    const timestamp = Date.now()
    const response = await api.get<any>(`/payments/external/history?page=${page}&_t=${timestamp}`, {
      headers: {
        'Cache-Control': 'no-cache, no-store, must-revalidate',
        'Pragma': 'no-cache'
      }
    })

    return {
      payments: response.data?.data?.payments || [],
      meta: response.data?.meta || {},
    }
  },
}

export const bankerAPI = {
  getClients: async (): Promise<Client[]> => {
    const response = await api.get<any>('/banker/clients')
    // API возвращает массив или объект с data
    const clients = Array.isArray(response.data) ? response.data : (response.data?.data || [])
    // Преобразуем формат если нужно
    return clients.map((c: any) => ({
      client_id: c.person_id || c.id || String(c.id || Math.random()),
      person_id: c.person_id || '',
      first_name: c.full_name?.split(' ')[0] || '',
      last_name: c.full_name?.split(' ')[1] || c.full_name || '',
      patronymic: c.full_name?.split(' ')[2] || '',
      phone: c.phone || '',
      email: c.email || '',
      passport_number: c.passport_number || '',
      registration_date: c.created_at || new Date().toISOString(),
    }))
  },

  getProducts: async (): Promise<Product[]> => {
    const response = await api.get<any>('/banker/products')
    // API возвращает массив
    const products = Array.isArray(response.data) ? response.data : []
    return products.map((p: any) => ({
      product_id: p.product_id || String(p.id || Math.random()),
      product_type: p.product_type || '',
      name: p.name || '',
      description: p.description || '',
      interest_rate: p.interest_rate ? parseFloat(p.interest_rate) : undefined,
      min_amount: p.min_amount ? parseFloat(p.min_amount) : undefined,
      max_amount: p.max_amount ? parseFloat(p.max_amount) : undefined,
      term_months: p.term_months || undefined,
      is_active: p.is_active !== undefined ? p.is_active : true,
    }))
  },

  getStats: async (): Promise<BankStats> => {
    const response = await api.get<any>('/banker/stats')
    return {
      total_clients: response.data?.total_clients || 0,
      total_accounts: response.data?.total_accounts || 0,
      total_transactions: response.data?.total_transactions || 0,
      total_balance: response.data?.total_balance || 0,
      active_consents: response.data?.active_consents || 0,
    }
  },

  getAPILogs: async (): Promise<APILog[]> => {
    const response = await api.get<any>('/banker/api-logs')
    // API возвращает массив
    const logs = Array.isArray(response.data) ? response.data : []
    return logs.map((log: any) => ({
      id: String(log.id || Math.random()),
      timestamp: log.timestamp || log.created_at || new Date().toISOString(),
      method: log.method || 'GET',
      path: log.path || log.endpoint || '',
      status_code: log.status_code || 200,
      duration_ms: log.duration_ms || log.response_time_ms || 0,
      client_id: log.client_id || log.person_id,
      team_client_id: log.team_client_id || log.caller_id,
    }))
  },

  getTransactions: async (): Promise<Transaction[]> => {
    const response = await api.get<any>('/banker/transactions')
    // API возвращает массив
    const transactions = Array.isArray(response.data) ? response.data : []
    return transactions.map((tx: any) => ({
      transaction_id: tx.transaction_id || String(tx.id || Math.random()),
      account_id: String(tx.account_id || ''),
      amount: parseFloat(tx.amount || '0'),
      currency: tx.currency || 'RUB',
      transaction_type: tx.transaction_type || (tx.direction === 'credit' ? 'credit' : 'debit'),
      description: tx.description || '',
      created_at: tx.created_at || tx.transaction_date || new Date().toISOString(),
      status: tx.status || 'completed',
      counterparty_name: tx.counterparty || tx.counterparty_name,
      counterparty_account: tx.counterparty_account,
    }))
  },

  getPendingConsents: async (): Promise<any[]> => {
    const response = await api.get<any>('/banker/consents/pending')
    return response.data?.data || []
  },

  getAllConsents: async (): Promise<any[]> => {
    const response = await api.get<any>('/banker/consents/all')
    return response.data?.data || []
  },

  approveConsent: async (requestId: string): Promise<void> => {
    await api.put(`/banker/consents/${requestId}/approve`)
  },

  rejectConsent: async (requestId: string): Promise<void> => {
    await api.put(`/banker/consents/${requestId}/reject`)
  },
}

export const adminAPI = {
  getTeams: async (): Promise<any[]> => {
    const response = await api.get<any>('/admin/teams')
    return response.data?.teams || []
  },

  suspendTeam: async (clientId: string): Promise<void> => {
    await api.put(`/admin/teams/${clientId}/suspend`)
  },

  activateTeam: async (clientId: string): Promise<void> => {
    await api.put(`/admin/teams/${clientId}/activate`)
  },

  deleteTeam: async (clientId: string): Promise<void> => {
    await api.delete(`/admin/teams/${clientId}`)
  },
}

export const virtualAccountsAPI = {
  getVirtualAccounts: async (): Promise<VirtualAccount[]> => {
    const response = await api.get<VirtualAccountListResponse>('/virtual-accounts')
    return response.data?.data || []
  },

  getVirtualAccount: async (accountId: number): Promise<VirtualAccount> => {
    const response = await api.get<VirtualAccount>(`/virtual-accounts/${accountId}`)
    return response.data
  },

  createVirtualAccount: async (data: VirtualAccountCreate): Promise<VirtualAccount> => {
    const response = await api.post<VirtualAccount>('/virtual-accounts', data)
    return response.data
  },

  updateVirtualAccount: async (accountId: number, data: VirtualAccountUpdate): Promise<VirtualAccount> => {
    const response = await api.put<VirtualAccount>(`/virtual-accounts/${accountId}`, data)
    return response.data
  },

  deleteVirtualAccount: async (accountId: number): Promise<void> => {
    await api.delete(`/virtual-accounts/${accountId}`)
  },
}

export const balanceAllocationsAPI = {
  getBalanceAllocations: async (): Promise<BalanceAllocation[]> => {
    const response = await api.get<BalanceAllocationListResponse>('/balance-allocations')
    return response.data?.data || []
  },

  getBalanceAllocation: async (allocationId: number): Promise<BalanceAllocation> => {
    const response = await api.get<BalanceAllocation>(`/balance-allocations/${allocationId}`)
    return response.data
  },

  createBalanceAllocation: async (data: BalanceAllocationCreate): Promise<BalanceAllocation> => {
    const response = await api.post<BalanceAllocation>('/balance-allocations', data)
    return response.data
  },

  updateBalanceAllocation: async (allocationId: number, data: BalanceAllocationUpdate): Promise<BalanceAllocation> => {
    const response = await api.put<BalanceAllocation>(`/balance-allocations/${allocationId}`, data)
    return response.data
  },

  deleteBalanceAllocation: async (allocationId: number): Promise<void> => {
    await api.delete(`/balance-allocations/${allocationId}`)
  },

  refreshBalanceAllocations: async (): Promise<void> => {
    // Invalidate cache first
    await api.post('/balance-allocations/refresh', {}, {
      headers: {
        'Cache-Control': 'no-cache'
      }
    })
  },

  getBalanceAllocationsWithRefresh: async (): Promise<BalanceAllocation[]> => {
    // First invalidate cache
    await api.post('/balance-allocations/refresh', {}, {
      headers: {
        'Cache-Control': 'no-cache'
      }
    })

    // Then fetch fresh data with cache-busting parameters
    const timestamp = Date.now()
    const response = await api.get<BalanceAllocationListResponse>(`/balance-allocations?_t=${timestamp}`, {
      headers: {
        'Cache-Control': 'no-cache, no-store, must-revalidate',
        'Pragma': 'no-cache'
      }
    })

    return response.data?.data || []
  },
}

export default api

