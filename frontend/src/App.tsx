import { useEffect, useState } from 'react'
import { Routes, Route, Navigate, useLocation } from 'react-router-dom'
import { authStore } from '@/store/auth'

import { LoginPage } from '@/pages/LoginPage'
import { RegisterPage } from '@/pages/RegisterPage'
import { DashboardPage } from '@/pages/DashboardPage'
import { ProjectsPage } from '@/pages/ProjectsPage'
import { ProjectDetailPage } from '@/pages/ProjectDetailPage'

function PrivateRoute({ children }: { children: JSX.Element }) {
  const isAuth = authStore.isAuthenticated()
  const location = useLocation()

  if (!isAuth) {
    return <Navigate to="/login" state={{ from: location }} replace />
  }

  return children
}

function App() {
  const [isReady, setIsReady] = useState(false)
  const [, setTick] = useState(0)

  useEffect(() => {
    // Initialiser l'état d'authentification
    authStore.loadUser().finally(() => setIsReady(true))

    const unsubscribe = authStore.subscribe(() => {
      // Forcer un re-render quand l'état d'auth change (ex: logout)
      setTick(t => t + 1)
    })

    return unsubscribe
  }, [])

  if (!isReady) return null // Éviter les flashs de redirection

  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />
      
      {/* Protected Routes */}
      <Route path="/dashboard" element={<PrivateRoute><DashboardPage /></PrivateRoute>} />
      <Route path="/projects" element={<PrivateRoute><ProjectsPage /></PrivateRoute>} />
      <Route path="/projects/new" element={<PrivateRoute><ProjectsPage /></PrivateRoute>} />
      <Route path="/projects/:id" element={<PrivateRoute><ProjectDetailPage /></PrivateRoute>} />

      {/* Default Redirect */}
      <Route path="/" element={<Navigate to="/dashboard" replace />} />
      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  )
}

export default App
