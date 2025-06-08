import { Navigate, Outlet } from 'react-router-dom'
import { useEffect, useState } from 'react'

const ProtectedRoute = () => {
  const [authState, setAuthState] = useState<'loading' | 'authenticated' | 'unauthenticated'>('loading')

  useEffect(() => {
    const checkAuthentication = async () => {
      try {
        // Check if we have a valid access token
        const accessToken = localStorage.getItem('afp_access_token')
        const userString = localStorage.getItem('afp_user')
        
        if (!accessToken || !userString) {
          setAuthState('unauthenticated')
          return
        }

        // Verify token is still valid by making a test API call
        const response = await fetch('http://127.0.0.1:8000/api/users/me/', {
          method: 'GET',
          headers: {
            'Authorization': `Bearer ${accessToken}`,
            'Content-Type': 'application/json',
          },
        })

        if (response.ok) {
          setAuthState('authenticated')
        } else {
          // Token is invalid, clear stored data
          localStorage.removeItem('afp_access_token')
          localStorage.removeItem('afp_user')
          localStorage.removeItem('afp_social_accounts')
          setAuthState('unauthenticated')
        }
      } catch (error) {
        console.error('Authentication check failed:', error)
        setAuthState('unauthenticated')
      }
    }

    checkAuthentication()
  }, [])

  if (authState === 'loading') {
    return (
      <div className="min-h-screen bg-gray-50 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
        <div className="sm:mx-auto sm:w-full sm:max-w-md">
          <div className="bg-white py-8 px-4 shadow sm:rounded-lg sm:px-10">
            <div className="text-center">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto"></div>
              <h2 className="mt-4 text-lg font-medium text-gray-900">
                Verificando autenticación...
              </h2>
            </div>
          </div>
        </div>
      </div>
    )
  }

  if (authState === 'unauthenticated') {
    return <Navigate to="/login" replace />
  }

  return <Outlet />
}

export default ProtectedRoute 