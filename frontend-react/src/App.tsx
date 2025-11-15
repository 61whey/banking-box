import { useEffect } from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { ProtectedRoute } from './components/protected-route'
import { Toaster } from './components/ui/toaster'
import { useAppStore } from './stores/app-store'
import { bankAPI } from './lib/api'
import ClientLogin from './app/client/login'
import ClientDashboard from './app/client/dashboard'
import ClientAccounts from './app/client/accounts'
import ClientVirtualAccounts from './app/client/virtual-accounts'
import ClientConsents from './app/client/consents'
import ClientTransfers from './app/client/transfers'
import BankerLogin from './app/banker/login'
import BankerDashboard from './app/banker/dashboard'
import BankerClients from './app/banker/clients'
import BankerProducts from './app/banker/products'
import BankerMonitoring from './app/banker/monitoring'
import BankerConsents from './app/banker/consents'
import BankerTeams from './app/banker/teams'
import DeveloperRegister from './app/developer/register'

function App() {
  const setBankName = useAppStore((state) => state.setBankName)

  useEffect(() => {
    // Загружаем название банка при инициализации приложения
    bankAPI
      .getBankInfo()
      .then((info) => {
        setBankName(info.bank)
      })
      .catch((error) => {
        console.warn('Failed to load bank info:', error)
        // Оставляем значение по умолчанию
      })
  }, [setBankName])

  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Navigate to="/app/client/login" replace />} />
        
        {/* Client routes */}
        <Route path="/app/client/login" element={<ClientLogin />} />
        <Route 
          path="/app/client/dashboard" 
          element={
            <ProtectedRoute>
              <ClientDashboard />
            </ProtectedRoute>
          } 
        />
        <Route
          path="/app/client/accounts"
          element={
            <ProtectedRoute>
              <ClientAccounts />
            </ProtectedRoute>
          }
        />
        <Route
          path="/app/client/virtual-accounts"
          element={
            <ProtectedRoute>
              <ClientVirtualAccounts />
            </ProtectedRoute>
          }
        />
        <Route
          path="/app/client/consents"
          element={
            <ProtectedRoute>
              <ClientConsents />
            </ProtectedRoute>
          }
        />
        <Route 
          path="/app/client/transfers" 
          element={
            <ProtectedRoute>
              <ClientTransfers />
            </ProtectedRoute>
          } 
        />
        
        {/* Admin routes */}
        <Route path="/app/admin/login" element={<BankerLogin />} />
        <Route 
          path="/app/admin/dashboard" 
          element={
            <ProtectedRoute redirectTo="/app/admin/login">
              <BankerDashboard />
            </ProtectedRoute>
          } 
        />
        <Route 
          path="/app/admin/clients" 
          element={
            <ProtectedRoute redirectTo="/app/admin/login">
              <BankerClients />
            </ProtectedRoute>
          } 
        />
        <Route 
          path="/app/admin/products" 
          element={
            <ProtectedRoute redirectTo="/app/admin/login">
              <BankerProducts />
            </ProtectedRoute>
          } 
        />
        <Route 
          path="/app/admin/monitoring" 
          element={
            <ProtectedRoute redirectTo="/app/admin/login">
              <BankerMonitoring />
            </ProtectedRoute>
          } 
        />
        <Route 
          path="/app/admin/consents" 
          element={
            <ProtectedRoute redirectTo="/app/admin/login">
              <BankerConsents />
            </ProtectedRoute>
          } 
        />
        <Route 
          path="/app/admin/teams" 
          element={
            <ProtectedRoute redirectTo="/app/admin/login">
              <BankerTeams />
            </ProtectedRoute>
          } 
        />
        
        {/* Developer routes */}
        <Route path="/developer.html" element={<DeveloperRegister />} />
        <Route path="/app/developer/register" element={<DeveloperRegister />} />
        
        {/* Fallback */}
        <Route path="*" element={<Navigate to="/app/client/login" replace />} />
      </Routes>
      <Toaster />
    </BrowserRouter>
  )
}

export default App

