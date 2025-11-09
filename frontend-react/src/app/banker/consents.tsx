import { useEffect, useState } from 'react'
import { BankerLayout } from '@/components/layouts/banker-layout'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { bankerAPI } from '@/lib/api'
import { useToast } from '@/hooks/use-toast'
import { FileText, CheckCircle, XCircle, Search } from 'lucide-react'
import { format } from 'date-fns'
import { ru } from 'date-fns/locale'

interface ConsentRequest {
  request_id: string
  client_id: string
  client_name: string
  requesting_bank: string
  requesting_bank_name: string
  permissions: string[]
  reason?: string
  status: string
  created_at: string
  responded_at?: string
}

export default function BankerConsents() {
  const [consents, setConsents] = useState<ConsentRequest[]>([])
  const [filteredConsents, setFilteredConsents] = useState<ConsentRequest[]>([])
  const [searchTerm, setSearchTerm] = useState('')
  const [loading, setLoading] = useState(true)
  const { toast } = useToast()

  const fetchConsents = async () => {
    try {
      const data = await bankerAPI.getAllConsents()
      const consentsArray = Array.isArray(data) ? data : []
      setConsents(consentsArray)
      setFilteredConsents(consentsArray)
    } catch (error: any) {
      toast({
        title: 'Ошибка загрузки',
        description: error.response?.data?.detail || 'Не удалось загрузить согласия',
        variant: 'destructive',
      })
      setConsents([])
      setFilteredConsents([])
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchConsents()
  }, [])

  useEffect(() => {
    if (searchTerm) {
      const filtered = consents.filter(
        (c) =>
          c.request_id.toLowerCase().includes(searchTerm.toLowerCase()) ||
          c.client_id.toLowerCase().includes(searchTerm.toLowerCase()) ||
          (c.requesting_bank && c.requesting_bank.toLowerCase().includes(searchTerm.toLowerCase()))
      )
      setFilteredConsents(filtered)
    } else {
      setFilteredConsents(consents)
    }
  }, [searchTerm, consents])

  const handleApprove = async (requestId: string) => {
    if (!confirm('Одобрить запрос на согласие?')) {
      return
    }
    try {
      await bankerAPI.approveConsent(requestId)
      toast({
        title: 'Согласие одобрено',
        description: 'Запрос на согласие успешно одобрен',
      })
      fetchConsents()
    } catch (error: any) {
      toast({
        title: 'Ошибка',
        description: error.response?.data?.detail || 'Не удалось одобрить согласие',
        variant: 'destructive',
      })
    }
  }

  const handleReject = async (requestId: string) => {
    if (!confirm('Отклонить запрос на согласие?')) {
      return
    }
    try {
      await bankerAPI.rejectConsent(requestId)
      toast({
        title: 'Согласие отклонено',
        description: 'Запрос на согласие успешно отклонен',
      })
      fetchConsents()
    } catch (error: any) {
      toast({
        title: 'Ошибка',
        description: error.response?.data?.detail || 'Не удалось отклонить согласие',
        variant: 'destructive',
      })
    }
  }

  const stats = {
    total: consents.length,
    authorized: consents.filter((c) => c.status === 'approved' || c.status === 'AUTHORIZED').length,
    pending: consents.filter((c) => c.status === 'pending' || c.status === 'PENDING').length,
    rejected: consents.filter((c) => c.status === 'rejected' || c.status === 'REJECTED').length,
    revoked: consents.filter((c) => c.status === 'revoked' || c.status === 'REVOKED').length,
  }

  return (
    <BankerLayout title="Управление согласиями">
      <div className="grid gap-6 md:grid-cols-4 mb-6">
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Всего</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.total}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Одобрено</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">{stats.authorized}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Ожидают</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-yellow-600">{stats.pending}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Отклонено</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-red-600">{stats.rejected + stats.revoked}</div>
          </CardContent>
        </Card>
      </div>

      <div className="mb-4">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Поиск по ID согласия или клиента..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="pl-10"
          />
        </div>
      </div>

      {loading ? (
        <p className="text-muted-foreground">Загрузка...</p>
      ) : filteredConsents.length === 0 ? (
        <Card>
          <CardContent className="pt-6">
            <p className="text-center text-muted-foreground">
              {searchTerm ? 'Ничего не найдено' : 'Нет запросов на согласия'}
            </p>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-4">
          {filteredConsents.map((consent) => (
            <Card key={consent.request_id}>
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-3">
                    <FileText className="h-8 w-8 text-primary" />
                    <div>
                      <CardTitle className="text-lg">{consent.client_name}</CardTitle>
                      <CardDescription className="font-mono text-xs">
                        {consent.request_id.substring(0, 12)}...
                      </CardDescription>
                    </div>
                  </div>
                  <span
                    className={`px-3 py-1 text-sm rounded ${
                      consent.status === 'approved' || consent.status === 'AUTHORIZED'
                        ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
                        : consent.status === 'pending' || consent.status === 'PENDING'
                        ? 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200'
                        : consent.status === 'rejected' || consent.status === 'REJECTED'
                        ? 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200'
                        : 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-200'
                    }`}
                  >
                    {consent.status}
                  </span>
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <p className="text-muted-foreground">Клиент:</p>
                      <p className="font-medium">{consent.client_id}</p>
                    </div>
                    <div>
                      <p className="text-muted-foreground">Запрашивающий банк:</p>
                      <p className="font-medium">{consent.requesting_bank || '—'}</p>
                    </div>
                    <div>
                      <p className="text-muted-foreground">Создано:</p>
                      <p className="font-medium">
                        {format(new Date(consent.created_at), 'dd MMM yyyy HH:mm', { locale: ru })}
                      </p>
                    </div>
                    {consent.responded_at && (
                      <div>
                        <p className="text-muted-foreground">Обработано:</p>
                        <p className="font-medium">
                          {format(new Date(consent.responded_at), 'dd MMM yyyy HH:mm', { locale: ru })}
                        </p>
                      </div>
                    )}
                  </div>

                  <div>
                    <p className="text-sm font-medium mb-2">Разрешения:</p>
                    <div className="flex flex-wrap gap-2">
                      {consent.permissions.map((perm, idx) => (
                        <span
                          key={idx}
                          className="px-2 py-1 text-xs bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200 rounded"
                        >
                          {perm}
                        </span>
                      ))}
                    </div>
                  </div>

                  {consent.reason && (
                    <div>
                      <p className="text-sm font-medium mb-1">Причина:</p>
                      <p className="text-sm text-muted-foreground">{consent.reason}</p>
                    </div>
                  )}

                  {(consent.status === 'pending' || consent.status === 'PENDING') && (
                    <div className="flex gap-2">
                      <Button
                        variant="default"
                        size="sm"
                        onClick={() => handleApprove(consent.request_id)}
                        className="flex-1"
                      >
                        <CheckCircle className="mr-2 h-4 w-4" />
                        Одобрить
                      </Button>
                      <Button
                        variant="destructive"
                        size="sm"
                        onClick={() => handleReject(consent.request_id)}
                        className="flex-1"
                      >
                        <XCircle className="mr-2 h-4 w-4" />
                        Отклонить
                      </Button>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </BankerLayout>
  )
}

