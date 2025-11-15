import { useNavigate } from 'react-router-dom'
import { Button } from '@/components/ui/button'
import { useAuthStore } from '@/stores/auth-store'
import { useAppStore } from '@/stores/app-store'
import { LogOut, Moon, Sun, LayoutDashboard, Users, Package, Activity, Building2, UserCheck, Shield } from 'lucide-react'

interface BankerLayoutProps {
  children: React.ReactNode
  title?: string
}

export function BankerLayout({ children, title }: BankerLayoutProps) {
  const navigate = useNavigate()
  const clearAuth = useAuthStore((state) => state.clearAuth)
  const { theme, toggleTheme, bankName } = useAppStore()

  const handleLogout = () => {
    clearAuth()
    navigate('/app/admin/login')
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <header className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center gap-2">
              <Building2 className="h-6 w-6 text-primary" />
              <h1 className="text-xl font-bold text-primary">{bankName} Admin</h1>
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
            onClick={() => navigate('/app/admin/dashboard')}
          >
            <LayoutDashboard className="mr-2 h-4 w-4" />
            Панель
          </Button>
          <Button
            variant="ghost"
            onClick={() => navigate('/app/admin/clients')}
          >
            <Users className="mr-2 h-4 w-4" />
            Клиенты
          </Button>
          <Button
            variant="ghost"
            onClick={() => navigate('/app/admin/products')}
          >
            <Package className="mr-2 h-4 w-4" />
            Продукты
          </Button>
          <Button
            variant="ghost"
            onClick={() => navigate('/app/admin/monitoring')}
          >
            <Activity className="mr-2 h-4 w-4" />
            Мониторинг
          </Button>
          <Button
            variant="ghost"
            onClick={() => navigate('/app/admin/consents')}
          >
            <Shield className="mr-2 h-4 w-4" />
            Согласия
          </Button>
          <Button
            variant="ghost"
            onClick={() => navigate('/app/admin/teams')}
          >
            <UserCheck className="mr-2 h-4 w-4" />
            Команды
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

