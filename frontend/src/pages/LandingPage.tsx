import { Link } from 'react-router-dom'

const LandingPage = () => {
  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Hero Section */}
      <div className="text-center mb-12">
        <h2 className="text-4xl font-bold text-gray-900 mb-4">
          Automatiza tu <span className="text-primary-600">Gestión Financiera</span>
        </h2>
        <p className="text-xl text-gray-600 max-w-3xl mx-auto mb-8">
          Conecta múltiples emails (Gmail, Outlook, Yahoo) y deja que la IA categorice y rastree automáticamente tus transacciones financieras.
          Perfecto para mercados sin APIs bancarias tradicionales.
        </p>
        <div className="flex gap-4 justify-center">
          <Link to="/login" className="btn-primary text-lg px-8 py-3">
            Comenzar Gratis
          </Link>
          <button className="btn-secondary text-lg px-8 py-3">Ver Demo</button>
        </div>
      </div>

      {/* Features Grid */}
      <div className="grid md:grid-cols-3 gap-8 mb-12">
        <div className="card text-center">
          <div className="w-12 h-12 bg-primary-100 rounded-lg flex items-center justify-center mx-auto mb-4">
            <svg className="w-6 h-6 text-primary-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
            </svg>
          </div>
          <h3 className="text-xl font-semibold mb-2">Procesamiento Multi-Email</h3>
          <p className="text-gray-600">
            Conecta Gmail, Outlook, Yahoo y más. Extrae automáticamente datos de transacciones de múltiples fuentes.
          </p>
        </div>

        <div className="card text-center">
          <div className="w-12 h-12 bg-primary-100 rounded-lg flex items-center justify-center mx-auto mb-4">
            <svg className="w-6 h-6 text-primary-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
            </svg>
          </div>
          <h3 className="text-xl font-semibold mb-2">Categorización con IA</h3>
          <p className="text-gray-600">
            IA inteligente categoriza automáticamente tus gastos y aprende de tus patrones de consumo.
          </p>
        </div>

        <div className="card text-center">
          <div className="w-12 h-12 bg-primary-100 rounded-lg flex items-center justify-center mx-auto mb-4">
            <svg className="w-6 h-6 text-primary-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
            </svg>
          </div>
          <h3 className="text-xl font-semibold mb-2">Análisis e Informes</h3>
          <p className="text-gray-600">
            Obtén reportes detallados e insights sobre tus patrones de gasto y salud financiera.
          </p>
        </div>
      </div>

      {/* Provider Showcase */}
      <div className="card max-w-4xl mx-auto mb-12">
        <h3 className="text-xl font-semibold mb-6 text-center">Conecta Múltiples Proveedores de Email</h3>
        <div className="grid grid-cols-3 gap-8 text-center">
          <div className="flex flex-col items-center">
            <div className="w-16 h-16 bg-red-100 rounded-lg flex items-center justify-center mb-3">
              <span className="text-2xl font-bold text-red-600">G</span>
            </div>
            <span className="font-medium">Gmail</span>
            <span className="text-sm text-gray-500">Google OAuth</span>
          </div>
          <div className="flex flex-col items-center">
            <div className="w-16 h-16 bg-blue-100 rounded-lg flex items-center justify-center mb-3">
              <span className="text-2xl font-bold text-blue-600">O</span>
            </div>
            <span className="font-medium">Outlook</span>
            <span className="text-sm text-gray-500">Microsoft Graph</span>
          </div>
          <div className="flex flex-col items-center">
            <div className="w-16 h-16 bg-purple-100 rounded-lg flex items-center justify-center mb-3">
              <span className="text-2xl font-bold text-purple-600">Y</span>
            </div>
            <span className="font-medium">Yahoo Mail</span>
            <span className="text-sm text-gray-500">Yahoo API</span>
          </div>
        </div>
      </div>

      {/* Demo Card */}
      <div className="card max-w-2xl mx-auto">
        <h3 className="text-xl font-semibold mb-4">Prueba el Demo</h3>
        <div className="space-y-4">
          <div className="flex items-center p-3 bg-gray-50 rounded-lg">
            <div className="w-2 h-2 bg-green-500 rounded-full mr-3"></div>
            <span className="text-sm">Múltiples emails conectados exitosamente</span>
          </div>
          <div className="flex items-center p-3 bg-gray-50 rounded-lg">
            <div className="w-2 h-2 bg-blue-500 rounded-full mr-3"></div>
            <span className="text-sm">Procesando 147 notificaciones bancarias...</span>
          </div>
          <div className="flex items-center p-3 bg-gray-50 rounded-lg">
            <div className="w-2 h-2 bg-primary-500 rounded-full mr-3"></div>
            <span className="text-sm">147 transacciones categorizadas e importadas</span>
          </div>
        </div>
        <div className="mt-6 text-center">
          <Link to="/login" className="btn-primary">
            Comenzar Ahora →
          </Link>
        </div>
      </div>
    </div>
  )
}

export default LandingPage