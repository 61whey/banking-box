import { useEffect, useState } from 'react'
import { ClientLayout } from '@/components/layouts/client-layout'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { accountsAPI, paymentsAPI } from '@/lib/api'
import { useToast } from '@/hooks/use-toast'
import type { Account } from '@/types/api'
import type { ExternalPaymentHistoryItem } from '@/lib/api'
import { Send, ArrowLeftRight, History, ChevronLeft, ChevronRight, RefreshCw } from 'lucide-react'
import { format } from 'date-fns'
import { ru } from 'date-fns/locale'

interface ExternalAccount {
  bank_code: string
  bank_name: string
  account: any
  balance: string | null
  error: string | null
}

export default function ClientTransfers() {
  const [accounts, setAccounts] = useState<Account[]>([])
  const [externalAccounts, setExternalAccounts] = useState<ExternalAccount[]>([])
  const [fromAccount, setFromAccount] = useState('')
  const [toAccountNumber, setToAccountNumber] = useState('')
  const [amount, setAmount] = useState('')
  const [description, setDescription] = useState('')
  const [toBankCode, setToBankCode] = useState('')
  const [loading, setLoading] = useState(false)
  
  // Multibank transfer state
  const [multibankFromAccount, setMultibankFromAccount] = useState('')
  const [multibankToAccount, setMultibankToAccount] = useState('')
  const [multibankAmount, setMultibankAmount] = useState('')
  const [multibankLoading, setMultibankLoading] = useState(false)
  const [loadingExternal, setLoadingExternal] = useState(true)
  
  // Transfer history state
  const [transferHistory, setTransferHistory] = useState<ExternalPaymentHistoryItem[]>([])
  const [historyLoading, setHistoryLoading] = useState(true)
  const [historyRefreshing, setHistoryRefreshing] = useState(false)
  const [currentPage, setCurrentPage] = useState(1)
  const [totalPages, setTotalPages] = useState(0)
  const [totalItems, setTotalItems] = useState(0)
  
  const { toast } = useToast()

  useEffect(() => {
    const fetchAccounts = async () => {
      try {
        const data = await accountsAPI.getAccounts()
        setAccounts(data)
        if (data.length > 0) {
          setFromAccount(data[0].account_id)
        }
      } catch (error: any) {
        toast({
          title: 'Ошибка загрузки',
          description: error.response?.data?.detail || 'Не удалось загрузить счета',
          variant: 'destructive',
        })
      }
    }

    fetchAccounts()
  }, [toast])

  useEffect(() => {
    const fetchExternalAccounts = async () => {
      try {
        const externalData = await accountsAPI.getExternalAccounts()
        const externalArray = Array.isArray(externalData) ? externalData : []
        // Filter only successful accounts
        const validAccounts = externalArray.filter((acc: any) => acc.account !== null && acc.error === null)
        setExternalAccounts(validAccounts)
        console.log('External accounts for transfers:', validAccounts.length)
      } catch (error: any) {
        console.error('Failed to load external accounts:', error)
        setExternalAccounts([])
      } finally {
        setLoadingExternal(false)
      }
    }

    fetchExternalAccounts()
  }, [])

  useEffect(() => {
    fetchTransferHistory(currentPage)
  }, [currentPage])

  const fetchTransferHistory = async (page: number) => {
    setHistoryLoading(true)
    try {
      const { payments, meta } = await paymentsAPI.getExternalPaymentHistory(page)
      setTransferHistory(payments)
      setCurrentPage(meta.page || page)
      setTotalPages(meta.total_pages || 0)
      setTotalItems(meta.total || 0)
    } catch (error: any) {
      console.error('Failed to load transfer history:', error)
      setTransferHistory([])
    } finally {
      setHistoryLoading(false)
    }
  }

  const handleRefreshHistory = async () => {
    setHistoryRefreshing(true)
    try {
      const { payments, meta } = await paymentsAPI.refreshExternalPaymentHistory(currentPage)
      setTransferHistory(payments)
      setCurrentPage(meta.page || currentPage)
      setTotalPages(meta.total_pages || 0)
      setTotalItems(meta.total || 0)
      
      toast({
        title: 'Обновлено',
        description: 'История переводов успешно обновлена',
      })
    } catch (error: any) {
      console.error('Failed to refresh transfer history:', error)
      toast({
        title: 'Ошибка обновления',
        description: error.response?.data?.detail || 'Не удалось обновить историю переводов',
        variant: 'destructive',
      })
    } finally {
      setHistoryRefreshing(false)
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)

    try {
      // Находим выбранный счет для получения account_number
      const selectedAccount = accounts.find((acc) => acc.account_id === fromAccount)
      const fromAccountNumber = selectedAccount?.account_number || fromAccount

      const payment = await paymentsAPI.createPayment({
        from_account_id: fromAccount,
        from_account_number: fromAccountNumber,
        to_account_number: toAccountNumber,
        amount: parseFloat(amount),
        currency: 'RUB',
        description,
        to_bank_code: toBankCode || undefined,
      })

      toast({
        title: 'Платеж создан',
        description: `Платеж ${payment.payment_id} успешно создан`,
      })

      setToAccountNumber('')
      setAmount('')
      setDescription('')
      setToBankCode('')
    } catch (error: any) {
      toast({
        title: 'Ошибка',
        description: error.response?.data?.detail || 'Не удалось создать платеж',
        variant: 'destructive',
      })
    } finally {
      setLoading(false)
    }
  }

  const handleMultibankSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setMultibankLoading(true)

    if (!multibankFromAccount || !multibankToAccount || !multibankAmount) {
      toast({
        title: 'Внимание',
        description: 'Заполните все поля!',
        variant: 'destructive',
      })
      setMultibankLoading(false)
      return
    }

    if (parseFloat(multibankAmount) <= 0) {
      toast({
        title: 'Внимание',
        description: 'Сумма должна быть больше нуля!',
        variant: 'destructive',
      })
      setMultibankLoading(false)
      return
    }

    try {
      const result = await paymentsAPI.createExternalPayment({
        from_account: multibankFromAccount,
        to_account: multibankToAccount,
        amount: parseFloat(multibankAmount),
        description: 'Перевод через Мультибанк',
      })

      if (result.error) {
        throw new Error(result.error)
      }

      toast({
        title: 'Успех',
        description: `Платеж ${result.payment_id} успешно создан через внешний банк`,
      })

      // Clear form
      setMultibankFromAccount('')
      setMultibankToAccount('')
      setMultibankAmount('')

      // Reload transfer history
      setTimeout(() => {
        fetchTransferHistory(currentPage)
      }, 1000)
    } catch (error: any) {
      toast({
        title: 'Ошибка платежа',
        description: error.response?.data?.detail || error.message || 'Не удалось создать платеж',
        variant: 'destructive',
      })
    } finally {
      setMultibankLoading(false)
    }
  }

  // Create options for multibank dropdowns
  const multibankOptions = externalAccounts.map((acc) => {
    const accountNumber =
      acc.account?.account && acc.account.account[0]
        ? acc.account.account[0].identification
        : ''
    const displayText = `${acc.bank_name} - ${accountNumber}`
    const value = `${acc.bank_code}:${accountNumber}`
    return { value, displayText, accountNumber }
  })

  const getStatusColor = (status: string) => {
    const statusLower = status.toLowerCase()
    if (statusLower.includes('completed') || statusLower.includes('accepted')) {
      return 'text-green-600'
    } else if (statusLower.includes('rejected') || statusLower.includes('failed')) {
      return 'text-red-600'
    } else {
      return 'text-yellow-600'
    }
  }

  return (
    <ClientLayout title="Переводы">
      <div className="space-y-6">
        {/* Multibank Transfers Section */}
        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <ArrowLeftRight className="h-5 w-5 text-primary" />
              <CardTitle>Переводы Мультибанк</CardTitle>
            </div>
            <CardDescription>
              Переводы между счетами из разных банков через OpenBanking
            </CardDescription>
          </CardHeader>
          <CardContent>
            {loadingExternal ? (
              <p className="text-muted-foreground">Загрузка счетов...</p>
            ) : externalAccounts.length === 0 ? (
              <p className="text-muted-foreground">
                Нет доступных счетов из других банков. Добавьте согласие в разделе "Согласия".
              </p>
            ) : (
              <form onSubmit={handleMultibankSubmit} className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="multibank-from">Откуда</Label>
                  <select
                    id="multibank-from"
                    className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                    value={multibankFromAccount}
                    onChange={(e) => setMultibankFromAccount(e.target.value)}
                    required
                    disabled={multibankLoading}
                  >
                    <option value="">Выберите счет</option>
                    {multibankOptions.map((opt, idx) => (
                      <option key={idx} value={opt.value}>
                        {opt.displayText}
                      </option>
                    ))}
                  </select>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="multibank-to">Куда</Label>
                  <select
                    id="multibank-to"
                    className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                    value={multibankToAccount}
                    onChange={(e) => setMultibankToAccount(e.target.value)}
                    required
                    disabled={multibankLoading}
                  >
                    <option value="">Выберите счет</option>
                    {multibankOptions.map((opt, idx) => (
                      <option key={idx} value={opt.value}>
                        {opt.displayText}
                      </option>
                    ))}
                  </select>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="multibank-amount">Сумма (₽)</Label>
                  <Input
                    id="multibank-amount"
                    type="number"
                    step="0.01"
                    min="0.01"
                    placeholder="1000"
                    value={multibankAmount}
                    onChange={(e) => setMultibankAmount(e.target.value)}
                    required
                    disabled={multibankLoading}
                  />
                </div>

                <div className="space-y-2">
                  <Label>&nbsp;</Label>
                  <Button type="submit" className="w-full" disabled={multibankLoading}>
                    {multibankLoading ? 'Отправка...' : 'Перевести'}
                  </Button>
                </div>
              </form>
            )}
          </CardContent>
        </Card>

        {/* Transfer History Section */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <History className="h-5 w-5 text-primary" />
                <CardTitle>История переводов</CardTitle>
              </div>
              <Button
                variant="outline"
                size="sm"
                onClick={handleRefreshHistory}
                disabled={historyRefreshing || historyLoading}
              >
                <RefreshCw className={`h-4 w-4 mr-2 ${historyRefreshing ? 'animate-spin' : ''}`} />
                Обновить
              </Button>
            </div>
            <CardDescription>История переводов из внешних банков</CardDescription>
          </CardHeader>
          <CardContent>
            {historyLoading ? (
              <p className="text-muted-foreground">Загрузка истории переводов...</p>
            ) : transferHistory.length === 0 ? (
              <div className="text-center py-8 text-muted-foreground">
                <History className="h-12 w-12 mx-auto mb-4 opacity-50" />
                <p>История переводов из внешних банков пуста</p>
              </div>
            ) : (
              <>
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead>
                      <tr className="border-b">
                        <th className="text-left p-3 font-medium text-sm">Дата/Время</th>
                        <th className="text-left p-3 font-medium text-sm">Банк-отправитель</th>
                        <th className="text-left p-3 font-medium text-sm">Счет-отправитель</th>
                        <th className="text-left p-3 font-medium text-sm">Банк-получатель</th>
                        <th className="text-left p-3 font-medium text-sm">Счет-получатель</th>
                        <th className="text-right p-3 font-medium text-sm">Сумма</th>
                        <th className="text-left p-3 font-medium text-sm">Статус</th>
                        <th className="text-left p-3 font-medium text-sm">Описание</th>
                      </tr>
                    </thead>
                    <tbody>
                      {transferHistory.map((payment, idx) => (
                        <tr key={idx} className="border-b">
                          <td className="p-3 text-sm">
                            {format(new Date(payment.creation_date_time), 'dd.MM.yyyy HH:mm', {
                              locale: ru,
                            })}
                          </td>
                          <td className="p-3 text-sm font-medium">{payment.source_bank}</td>
                          <td className="p-3 text-sm font-mono text-xs">
                            {payment.source_account}
                          </td>
                          <td className="p-3 text-sm font-medium">{payment.destination_bank}</td>
                          <td className="p-3 text-sm font-mono text-xs">
                            {payment.destination_account}
                          </td>
                          <td className="p-3 text-sm text-right font-semibold">
                            {payment.amount.toLocaleString('ru-RU', {
                              minimumFractionDigits: 2,
                              maximumFractionDigits: 2,
                            })}{' '}
                            ₽
                          </td>
                          <td className={`p-3 text-sm font-medium ${getStatusColor(payment.status)}`}>
                            {payment.status}
                          </td>
                          <td className="p-3 text-sm">{payment.description}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>

                {/* Pagination */}
                {totalPages > 1 && (
                  <div className="flex justify-between items-center mt-4 pt-4 border-t">
                    <div className="text-sm text-muted-foreground">
                      Страница {currentPage} из {totalPages} (Всего: {totalItems})
                    </div>
                    <div className="flex gap-2">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
                        disabled={currentPage === 1 || historyLoading}
                      >
                        <ChevronLeft className="h-4 w-4" />
                        Назад
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
                        disabled={currentPage === totalPages || historyLoading}
                      >
                        Вперед
                        <ChevronRight className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                )}
              </>
            )}
          </CardContent>
        </Card>

        {/* Regular Transfer Section */}
        <Card className="max-w-2xl">
          <CardHeader>
            <CardTitle>Новый перевод</CardTitle>
            <CardDescription>Отправка денег на другой счет</CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="from-account">Счет списания</Label>
                <select
                  id="from-account"
                  className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                  value={fromAccount}
                  onChange={(e) => setFromAccount(e.target.value)}
                  required
                  disabled={loading}
                >
                  {accounts.map((account) => (
                    <option key={account.account_id} value={account.account_id}>
                      {account.account_number} - {account.balance.toLocaleString('ru-RU')} ₽
                    </option>
                  ))}
                </select>
              </div>

              <div className="space-y-2">
                <Label htmlFor="to-account">Счет получателя</Label>
                <Input
                  id="to-account"
                  type="text"
                  placeholder="40817810099910004312"
                  value={toAccountNumber}
                  onChange={(e) => setToAccountNumber(e.target.value)}
                  required
                  disabled={loading}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="to-bank">Код банка получателя (опционально)</Label>
                <Input
                  id="to-bank"
                  type="text"
                  placeholder="ABANK, SBANK и т.д."
                  value={toBankCode}
                  onChange={(e) => setToBankCode(e.target.value)}
                  disabled={loading}
                />
                <p className="text-xs text-muted-foreground">
                  Оставьте пустым для перевода внутри банка
                </p>
              </div>

              <div className="space-y-2">
                <Label htmlFor="amount">Сумма</Label>
                <Input
                  id="amount"
                  type="number"
                  step="0.01"
                  min="0.01"
                  placeholder="1000.00"
                  value={amount}
                  onChange={(e) => setAmount(e.target.value)}
                  required
                  disabled={loading}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="description">Назначение платежа</Label>
                <Input
                  id="description"
                  type="text"
                  placeholder="Перевод за товары"
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  required
                  disabled={loading}
                />
              </div>

              <Button type="submit" className="w-full" disabled={loading}>
                {loading ? (
                  'Отправка...'
                ) : (
                  <>
                    <Send className="mr-2 h-4 w-4" />
                    Отправить
                  </>
                )}
              </Button>
            </form>
          </CardContent>
        </Card>
      </div>
    </ClientLayout>
  )
}
