import { Navigate, Outlet } from 'react-router-dom'

const ProtectedRoute = () => {
  // TODO: Implement actual authentication check
  // For now, always redirect to login for testing purposes
  const isAuthenticated = false // This will be replaced with actual auth state

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }

  return <Outlet />
}

export default ProtectedRoute 