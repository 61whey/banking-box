import { useEffect, useState } from 'react'
import { ClientLayout } from '@/components/layouts/client-layout'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { consentsAPI } from '@/lib/api'
import { useToast } from '@/hooks/use-toast'
import type { Consent } from '@/types/api'
import { FileText, Trash2 } from 'lucide-react'
import { format } from 'date-fns'
import { ru } from 'date-fns/locale'

export default function ClientConsents() {
  const [consents, setConsents] = useState<Consent[]>([])
  const [loading, setLoading] = useState(true)
  const { toast } = useToast()

  const fetchConsents = async () => {
    try {
      const data = await consentsAPI.getConsents()
      // Убеждаемся что data это массив
      const consentsArray = Array.isArray(data) ? data : []
      setConsents(consentsArray)
    } catch (error: any) {
      toast({
        title: 'Ошибка загрузки',
        description: error.response?.data?.detail || 'Не удалось загрузить согласия',
        variant: 'destructive',
      })
      // Устанавливаем пустой массив в случае ошибки
      setConsents([])
    } finally {
      setLoading(false)
    }
  }

  const handleDeleteConsent = async (consentId: string) => {
    try {
      await consentsAPI.deleteConsent(consentId)
      toast({
        title: 'Согласие отозвано',
        description: 'Доступ к данным был успешно отозван',
      })
      fetchConsents()
    } catch (error: any) {
      toast({
        title: 'Ошибка',
        description: error.response?.data?.detail || 'Не удалось отозвать согласие',
        variant: 'destructive',
      })
    }
  }

  useEffect(() => {
    fetchConsents()
  }, [])

  return (
    <ClientLayout title="Мои согласия">
      {loading ? (
        <p className="text-muted-foreground">Загрузка...</p>
      ) : consents.length === 0 ? (
        <Card>
          <CardContent className="pt-6">
            <p className="text-center text-muted-foreground">У вас нет активных согласий</p>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-6">
          {consents.map((consent) => (
            <Card key={consent.consent_id}>
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-3">
                    <FileText className="h-8 w-8 text-primary" />
                    <div>
                      <CardTitle>{consent.team_name || 'Внешнее приложение'}</CardTitle>
                      <CardDescription>ID: {consent.consent_id}</CardDescription>
                    </div>
                  </div>
                  <span className={`px-3 py-1 text-sm rounded ${
                    consent.status === 'Authorised' 
                      ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200' 
                      : consent.status === 'Revoked'
                      ? 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200'
                      : 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-200'
                  }`}>
                    {consent.status}
                  </span>
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div>
                    <h4 className="text-sm font-medium mb-2">Разрешения:</h4>
                    <div className="flex flex-wrap gap-2">
                      {consent.permissions.map((permission, index) => (
                        <span
                          key={index}
                          className="px-2 py-1 text-xs bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200 rounded"
                        >
                          {permission}
                        </span>
                      ))}
                    </div>
                  </div>
                  <div className="flex justify-between items-center text-sm">
                    <div>
                      <p className="text-muted-foreground">
                        Создано: {format(new Date(consent.created_at), 'dd MMM yyyy', { locale: ru })}
                      </p>
                      <p className="text-muted-foreground">
                        Истекает: {format(new Date(consent.expiration_date), 'dd MMM yyyy', { locale: ru })}
                      </p>
                    </div>
                    {consent.status === 'Authorised' && (
                      <Button
                        variant="destructive"
                        size="sm"
                        onClick={() => handleDeleteConsent(consent.consent_id)}
                      >
                        <Trash2 className="mr-2 h-4 w-4" />
                        Отозвать
                      </Button>
                    )}
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

