import { Outlet, Link, useLocation } from 'react-router-dom'

const PublicLayout = () => {
  const location = useLocation()
  const isLandingPage = location.pathname === '/'

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <Link to="/" className="flex items-center">
              <h1 className="text-2xl font-bold text-primary-600">AFP</h1>
              <span className="ml-2 text-sm text-gray-500">Tu Asistente de Finanzas Personales</span>
            </Link>
            <nav className="flex items-center gap-4">
              {isLandingPage ? (
                <Link to="/login" className="btn-primary">
                  Iniciar Sesión
                </Link>
              ) : (
                <Link to="/" className="btn-secondary">
                  ← Volver al Inicio
                </Link>
              )}
            </nav>
          </div>
        </div>
      </header>

      {/* Main Content - This is where each page will render */}
      <main>
        <Outlet />
      </main>

      {/* Footer */}
      <footer className="bg-gray-900 text-white py-8">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <p>&copy; 2024 AFP - Gestión de Finanzas Personales. Hecho con ❤️ para la automatización financiera.</p>
        </div>
      </footer>
    </div>
  )
}

export default PublicLayout 