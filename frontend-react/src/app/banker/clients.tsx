import { useEffect, useState } from 'react'
import { BankerLayout } from '@/components/layouts/banker-layout'
import { Card, CardContent } from '@/components/ui/card'
import { bankerAPI } from '@/lib/api'
import { useToast } from '@/hooks/use-toast'
import type { Client } from '@/types/api'
import { format } from 'date-fns'
import { ru } from 'date-fns/locale'

export default function BankerClients() {
  const [clients, setClients] = useState<Client[]>([])
  const [loading, setLoading] = useState(true)
  const { toast } = useToast()

  useEffect(() => {
    const fetchClients = async () => {
      try {
        const data = await bankerAPI.getClients()
        // Убеждаемся что data это массив
        const clientsArray = Array.isArray(data) ? data : []
        setClients(clientsArray)
      } catch (error: any) {
        toast({
          title: 'Ошибка загрузки',
          description: error.response?.data?.detail || 'Не удалось загрузить клиентов',
          variant: 'destructive',
        })
      } finally {
        setLoading(false)
      }
    }

    fetchClients()
  }, [toast])

  return (
    <BankerLayout title="Клиенты">
      {loading ? (
        <p className="text-muted-foreground">Загрузка...</p>
      ) : clients.length === 0 ? (
        <Card>
          <CardContent className="pt-6">
            <p className="text-center text-muted-foreground">Нет клиентов</p>
          </CardContent>
        </Card>
      ) : (
        <div className="overflow-x-auto -mx-4 sm:mx-0">
          <div className="inline-block min-w-full align-middle px-4 sm:px-0">
            <table className="w-full">
            <thead className="bg-gray-50 dark:bg-gray-800">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Person ID
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  ФИО
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Контакты
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Дата регистрации
                </th>
              </tr>
            </thead>
            <tbody className="bg-white dark:bg-gray-900 divide-y divide-gray-200 dark:divide-gray-800">
              {clients.map((client) => (
                <tr key={client.client_id}>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                    {client.person_id}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm">
                    {client.last_name} {client.first_name} {client.patronymic}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm">
                    <div>{client.phone}</div>
                    <div className="text-gray-500">{client.email}</div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {format(new Date(client.registration_date), 'dd MMM yyyy', { locale: ru })}
                  </td>
                </tr>
              ))}
            </tbody>
            </table>
          </div>
        </div>
      )}
    </BankerLayout>
  )
}

