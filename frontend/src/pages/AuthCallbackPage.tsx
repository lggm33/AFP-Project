import { useEffect, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'

const AuthCallbackPage = () => {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const [status, setStatus] = useState<'loading' | 'success' | 'error'>('loading')

  useEffect(() => {
    const handleCallback = async () => {
      try {
        // Get parameters from the URL
        const error = searchParams.get('error')
        const accessToken = searchParams.get('access_token')
        const refreshToken = searchParams.get('refresh_token')
        const userId = searchParams.get('user_id')
        const email = searchParams.get('email')
        const username = searchParams.get('username')
        const providers = searchParams.get('providers')
        
        if (error) {
          console.error('OAuth error:', error)
          const message = searchParams.get('message')
          console.error('Error message:', message)
          setStatus('error')
          return
        }

        // Check if we have tokens from Django redirect
        if (accessToken && refreshToken && userId) {
          console.log('🎉 OAuth successful! Tokens received from Django')
          
          // Create user object
          const userData = {
            id: parseInt(userId),
            username: username || '',
            email: email || '',
            first_name: '',
            last_name: '',
          }
          
          // Create social accounts array
          const socialAccounts = providers ? providers.split(',').map(provider => ({
            provider: provider,
            uid: '',
            email: email,
          })) : []
          
          // Store tokens and user info in localStorage
          localStorage.setItem('afp_access_token', accessToken)
          localStorage.setItem('afp_user', JSON.stringify(userData))
          localStorage.setItem('afp_social_accounts', JSON.stringify(socialAccounts))
          
          console.log('✅ Tokens and user data stored successfully')
          
          setStatus('success')
          setTimeout(() => {
            navigate('/app/dashboard')
          }, 2000)
        } else {
          console.error('❌ Missing required tokens or user data in callback')
          setStatus('error')
        }
      } catch (error) {
        console.error('Callback handling error:', error)
        setStatus('error')
      }
    }

    handleCallback()
  }, [searchParams, navigate])

  if (status === 'loading') {
    return (
      <div className="min-h-screen bg-gray-50 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
        <div className="sm:mx-auto sm:w-full sm:max-w-md">
          <div className="bg-white py-8 px-4 shadow sm:rounded-lg sm:px-10">
            <div className="text-center">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto"></div>
              <h2 className="mt-4 text-lg font-medium text-gray-900">
                Completando autenticación...
              </h2>
              <p className="mt-2 text-sm text-gray-600">
                Estamos procesando tu información de acceso.
              </p>
            </div>
          </div>
        </div>
      </div>
    )
  }

  if (status === 'success') {
    return (
      <div className="min-h-screen bg-gray-50 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
        <div className="sm:mx-auto sm:w-full sm:max-w-md">
          <div className="bg-white py-8 px-4 shadow sm:rounded-lg sm:px-10">
            <div className="text-center">
              <div className="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-green-100">
                <svg className="h-6 w-6 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
              </div>
              <h2 className="mt-4 text-lg font-medium text-gray-900">
                ¡Autenticación exitosa!
              </h2>
              <p className="mt-2 text-sm text-gray-600">
                Redirigiendo al dashboard...
              </p>
            </div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
      <div className="sm:mx-auto sm:w-full sm:max-w-md">
        <div className="bg-white py-8 px-4 shadow sm:rounded-lg sm:px-10">
          <div className="text-center">
            <div className="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-red-100">
              <svg className="h-6 w-6 text-red-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </div>
            <h2 className="mt-4 text-lg font-medium text-gray-900">
              Error de autenticación
            </h2>
            <p className="mt-2 text-sm text-gray-600">
              Hubo un problema al completar la autenticación.
            </p>
            <button
              onClick={() => navigate('/login')}
              className="mt-4 w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
            >
              Intentar de nuevo
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

export default AuthCallbackPage 