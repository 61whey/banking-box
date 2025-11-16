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

export enum AccountType {
  Checking = "checking",
  Savings = "savings"
}

export enum CalculationType {
  Automatic = "automatic",
  Fixed = "fixed"
}

export enum Currency {
  RUB = "RUB"
}

export interface VirtualAccount {
  id: number
  client_id: number
  account_number: string
  account_type: string
  calculation_type: string
  balance: string
  currency: string
  status: string
  created_at: string
  updated_at: string | null
}

export interface VirtualAccountCreate {
  account_type: string
  calculation_type: string
  balance?: string
  currency: string
}

export interface VirtualAccountUpdate {
  account_type?: string
  calculation_type?: string
  balance?: string
  currency?: string
  status?: string
}

export interface VirtualAccountListResponse {
  data: VirtualAccount[]
  count: number
}

export interface BalanceAllocation {
  id: number | null
  client_id: number
  bank_id: number
  bank_code: string
  bank_name: string
  target_share: number | null
  account_type: string
  actual_amount: string
  actual_share: number
  created_at: string | null
  updated_at: string | null
}

export interface BalanceAllocationCreate {
  bank_id: number
  target_share: number
  account_type: string
}

export interface BalanceAllocationUpdate {
  target_share?: number
  account_type?: string
}

export interface BalanceAllocationListResponse {
  data: BalanceAllocation[]
  count: number
}

export interface TargetBankAmount {
  bank_id: number
  bank_code: string
  bank_name: string
  target_share: number
  target_amount: number
  accounts_count: number
}

export interface TargetAccountBalance {
  bank_code: string
  bank_name: string
  account_id: string
  current_balance: number
  target_balance: number
}

export interface PaymentItem {
  source_account_id: string
  destination_account_id: string
  amount: number
  source_bank: string
  source_bank_id: number
  destination_bank: string
  destination_bank_id: number
}

export interface ExecutedPaymentResult {
  source_account_id: string
  destination_account_id: string
  amount: number
  source_bank: string
  source_bank_id: number
  destination_bank: string
  destination_bank_id: number
  status: 'success' | 'failed'
  error_message: string | null
  payment_id: string | null
}

export interface ApplyAllocationsData {
  external_accounts_count: number
  total_balance: number
  target_bank_amounts: TargetBankAmount[]
  target_account_balances: TargetAccountBalance[]
  payments_list: PaymentItem[]
  executed_payments?: ExecutedPaymentResult[]
  successful_count?: number
  failed_count?: number
}

export interface ApplyAllocationsResponse {
  success: boolean
  message: string
  data: ApplyAllocationsData | null
}

