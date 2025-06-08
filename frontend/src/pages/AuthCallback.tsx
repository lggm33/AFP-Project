import { useEffect, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'

const AuthCallbackPage = () => {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const { loginWithTokens } = useAuth()
  const [status, setStatus] = useState<'processing' | 'success' | 'error'>('processing')
  const [message, setMessage] = useState('Procesando autenticación...')

  useEffect(() => {
    const processAuthCallback = async () => {
      try {
        // Extract tokens from URL parameters
        const accessToken = searchParams.get('access_token')
        const refreshToken = searchParams.get('refresh_token')
        const email = searchParams.get('email')
        const username = searchParams.get('username')
        const userId = searchParams.get('user_id')
        const providers = searchParams.get('providers')
        // const sessionCreated = searchParams.get('session_created') // Future use

        // Check for error parameters
        const error = searchParams.get('error')
        if (error) {
          setStatus('error')
          setMessage(`Error de autenticación: ${error}`)
          setTimeout(() => navigate('/login'), 3000)
          return
        }

        // Validate required tokens
        if (!accessToken || !refreshToken || !email || !username) {
          setStatus('error')
          setMessage('Tokens de autenticación incompletos. Redirigiendo al login...')
          setTimeout(() => navigate('/login'), 3000)
          return
        }

        // Login with tokens using the auth hook
        loginWithTokens(accessToken, refreshToken, {
          user_id: userId ? parseInt(userId) : undefined,
          username,
          email,
          providers: providers || ''
        })

        setStatus('success')
        setMessage(`¡Bienvenido ${username}! Autenticación exitosa.`)

        // Show success message briefly then redirect
        setTimeout(() => navigate('/app/dashboard'), 2000)

      } catch (error) {
        console.error('Auth callback error:', error)
        setStatus('error')
        setMessage('Error al procesar la autenticación. Redirigiendo al login...')
        setTimeout(() => navigate('/login'), 3000)
      }
    }

    processAuthCallback()
  }, [searchParams, navigate, loginWithTokens])

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
      <div className="sm:mx-auto sm:w-full sm:max-w-md">
        <div className="bg-white py-8 px-4 shadow sm:rounded-lg sm:px-10">
          <div className="text-center">
            {/* Status Icon */}
            <div className="mx-auto flex items-center justify-center h-12 w-12 rounded-full mb-4">
              {status === 'processing' && (
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
              )}
              {status === 'success' && (
                <div className="bg-green-100 h-12 w-12 rounded-full flex items-center justify-center">
                  <svg className="h-6 w-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7"></path>
                  </svg>
                </div>
              )}
              {status === 'error' && (
                <div className="bg-red-100 h-12 w-12 rounded-full flex items-center justify-center">
                  <svg className="h-6 w-6 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12"></path>
                  </svg>
                </div>
              )}
            </div>

            {/* Status Message */}
            <h2 className={`text-lg font-medium mb-2 ${
              status === 'success' ? 'text-green-900' : 
              status === 'error' ? 'text-red-900' : 
              'text-gray-900'
            }`}>
              {status === 'processing' && 'Procesando Autenticación'}
              {status === 'success' && '¡Autenticación Exitosa!'}
              {status === 'error' && 'Error de Autenticación'}
            </h2>

            <p className={`text-sm ${
              status === 'success' ? 'text-green-600' : 
              status === 'error' ? 'text-red-600' : 
              'text-gray-600'
            }`}>
              {message}
            </p>

            {/* Progress indicator for success */}
            {status === 'success' && (
              <div className="mt-4">
                <div className="bg-gray-200 rounded-full h-2">
                  <div className="bg-primary-600 h-2 rounded-full animate-pulse" style={{ width: '100%' }}></div>
                </div>
                <p className="text-xs text-gray-500 mt-2">Redirigiendo al dashboard...</p>
              </div>
            )}

            {/* Error retry option */}
            {status === 'error' && (
              <div className="mt-4">
                <button
                  onClick={() => navigate('/login')}
                  className="btn-primary text-sm"
                >
                  Volver al Login
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

export default AuthCallbackPage 