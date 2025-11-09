import { useEffect } from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { ProtectedRoute } from './components/protected-route'
import { Toaster } from './components/ui/toaster'
import { useAppStore } from './stores/app-store'
import { bankAPI } from './lib/api'
import ClientLogin from './app/client/login'
import ClientDashboard from './app/client/dashboard'
import ClientAccounts from './app/client/accounts'
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
        
        {/* Banker routes */}
        <Route path="/app/banker/login" element={<BankerLogin />} />
        <Route 
          path="/app/banker/dashboard" 
          element={
            <ProtectedRoute redirectTo="/app/banker/login">
              <BankerDashboard />
            </ProtectedRoute>
          } 
        />
        <Route 
          path="/app/banker/clients" 
          element={
            <ProtectedRoute redirectTo="/app/banker/login">
              <BankerClients />
            </ProtectedRoute>
          } 
        />
        <Route 
          path="/app/banker/products" 
          element={
            <ProtectedRoute redirectTo="/app/banker/login">
              <BankerProducts />
            </ProtectedRoute>
          } 
        />
        <Route 
          path="/app/banker/monitoring" 
          element={
            <ProtectedRoute redirectTo="/app/banker/login">
              <BankerMonitoring />
            </ProtectedRoute>
          } 
        />
        <Route 
          path="/app/banker/consents" 
          element={
            <ProtectedRoute redirectTo="/app/banker/login">
              <BankerConsents />
            </ProtectedRoute>
          } 
        />
        <Route 
          path="/app/banker/teams" 
          element={
            <ProtectedRoute redirectTo="/app/banker/login">
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

