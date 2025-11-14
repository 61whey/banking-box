import { useEffect, useState } from 'react'
import { ClientLayout } from '@/components/layouts/client-layout'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { accountsAPI } from '@/lib/api'
import { useToast } from '@/hooks/use-toast'
import type { Account, Transaction } from '@/types/api'
import { CreditCard, TrendingUp, Wallet, Building2, RefreshCw } from 'lucide-react'
import { format } from 'date-fns'
import { ru } from 'date-fns/locale'

export default function ClientDashboard() {
  const [accounts, setAccounts] = useState<Account[]>([])
  const [externalAccounts, setExternalAccounts] = useState<any[]>([])
  const [recentTransactions, setRecentTransactions] = useState<Transaction[]>([])
  const [loading, setLoading] = useState(true)
  const [loadingExternal, setLoadingExternal] = useState(true)
  const [externalAccountsError, setExternalAccountsError] = useState<string | null>(null)
  const { toast } = useToast()

  useEffect(() => {
    const fetchData = async () => {
      try {
        const accountsData = await accountsAPI.getAccounts()
        // Убеждаемся что accountsData это массив
        const accountsArray = Array.isArray(accountsData) ? accountsData : []
        setAccounts(accountsArray)

        if (accountsArray.length > 0) {
          const transactionsData = await accountsAPI.getTransactions(accountsArray[0].account_id)
          // Убеждаемся что transactionsData это массив
          const transactionsArray = Array.isArray(transactionsData) ? transactionsData : []
          setRecentTransactions(transactionsArray.slice(0, 5))
        }
      } catch (error: any) {
        toast({
          title: 'Ошибка загрузки',
          description: error.response?.data?.detail || 'Не удалось загрузить данные',
          variant: 'destructive',
        })
        // Устанавливаем пустые массивы в случае ошибки
        setAccounts([])
        setRecentTransactions([])
      } finally {
        setLoading(false)
      }
    }

    fetchData()
  }, [toast])

  useEffect(() => {
    const fetchExternalAccounts = async () => {
      try {
        setExternalAccountsError(null)
        const externalData = await accountsAPI.getExternalAccounts()
        const externalArray = Array.isArray(externalData) ? externalData : []
        setExternalAccounts(externalArray)
        
        // Логируем для отладки
        console.log('External accounts loaded:', externalArray.length, 'accounts')
      } catch (error: any) {
        console.error('Failed to load external accounts:', error)
        const errorMessage = error.response?.data?.detail || 'Не удалось загрузить счета из других банков'
        setExternalAccountsError(errorMessage)
        setExternalAccounts([])
      } finally {
        setLoadingExternal(false)
      }
    }

    fetchExternalAccounts()
  }, [])

  const totalBalance = Array.isArray(accounts) ? accounts.reduce((sum, acc) => sum + (acc.balance || 0), 0) : 0

  const handleRefreshExternalAccounts = async () => {
    setLoadingExternal(true)
    setExternalAccountsError(null)
    try {
      const externalData = await accountsAPI.getExternalAccounts()
      const externalArray = Array.isArray(externalData) ? externalData : []
      setExternalAccounts(externalArray)
      console.log('External accounts refreshed:', externalArray.length, 'accounts')
      toast({
        title: 'Обновлено',
        description: `Загружено счетов: ${externalArray.length}`,
      })
    } catch (error: any) {
      console.error('Failed to refresh external accounts:', error)
      const errorMessage = error.response?.data?.detail || 'Не удалось загрузить счета из других банков'
      setExternalAccountsError(errorMessage)
      setExternalAccounts([])
      toast({
        title: 'Ошибка обновления',
        description: errorMessage,
        variant: 'destructive',
      })
    } finally {
      setLoadingExternal(false)
    }
  }

  return (
    <ClientLayout title="Обзор">
      <div className="grid gap-6 md:grid-cols-3 mb-6">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Всего счетов</CardTitle>
            <CreditCard className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{accounts.length}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Общий баланс</CardTitle>
            <Wallet className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {totalBalance.toLocaleString('ru-RU')} ₽
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Транзакций</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{recentTransactions.length}</div>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Мои счета</CardTitle>
            <CardDescription>Список ваших банковских счетов</CardDescription>
          </CardHeader>
          <CardContent>
            {loading ? (
              <p className="text-muted-foreground">Загрузка...</p>
            ) : accounts.length === 0 ? (
              <p className="text-muted-foreground">У вас нет счетов</p>
            ) : (
              <div className="space-y-4">
                {accounts.map((account) => (
                  <div
                    key={account.account_id}
                    className="flex justify-between items-center p-4 border rounded-lg"
                  >
                    <div>
                      <p className="font-medium">{account.account_number}</p>
                      <p className="text-sm text-muted-foreground">{account.account_type}</p>
                    </div>
                    <div className="text-right">
                      <p className="font-bold">{account.balance.toLocaleString('ru-RU')} ₽</p>
                      <p className="text-sm text-muted-foreground">{account.currency}</p>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Последние операции</CardTitle>
            <CardDescription>Недавние транзакции по вашим счетам</CardDescription>
          </CardHeader>
          <CardContent>
            {loading ? (
              <p className="text-muted-foreground">Загрузка...</p>
            ) : recentTransactions.length === 0 ? (
              <p className="text-muted-foreground">Нет транзакций</p>
            ) : (
              <div className="space-y-4">
                {recentTransactions.map((tx) => (
                  <div
                    key={tx.transaction_id}
                    className="flex justify-between items-start p-4 border rounded-lg"
                  >
                    <div className="flex-1">
                      <p className="font-medium">{tx.description}</p>
                      <p className="text-sm text-muted-foreground">
                        {format(new Date(tx.created_at), 'dd MMM yyyy, HH:mm', { locale: ru })}
                      </p>
                    </div>
                    <div className="text-right">
                      <p
                        className={`font-bold ${
                          tx.transaction_type === 'credit'
                            ? 'text-green-600'
                            : 'text-red-600'
                        }`}
                      >
                        {tx.transaction_type === 'credit' ? '+' : '-'}
                        {tx.amount.toLocaleString('ru-RU')} ₽
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      <Card className="mt-6">
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <div className="flex items-center gap-2">
                <Building2 className="h-5 w-5 text-primary" />
                <CardTitle>Счета Мультибанк</CardTitle>
              </div>
              <CardDescription>Счета из других банков, доступные через OpenBanking</CardDescription>
            </div>
            <button
              onClick={handleRefreshExternalAccounts}
              disabled={loadingExternal}
              className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-primary hover:bg-primary/10 rounded-md transition-colors disabled:opacity-50"
              title="Обновить счета"
            >
              <RefreshCw className={`h-4 w-4 ${loadingExternal ? 'animate-spin' : ''}`} />
              Обновить
            </button>
          </div>
        </CardHeader>
        <CardContent>
          {loadingExternal ? (
            <p className="text-muted-foreground">Загрузка...</p>
          ) : externalAccountsError ? (
            <div className="text-sm text-red-600">
              <p>Ошибка: {externalAccountsError}</p>
            </div>
          ) : externalAccounts.length === 0 ? (
            <p className="text-muted-foreground">
              Нет подключенных счетов из других банков. Добавьте согласие в разделе "Согласия".
            </p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b">
                    <th className="text-left p-4 font-medium">Банк</th>
                    <th className="text-left p-4 font-medium">Номер счета</th>
                    <th className="text-left p-4 font-medium">Тип</th>
                    <th className="text-right p-4 font-medium">Баланс</th>
                  </tr>
                </thead>
                <tbody>
                  {externalAccounts.map((acc: any, idx: number) => {
                    const account = acc.account
                    const accountNumber =
                      account?.account && account.account[0]
                        ? account.account[0].identification
                        : 'N/A'
                    const accountType = account?.accountSubType || account?.accountType || 'N/A'
                    const balance = acc.balance
                      ? parseFloat(acc.balance).toLocaleString('ru-RU') + ' ₽'
                      : 'N/A'

                    return (
                      <tr key={idx} className="border-b">
                        <td className="p-4 font-medium">{acc.bank_name || 'N/A'}</td>
                        <td className="p-4 font-mono text-sm">{accountNumber}</td>
                        <td className="p-4">{accountType}</td>
                        <td className="p-4 text-right font-semibold">{balance}</td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>
    </ClientLayout>
  )
}

