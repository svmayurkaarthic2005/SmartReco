/**
 * Protected route wrapper
 * Redirects to login if not authenticated
 */

import { Navigate, Outlet } from 'react-router-dom'
import { useAuthStore } from '../../store/authStore'
import { TimeOnPageTracker } from '../../tracker/TimeOnPageTracker'

export const ProtectedRoute = () => {
  const { isAuthenticated, isLoading } = useAuthStore()

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    )
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }

  return (
    <>
      <TimeOnPageTracker />
      <Outlet />
    </>
  )
}

export const AdminRoute = () => {
  const { isAuthenticated, isLoading, user } = useAuthStore()

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    )
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }

  if (user?.role !== 'admin') {
    return <Navigate to="/dashboard" replace />
  }

  return <Outlet />
}
