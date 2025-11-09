import { useEffect, useState } from 'react'
import { BankerLayout } from '@/components/layouts/banker-layout'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { bankerAPI } from '@/lib/api'
import { useToast } from '@/hooks/use-toast'
import type { APILog, Transaction } from '@/types/api'
import { format } from 'date-fns'
import { ru } from 'date-fns/locale'

export default function BankerMonitoring() {
  const [apiLogs, setApiLogs] = useState<APILog[]>([])
  const [transactions, setTransactions] = useState<Transaction[]>([])
  const [loading, setLoading] = useState(true)
  const { toast } = useToast()

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [logsData, transactionsData] = await Promise.all([
          bankerAPI.getAPILogs(),
          bankerAPI.getTransactions(),
        ])
        // Убеждаемся что данные это массивы
        const logsArray = Array.isArray(logsData) ? logsData : []
        const transactionsArray = Array.isArray(transactionsData) ? transactionsData : []
        setApiLogs(logsArray.slice(0, 10))
        setTransactions(transactionsArray.slice(0, 10))
      } catch (error: any) {
        toast({
          title: 'Ошибка загрузки',
          description: error.response?.data?.detail || 'Не удалось загрузить данные',
          variant: 'destructive',
        })
      } finally {
        setLoading(false)
      }
    }

    fetchData()
  }, [toast])

  return (
    <BankerLayout title="Мониторинг">
      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>API логи</CardTitle>
            <CardDescription>Последние 10 запросов к API</CardDescription>
          </CardHeader>
          <CardContent>
            {loading ? (
              <p className="text-muted-foreground">Загрузка...</p>
            ) : apiLogs.length === 0 ? (
              <p className="text-muted-foreground">Нет логов</p>
            ) : (
              <div className="space-y-3">
                {apiLogs.map((log) => (
                  <div key={log.id} className="p-3 border rounded-lg text-sm">
                    <div className="flex justify-between items-start mb-1">
                      <span className="font-mono">
                        {log.method} {log.path}
                      </span>
                      <span
                        className={`px-2 py-1 text-xs rounded ${
                          log.status_code >= 200 && log.status_code < 300
                            ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
                            : log.status_code >= 400
                            ? 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200'
                            : 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-200'
                        }`}
                      >
                        {log.status_code}
                      </span>
                    </div>
                    <div className="flex justify-between text-xs text-muted-foreground">
                      <span>
                        {format(new Date(log.timestamp), 'HH:mm:ss dd.MM.yyyy', { locale: ru })}
                      </span>
                      <span>{log.duration_ms}ms</span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Последние транзакции</CardTitle>
            <CardDescription>Последние 10 транзакций в системе</CardDescription>
          </CardHeader>
          <CardContent>
            {loading ? (
              <p className="text-muted-foreground">Загрузка...</p>
            ) : transactions.length === 0 ? (
              <p className="text-muted-foreground">Нет транзакций</p>
            ) : (
              <div className="space-y-3">
                {transactions.map((tx) => (
                  <div key={tx.transaction_id} className="p-3 border rounded-lg">
                    <div className="flex justify-between items-start mb-1">
                      <div className="flex-1">
                        <p className="text-sm font-medium">{tx.description}</p>
                        <p className="text-xs text-muted-foreground">
                          {format(new Date(tx.created_at), 'HH:mm dd MMM', { locale: ru })}
                        </p>
                      </div>
                      <div className="text-right">
                        <p
                          className={`text-sm font-bold ${
                            tx.transaction_type === 'credit'
                              ? 'text-green-600'
                              : 'text-red-600'
                          }`}
                        >
                          {tx.transaction_type === 'credit' ? '+' : '-'}
                          {tx.amount.toLocaleString('ru-RU')} ₽
                        </p>
                        <p className="text-xs text-muted-foreground">{tx.status}</p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </BankerLayout>
  )
}

