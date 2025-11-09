import { useEffect, useState } from 'react'
import { ClientLayout } from '@/components/layouts/client-layout'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { accountsAPI, paymentsAPI } from '@/lib/api'
import { useToast } from '@/hooks/use-toast'
import type { Account } from '@/types/api'
import { Send } from 'lucide-react'

export default function ClientTransfers() {
  const [accounts, setAccounts] = useState<Account[]>([])
  const [fromAccount, setFromAccount] = useState('')
  const [toAccountNumber, setToAccountNumber] = useState('')
  const [amount, setAmount] = useState('')
  const [description, setDescription] = useState('')
  const [toBankCode, setToBankCode] = useState('')
  const [loading, setLoading] = useState(false)
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

  return (
    <ClientLayout title="Переводы">
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
    </ClientLayout>
  )
}

