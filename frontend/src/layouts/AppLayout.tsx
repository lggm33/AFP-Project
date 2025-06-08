import { Outlet, Link, useLocation } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'

const AppLayout = () => {
  const location = useLocation()
  const { user, logout, isLoading } = useAuth()

  const navigation = [
    { name: 'Dashboard', href: '/app/dashboard', icon: '📊' },
    { name: 'Transacciones', href: '/app/transactions', icon: '💳' },
    { name: 'Análisis', href: '/app/analytics', icon: '📈' },
    { name: 'Configuración', href: '/app/settings', icon: '⚙️' },
  ]

  const isActive = (href: string) => {
    return location.pathname === href || (href === '/app/dashboard' && location.pathname === '/app')
  }

  const handleLogout = async () => {
    if (window.confirm('¿Estás seguro de que deseas cerrar sesión?')) {
      await logout()
    }
  }

  const getUserInitials = (username: string, email: string) => {
    if (username) {
      return username.substring(0, 2).toUpperCase()
    }
    if (email) {
      return email.substring(0, 2).toUpperCase()
    }
    return 'U'
  }

  return (
    <div className="min-h-screen bg-gray-100">
      {/* Sidebar */}
      <div className="fixed inset-y-0 left-0 z-50 w-64 bg-white shadow-lg">
        <div className="flex h-full flex-col">
          {/* Logo */}
          <div className="flex h-16 shrink-0 items-center px-6 border-b">
            <Link to="/" className="flex items-center">
              <h1 className="text-xl font-bold text-primary-600">AFP</h1>
              <span className="ml-2 text-sm text-gray-500">Dashboard</span>
            </Link>
          </div>

          {/* Navigation */}
          <nav className="flex-1 px-4 py-6">
            <ul className="space-y-2">
              {navigation.map((item) => (
                <li key={item.name}>
                  <Link
                    to={item.href}
                    className={`group flex gap-x-3 rounded-md p-3 text-sm font-medium transition-colors ${
                      isActive(item.href)
                        ? 'bg-primary-50 text-primary-600'
                        : 'text-gray-700 hover:text-primary-600 hover:bg-gray-50'
                    }`}
                  >
                    <span className="text-lg">{item.icon}</span>
                    {item.name}
                  </Link>
                </li>
              ))}
            </ul>
          </nav>

          {/* User Profile */}
          <div className="border-t px-4 py-4">
            <div className="flex items-center gap-3 p-3 rounded-md hover:bg-gray-50">
              <div className="w-8 h-8 bg-primary-100 rounded-full flex items-center justify-center">
                <span className="text-primary-600 font-medium text-sm">
                  {user ? getUserInitials(user.username, user.email) : 'U'}
                </span>
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-gray-700">
                  {user?.username || 'Usuario'}
                </p>
                <p className="text-xs text-gray-500 truncate">
                  {user?.email || 'email@domain.com'}
                </p>
              </div>
              <button 
                onClick={handleLogout}
                disabled={isLoading}
                className="text-gray-400 hover:text-red-600 disabled:opacity-50 transition-colors"
                title="Cerrar sesión"
              >
                <span className="sr-only">Cerrar sesión</span>
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
                </svg>
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Main content */}
      <div className="pl-64">
        {/* Top header */}
        <header className="bg-white shadow-sm border-b">
          <div className="px-6 py-4">
            <div className="flex items-center justify-between">
              <h1 className="text-2xl font-semibold text-gray-900">
                {navigation.find(item => isActive(item.href))?.name || 'Dashboard'}
              </h1>
              <div className="flex items-center gap-4">
                <button className="btn-secondary">
                  + Conectar Email
                </button>
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                  <span className="text-sm text-gray-600">
                    {user?.providers?.length || 0} emails conectados
                  </span>
                </div>
                
                {/* User menu in header */}
                <div className="flex items-center gap-2 text-sm text-gray-600">
                  <span>Hola, {user?.username || 'Usuario'}</span>
                  <button 
                    onClick={handleLogout}
                    disabled={isLoading}
                    className="text-gray-500 hover:text-red-600 disabled:opacity-50 transition-colors ml-2"
                    title="Cerrar sesión"
                  >
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
                    </svg>
                  </button>
                </div>
              </div>
            </div>
          </div>
        </header>

        {/* Page content */}
        <main className="p-6">
          <Outlet />
        </main>
      </div>
    </div>
  )
}

export default AppLayout 