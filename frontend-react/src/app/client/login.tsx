import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { useToast } from '@/hooks/use-toast'
import { useAuthStore } from '@/stores/auth-store'
import { authAPI } from '@/lib/api'
import { LogIn, Dice6 } from 'lucide-react'

const TEST_CLIENTS = [
  'team025-1', 'team025-2', 'team025-3', 'team025-4', 'team025-5',
  'team025-6', 'team025-7', 'team025-8', 'team025-9', 'team025-10',
  'demo-client-001', 'demo-client-002', 'demo-client-003'
]

export default function ClientLogin() {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()
  const { toast } = useToast()
  const setAuth = useAuthStore((state) => state.setAuth)

  const performLogin = async (loginUsername: string, loginPassword: string) => {
    setLoading(true)

    try {
      const response = await authAPI.login({ username: loginUsername, password: loginPassword })
      setAuth(response.access_token, response.client_id)
      toast({
        title: 'Успешный вход',
        description: 'Добро пожаловать в систему!',
      })
      navigate('/app/client/dashboard')
    } catch (error: any) {
      toast({
        title: 'Ошибка входа',
        description: error.response?.data?.detail || 'Неверные учетные данные',
        variant: 'destructive',
      })
    } finally {
      setLoading(false)
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    await performLogin(username, password)
  }

  const handleRandomLogin = async () => {
    const randomClient = TEST_CLIENTS[Math.floor(Math.random() * TEST_CLIENTS.length)]
    setUsername(randomClient)
    setPassword('password')
    // Вызываем логин напрямую с выбранными данными
    await performLogin(randomClient, 'password')
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-[#667eea] to-[#764ba2] p-4">
      <Card className="w-full max-w-md">
        <CardHeader className="space-y-1">
          <CardTitle className="text-2xl text-center">Вход в систему</CardTitle>
          <CardDescription className="text-center">
            Введите ваши учетные данные для входа
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="username">Логин (Person ID)</Label>
              <Input
                id="username"
                type="text"
                placeholder="cli-vb-001 или demo-client-001"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                required
                disabled={loading}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="password">Пароль</Label>
              <Input
                id="password"
                type="password"
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                disabled={loading}
              />
            </div>
            <Button type="submit" className="w-full" disabled={loading}>
              {loading ? (
                'Вход...'
              ) : (
                <>
                  <LogIn className="mr-2 h-4 w-4" />
                  Войти
                </>
              )}
            </Button>
            <Button
              type="button"
              variant="outline"
              className="w-full mt-2"
              disabled={loading}
              onClick={handleRandomLogin}
            >
              <Dice6 className="mr-2 h-4 w-4" />
              Войти как случайный клиент
            </Button>
          </form>
          <div className="mt-4 text-center text-sm text-gray-600 dark:text-gray-400">
            <p className="mb-2">Тестовый аккаунт: demo-client-001 / password</p>
            <p className="text-xs">
              Команда team025: team025-1 до team025-10<br />
              Demo клиенты: demo-client-001, demo-client-002, demo-client-003<br />
              Пароль для всех: password
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

