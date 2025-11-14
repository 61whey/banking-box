import { useNavigate } from 'react-router-dom'
import { Button } from '@/components/ui/button'
import { useAuthStore } from '@/stores/auth-store'
import { useAppStore } from '@/stores/app-store'
import { LogOut, Moon, Sun, Home, CreditCard, FileText, Send } from 'lucide-react'

interface ClientLayoutProps {
  children: React.ReactNode
  title?: string
}

export function ClientLayout({ children, title }: ClientLayoutProps) {
  const navigate = useNavigate()
  const clearAuth = useAuthStore((state) => state.clearAuth)
  const { theme, toggleTheme, bankName } = useAppStore()

  const handleLogout = () => {
    clearAuth()
    navigate('/app/client/login')
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <header className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center">
              <h1 className="text-xl font-bold text-primary">{bankName}</h1>
            </div>
            <div className="flex items-center gap-2">
              <Button
                variant="ghost"
                size="icon"
                onClick={toggleTheme}
              >
                {theme === 'light' ? <Moon className="h-5 w-5" /> : <Sun className="h-5 w-5" />}
              </Button>
              <Button variant="ghost" onClick={handleLogout}>
                <LogOut className="mr-2 h-4 w-4" />
                Выход
              </Button>
            </div>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 w-full">
        <nav className="flex gap-4 mb-6">
          <Button
            variant="ghost"
            onClick={() => navigate('/app/client/dashboard')}
          >
            <Home className="mr-2 h-4 w-4" />
            Главная
          </Button>
          <Button
            variant="ghost"
            onClick={() => navigate('/app/client/accounts')}
          >
            <CreditCard className="mr-2 h-4 w-4" />
            Счета
          </Button>
          <Button
            variant="ghost"
            onClick={() => navigate('/app/client/consents')}
          >
            <FileText className="mr-2 h-4 w-4" />
            Согласия
          </Button>
          <Button
            variant="ghost"
            onClick={() => navigate('/app/client/transfers')}
          >
            <Send className="mr-2 h-4 w-4" />
            Переводы
          </Button>
        </nav>

        {title && (
          <h2 className="text-3xl font-bold mb-6 text-gray-900 dark:text-gray-100">
            {title}
          </h2>
        )}

        {children}
      </div>
    </div>
  )
}

