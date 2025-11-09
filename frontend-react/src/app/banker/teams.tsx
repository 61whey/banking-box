import { useEffect, useState } from 'react'
import { BankerLayout } from '@/components/layouts/banker-layout'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { adminAPI } from '@/lib/api'
import { useToast } from '@/hooks/use-toast'
import { Users, Ban, CheckCircle, Copy, ExternalLink } from 'lucide-react'
import { format } from 'date-fns'
import { ru } from 'date-fns/locale'

interface Team {
  client_id: string
  client_secret: string
  team_name: string
  is_active: boolean
  created_at: string
}

export default function BankerTeams() {
  const [teams, setTeams] = useState<Team[]>([])
  const [loading, setLoading] = useState(true)
  const { toast } = useToast()

  const fetchTeams = async () => {
    try {
      const data = await adminAPI.getTeams()
      const teamsArray = Array.isArray(data) ? data : []
      setTeams(teamsArray)
    } catch (error: any) {
      toast({
        title: 'Ошибка загрузки',
        description: error.response?.data?.detail || 'Не удалось загрузить команды',
        variant: 'destructive',
      })
      setTeams([])
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchTeams()
  }, [])

  const handleSuspend = async (clientId: string) => {
    if (!confirm(`Приостановить команду ${clientId}? Они не смогут делать запросы к API.`)) {
      return
    }
    try {
      await adminAPI.suspendTeam(clientId)
      toast({
        title: 'Команда приостановлена',
        description: `Команда ${clientId} успешно приостановлена`,
      })
      fetchTeams()
    } catch (error: any) {
      toast({
        title: 'Ошибка',
        description: error.response?.data?.detail || 'Не удалось приостановить команду',
        variant: 'destructive',
      })
    }
  }

  const handleActivate = async (clientId: string) => {
    try {
      await adminAPI.activateTeam(clientId)
      toast({
        title: 'Команда активирована',
        description: `Команда ${clientId} успешно активирована`,
      })
      fetchTeams()
    } catch (error: any) {
      toast({
        title: 'Ошибка',
        description: error.response?.data?.detail || 'Не удалось активировать команду',
        variant: 'destructive',
      })
    }
  }

  const handleCopy = (text: string, label: string) => {
    navigator.clipboard.writeText(text)
    toast({
      title: 'Скопировано',
      description: `${label} скопирован в буфер обмена`,
    })
  }

  return (
    <BankerLayout title="Команды участников">
      <div className="mb-4">
        <Button
          variant="outline"
          onClick={() => window.open('/app/developer/register', '_blank')}
          className="inline-flex items-center gap-2"
        >
          <ExternalLink className="h-4 w-4" />
          Страница регистрации команд
        </Button>
      </div>

      {loading ? (
        <p className="text-muted-foreground">Загрузка...</p>
      ) : teams.length === 0 ? (
        <Card>
          <CardContent className="pt-6">
            <p className="text-center text-muted-foreground">Нет зарегистрированных команд</p>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {teams.map((team) => (
            <Card key={team.client_id}>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <Users className="h-8 w-8 text-primary" />
                    <div>
                      <CardTitle className="text-lg">{team.team_name || team.client_id}</CardTitle>
                      <CardDescription className="font-mono text-xs">{team.client_id}</CardDescription>
                    </div>
                  </div>
                  <span
                    className={`px-2 py-1 text-xs rounded ${
                      team.is_active
                        ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
                        : 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200'
                    }`}
                  >
                    {team.is_active ? 'Активна' : 'Приостановлена'}
                  </span>
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div>
                    <p className="text-xs text-muted-foreground mb-1">Client Secret:</p>
                    <div className="flex items-center gap-2">
                      <code className="flex-1 text-xs bg-gray-100 dark:bg-gray-800 p-2 rounded break-all">
                        {team.client_secret}
                      </code>
                      <Button
                        variant="ghost"
                        size="icon"
                        className="h-8 w-8"
                        onClick={() => handleCopy(team.client_secret, 'Client Secret')}
                      >
                        <Copy className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>

                  {team.created_at && (
                    <p className="text-xs text-muted-foreground">
                      Создано: {format(new Date(team.created_at), 'dd MMM yyyy', { locale: ru })}
                    </p>
                  )}

                  <div className="flex gap-2">
                    {team.is_active ? (
                      <Button
                        variant="destructive"
                        size="sm"
                        onClick={() => handleSuspend(team.client_id)}
                        className="flex-1"
                      >
                        <Ban className="mr-2 h-4 w-4" />
                        Приостановить
                      </Button>
                    ) : (
                      <Button
                        variant="default"
                        size="sm"
                        onClick={() => handleActivate(team.client_id)}
                        className="flex-1"
                      >
                        <CheckCircle className="mr-2 h-4 w-4" />
                        Активировать
                      </Button>
                    )}
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </BankerLayout>
  )
}

