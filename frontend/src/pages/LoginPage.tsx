import { Link } from 'react-router-dom'

const LoginPage = () => {
  const handleProviderLogin = (provider: string) => {
    // Redirect to Django allauth OAuth endpoints
    const backendUrl = 'http://127.0.0.1:8000'
    
    switch (provider) {
      case 'google':
        window.location.href = `${backendUrl}/accounts/google/login/`
        break
      case 'microsoft':
        window.location.href = `${backendUrl}/accounts/microsoft/login/`
        break
      case 'yahoo':
        console.log('Yahoo OAuth coming soon')
        break
      default:
        console.log(`Provider ${provider} not implemented yet`)
    }
  }

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
      <div className="sm:mx-auto sm:w-full sm:max-w-md">
        <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">
          Conecta tu Email
        </h2>
        <p className="mt-2 text-center text-sm text-gray-600">
          Selecciona tu proveedor de email para comenzar
        </p>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
        <div className="bg-white py-8 px-4 shadow sm:rounded-lg sm:px-10">
          <div className="space-y-4">
            {/* Google Login */}
            <button
              onClick={() => handleProviderLogin('google')}
              className="w-full flex justify-center items-center px-4 py-3 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 transition-colors"
            >
              <div className="flex items-center">
                <div className="w-5 h-5 bg-red-500 rounded mr-3 flex items-center justify-center">
                  <span className="text-white text-xs font-bold">G</span>
                </div>
                <span>Continuar con Gmail</span>
              </div>
            </button>

            {/* Microsoft Login */}
            <button
              onClick={() => handleProviderLogin('microsoft')}
              className="w-full flex justify-center items-center px-4 py-3 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 transition-colors"
            >
              <div className="flex items-center">
                <div className="w-5 h-5 bg-blue-500 rounded mr-3 flex items-center justify-center">
                  <span className="text-white text-xs font-bold">M</span>
                </div>
                <span>Continuar con Outlook</span>
              </div>
            </button>

            {/* Yahoo Login */}
            <button
              onClick={() => handleProviderLogin('yahoo')}
              className="w-full flex justify-center items-center px-4 py-3 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 transition-colors"
            >
              <div className="flex items-center">
                <div className="w-5 h-5 bg-purple-500 rounded mr-3 flex items-center justify-center">
                  <span className="text-white text-xs font-bold">Y</span>
                </div>
                <span>Continuar con Yahoo Mail</span>
              </div>
            </button>

            {/* Coming Soon Providers */}
            <div className="border-t pt-4 mt-6">
              <p className="text-center text-sm text-gray-500 mb-3">Próximamente:</p>
              <div className="space-y-2">
                <button
                  disabled
                  className="w-full flex justify-center items-center px-4 py-3 border border-gray-200 rounded-md shadow-sm text-sm font-medium text-gray-400 bg-gray-50 cursor-not-allowed"
                >
                  <div className="flex items-center">
                    <div className="w-5 h-5 bg-gray-300 rounded mr-3 flex items-center justify-center">
                      <span className="text-white text-xs font-bold">i</span>
                    </div>
                    <span>iCloud Mail (próximamente)</span>
                  </div>
                </button>
                <button
                  disabled
                  className="w-full flex justify-center items-center px-4 py-3 border border-gray-200 rounded-md shadow-sm text-sm font-medium text-gray-400 bg-gray-50 cursor-not-allowed"
                >
                  <div className="flex items-center">
                    <div className="w-5 h-5 bg-gray-300 rounded mr-3 flex items-center justify-center">
                      <span className="text-white text-xs font-bold">P</span>
                    </div>
                    <span>ProtonMail (próximamente)</span>
                  </div>
                </button>
              </div>
            </div>
          </div>

          <div className="mt-6">
            <div className="relative">
              <div className="absolute inset-0 flex items-center">
                <div className="w-full border-t border-gray-300" />
              </div>
              <div className="relative flex justify-center text-sm">
                <span className="px-2 bg-white text-gray-500">Seguro y Privado</span>
              </div>
            </div>
          </div>

          <div className="mt-6 text-center">
            <p className="text-xs text-gray-500">
              Solo accedemos a tus emails bancarios para procesar transacciones.
              <br />
              No almacenamos contenido de emails ni información personal.
            </p>
          </div>
        </div>

        <div className="mt-6 text-center">
          <Link to="/" className="text-sm text-primary-600 hover:text-primary-500">
            ← Volver al inicio
          </Link>
        </div>
      </div>
    </div>
  )
}

export default LoginPage 