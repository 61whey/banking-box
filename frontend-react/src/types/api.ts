export interface LoginRequest {
  username: string
  password: string
}

export interface LoginResponse {
  access_token: string
  token_type: string
  client_id: string
}

export interface BankerLoginRequest {
  username: string
  password: string
}

export interface BankerLoginResponse {
  access_token: string
  token_type: string
}

export interface Account {
  account_id: string
  account_number: string
  account_type: string
  balance: number
  currency: string
  status: string
  bank_code: string
  client_person_id?: string
}

export interface Transaction {
  transaction_id: string
  account_id: string
  amount: number
  currency: string
  transaction_type: string
  description: string
  created_at: string
  status: string
  counterparty_name?: string
  counterparty_account?: string
}

export interface Consent {
  consent_id: string
  status: string
  permissions: string[]
  expiration_date: string
  created_at: string
  team_name?: string
  team_client_id?: string
}

export interface PaymentRequest {
  from_account_id: string
  from_account_number?: string  // Опционально, если не указан - будет получен из account_id
  to_account_number: string
  amount: number
  currency: string
  description: string
  to_bank_code?: string
}

export interface PaymentResponse {
  payment_id: string
  status: string
  created_at: string
  from_account_id: string
  to_account_number: string
  amount: number
  currency: string
}

export interface Client {
  client_id: string
  person_id: string
  first_name: string
  last_name: string
  patronymic?: string
  phone?: string
  email?: string
  passport_number?: string
  registration_date: string
}

export interface Product {
  product_id: string
  product_type: string
  name: string
  description: string
  interest_rate?: number
  min_amount?: number
  max_amount?: number
  term_months?: number
  is_active: boolean
}

export interface BankStats {
  total_clients: number
  total_accounts: number
  total_transactions: number
  total_balance: number
  active_consents: number
}

export interface APILog {
  id: string
  timestamp: string
  method: string
  path: string
  status_code: number
  duration_ms: number
  client_id?: string
  team_client_id?: string
}

