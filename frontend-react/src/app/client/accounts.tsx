import { useEffect, useState } from 'react'
import { ClientLayout } from '@/components/layouts/client-layout'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { accountsAPI } from '@/lib/api'
import { useToast } from '@/hooks/use-toast'
import type { Account } from '@/types/api'
import { CreditCard, Building2, RefreshCw } from 'lucide-react'

export default function ClientAccounts() {
  const [accounts, setAccounts] = useState<Account[]>([])
  const [externalAccounts, setExternalAccounts] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [loadingExternal, setLoadingExternal] = useState(true)
  const [externalAccountsError, setExternalAccountsError] = useState<string | null>(null)
  const { toast } = useToast()

  useEffect(() => {
    const fetchAccounts = async () => {
      try {
        const data = await accountsAPI.getAccounts()
        setAccounts(data)
      } catch (error: any) {
        toast({
          title: 'Ошибка загрузки',
          description: error.response?.data?.detail || 'Не удалось загрузить счета',
          variant: 'destructive',
        })
      } finally {
        setLoading(false)
      }
    }

    fetchAccounts()
  }, [toast])

  useEffect(() => {
    const fetchExternalAccounts = async () => {
      try {
        setExternalAccountsError(null)
        const externalData = await accountsAPI.getExternalAccounts()
        const externalArray = Array.isArray(externalData) ? externalData : []
        setExternalAccounts(externalArray)
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

  const handleRefreshExternalAccounts = async () => {
    setLoadingExternal(true)
    setExternalAccountsError(null)
    try {
      // Invalidate cache and fetch fresh data
      const externalArray = await accountsAPI.getExternalAccountsWithRefresh()
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
    <ClientLayout title="Мои счета">
      <Card className="mb-6">
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

      {loading ? (
        <p className="text-muted-foreground">Загрузка...</p>
      ) : accounts.length === 0 ? (
        <Card>
          <CardContent className="pt-6">
            <p className="text-center text-muted-foreground">У вас нет счетов</p>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {accounts.map((account) => (
            <Card key={account.account_id}>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CreditCard className="h-8 w-8 text-primary" />
                  <span className={`px-2 py-1 text-xs rounded ${
                    account.status === 'active' 
                      ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200' 
                      : 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-200'
                  }`}>
                    {account.status}
                  </span>
                </div>
                <CardTitle className="text-lg mt-4">{account.account_number}</CardTitle>
                <CardDescription>{account.account_type}</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  <div className="flex justify-between">
                    <span className="text-sm text-muted-foreground">Баланс:</span>
                    <span className="font-bold text-lg">
                      {account.balance.toLocaleString('ru-RU')} {account.currency}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm text-muted-foreground">Банк:</span>
                    <span className="text-sm">{account.bank_code}</span>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </ClientLayout>
  )
}

