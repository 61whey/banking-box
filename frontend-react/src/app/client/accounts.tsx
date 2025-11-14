import { useEffect, useState } from 'react'
import { ClientLayout } from '@/components/layouts/client-layout'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { accountsAPI } from '@/lib/api'
import { useToast } from '@/hooks/use-toast'
import type { Account } from '@/types/api'
import { CreditCard } from 'lucide-react'

export default function ClientAccounts() {
  const [accounts, setAccounts] = useState<Account[]>([])
  const [loading, setLoading] = useState(true)
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

  return (
    <ClientLayout title="Мои счета">
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

