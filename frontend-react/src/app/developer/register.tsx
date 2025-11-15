import { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { useToast } from '@/hooks/use-toast'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Copy, ExternalLink } from 'lucide-react'
import { authAPI } from '@/lib/api'

interface RegisterTeamRequest {
  team_name: string
  client_id: string
  email?: string
  telegram?: string
  contact_person?: string
}

export default function DeveloperRegister() {
  const [formData, setFormData] = useState<RegisterTeamRequest>({
    team_name: '',
    client_id: '',
    email: '',
    telegram: '',
    contact_person: '',
  })
  const [loading, setLoading] = useState(false)
  const [showSuccess, setShowSuccess] = useState(false)
  const [credentials, setCredentials] = useState<{
    client_id: string
    client_secret: string
    test_clients: string[]
  } | null>(null)
  const { toast } = useToast()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)

    try {
      const data: RegisterTeamRequest = {
        team_name: formData.team_name,
        client_id: formData.client_id,
      }

      if (formData.email?.trim()) data.email = formData.email.trim()
      if (formData.telegram?.trim()) data.telegram = formData.telegram.trim()
      if (formData.contact_person?.trim()) data.contact_person = formData.contact_person.trim()

      const response = await authAPI.registerTeam(data)
      // API возвращает credentials в формате { client_id, client_secret, team_name }
      setCredentials({
        client_id: response.credentials.client_id,
        client_secret: response.credentials.client_secret,
        test_clients: response.test_clients || [],
      })
      setShowSuccess(true)
      // Сброс формы
      setFormData({
        team_name: '',
        client_id: '',
        email: '',
        telegram: '',
        contact_person: '',
      })
    } catch (error: any) {
      toast({
        title: 'Ошибка регистрации',
        description: error.response?.data?.detail || 'Не удалось зарегистрировать команду',
        variant: 'destructive',
      })
    } finally {
      setLoading(false)
    }
  }

  const handleCopy = (text: string, label: string) => {
    navigator.clipboard.writeText(text)
    toast({
      title: 'Скопировано',
      description: `${label} скопирован в буфер обмена`,
    })
  }

  const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:54080'

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-[#667eea] to-[#764ba2] p-4">
      <div className="w-full max-w-2xl">
        <div className="text-center mb-8 text-white">
          <div className="text-6xl mb-4">🏦</div>
          <h1 className="text-4xl font-bold mb-2">Bank API</h1>
          <p className="text-lg opacity-90">Регистрация команды для доступа к API</p>
        </div>

        <Card>
          <CardHeader>
            <CardTitle className="text-2xl">Создайте свою команду</CardTitle>
            <CardDescription>
              Получите учетные данные для работы с API банка и начните разработку
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-6">
              <div className="space-y-2">
                <Label htmlFor="team_name">
                  Название команды <span className="text-red-500">*</span>
                </Label>
                <Input
                  id="team_name"
                  type="text"
                  placeholder="Например: Awesome Developers"
                  value={formData.team_name}
                  onChange={(e) => setFormData({ ...formData, team_name: e.target.value })}
                  required
                  disabled={loading}
                />
                <p className="text-sm text-muted-foreground">Как называется ваша команда или проект?</p>
              </div>

              <div className="space-y-2">
                <Label htmlFor="client_id">
                  Client ID <span className="text-red-500">*</span>
                </Label>
                <Input
                  id="client_id"
                  type="text"
                  placeholder="team201"
                  pattern="team[0-9]+"
                  maxLength={20}
                  value={formData.client_id}
                  onChange={(e) => setFormData({ ...formData, client_id: e.target.value })}
                  required
                  disabled={loading}
                />
                <p className="text-sm text-muted-foreground">
                  Уникальный идентификатор вашей команды. Формат: team + число (например, team201)
                </p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="email">
                    Email <span className="text-muted-foreground text-xs">(опционально)</span>
                  </Label>
                  <Input
                    id="email"
                    type="email"
                    placeholder="team@example.com"
                    value={formData.email}
                    onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                    disabled={loading}
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="telegram">
                    Telegram <span className="text-muted-foreground text-xs">(опционально)</span>
                  </Label>
                  <Input
                    id="telegram"
                    type="text"
                    placeholder="@username"
                    value={formData.telegram}
                    onChange={(e) => setFormData({ ...formData, telegram: e.target.value })}
                    disabled={loading}
                  />
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="contact_person">
                  Контактное лицо <span className="text-muted-foreground text-xs">(опционально)</span>
                </Label>
                <Input
                  id="contact_person"
                  type="text"
                  placeholder="Иван Иванов"
                  value={formData.contact_person}
                  onChange={(e) => setFormData({ ...formData, contact_person: e.target.value })}
                  disabled={loading}
                />
                <p className="text-sm text-muted-foreground">Имя человека, ответственного за команду</p>
              </div>

              <Button type="submit" className="w-full" size="lg" disabled={loading}>
                {loading ? '⏳ Регистрация...' : '🚀 Зарегистрировать команду'}
              </Button>
            </form>

            <div className="mt-6 text-center text-sm text-muted-foreground">
              <p>
                Нужна помощь?{' '}
                <a href={`${BASE_URL}/docs`} target="_blank" rel="noopener noreferrer" className="text-primary hover:underline">
                  Документация API
                </a>
              </p>
            </div>
          </CardContent>
        </Card>
      </div>

      <Dialog open={showSuccess} onOpenChange={setShowSuccess}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <div className="text-center mb-4">
              <div className="text-6xl mb-2">🎉</div>
              <DialogTitle className="text-3xl bg-gradient-to-r from-[#667eea] to-[#764ba2] bg-clip-text text-transparent">
                Команда успешно зарегистрирована!
              </DialogTitle>
            </div>
            <DialogDescription className="text-center">
              Сохраните учетные данные в безопасном месте
            </DialogDescription>
          </DialogHeader>

          {credentials && (
            <div className="space-y-4">
              <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-4 space-y-4">
                <div>
                  <Label className="text-xs uppercase tracking-wide text-muted-foreground mb-2 block">
                    Client ID
                  </Label>
                  <div className="flex gap-2">
                    <code className="flex-1 bg-white dark:bg-gray-900 border rounded-lg p-3 text-sm font-mono break-all">
                      {credentials.client_id}
                    </code>
                    <Button
                      variant="outline"
                      size="icon"
                      onClick={() => handleCopy(credentials.client_id, 'Client ID')}
                    >
                      <Copy className="h-4 w-4" />
                    </Button>
                  </div>
                </div>

                <div>
                  <Label className="text-xs uppercase tracking-wide text-muted-foreground mb-2 block">
                    Client Secret
                  </Label>
                  <div className="flex gap-2">
                    <code className="flex-1 bg-white dark:bg-gray-900 border rounded-lg p-3 text-sm font-mono break-all">
                      {credentials.client_secret}
                    </code>
                    <Button
                      variant="outline"
                      size="icon"
                      onClick={() => handleCopy(credentials.client_secret, 'Client Secret')}
                    >
                      <Copy className="h-4 w-4" />
                    </Button>
                  </div>
                </div>

                {credentials.test_clients.length > 0 && (
                  <div>
                    <Label className="text-xs uppercase tracking-wide text-muted-foreground mb-2 block">
                      Тестовые клиенты для UI
                    </Label>
                    <code className="block bg-white dark:bg-gray-900 border rounded-lg p-3 text-sm font-mono break-all">
                      {credentials.test_clients.slice(0, 3).join(', ')} ...{' '}
                      {credentials.test_clients[credentials.test_clients.length - 1]}
                    </code>
                  </div>
                )}

                <div>
                  <Label className="text-xs uppercase tracking-wide text-muted-foreground mb-2 block">
                    Пароль для UI
                  </Label>
                  <code className="block bg-white dark:bg-gray-900 border rounded-lg p-3 text-sm font-mono">
                    password
                  </code>
                </div>
              </div>

              <div className="bg-yellow-50 dark:bg-yellow-900/20 border-l-4 border-yellow-500 p-4 rounded">
                <p className="font-semibold text-yellow-800 dark:text-yellow-200 mb-1">⚠️ Важно!</p>
                <p className="text-sm text-yellow-700 dark:text-yellow-300">
                  Client Secret показывается только один раз. Обязательно сохраните его в безопасном месте. Без него вы не
                  сможете делать межбанковские запросы.
                </p>
              </div>

              <div className="bg-blue-50 dark:bg-blue-900/20 border-l-4 border-blue-500 p-4 rounded">
                <p className="font-semibold text-blue-800 dark:text-blue-200 mb-2">📋 Следующие шаги:</p>
                <p className="text-sm text-blue-700 dark:text-blue-300 mb-4">
                  Сохраните Client ID и Client Secret в надежном месте
                </p>
                <div className="flex gap-2 flex-wrap">
                  <Button
                    variant="outline"
                    className="flex-1 min-w-[200px]"
                    onClick={() => window.open('/app/client/login', '_blank')}
                  >
                    <ExternalLink className="mr-2 h-4 w-4" />
                    Открыть UI банка
                  </Button>
                  <Button
                    variant="outline"
                    className="flex-1 min-w-[200px]"
                    onClick={() => window.open(`${BASE_URL}/docs`, '_blank')}
                  >
                    <ExternalLink className="mr-2 h-4 w-4" />
                    Документация API
                  </Button>
                </div>
              </div>

              <Button className="w-full" onClick={() => setShowSuccess(false)}>
                Понятно, начинаем!
              </Button>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  )
}

