const SettingsPage = () => {
  return (
    <div className="space-y-6">
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-semibold mb-2">Configuración</h2>
        <p className="text-gray-600">
          Gestiona tu perfil, proveedores de email y preferencias de la aplicación.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-medium mb-4">Proveedores de Email</h3>
          <div className="space-y-3">
            <div className="flex items-center justify-between p-3 border rounded-lg">
              <span>Gmail</span>
              <button className="btn-secondary text-sm">Desconectar</button>
            </div>
            <div className="flex items-center justify-between p-3 border rounded-lg">
              <span>Outlook</span>
              <button className="btn-secondary text-sm">Desconectar</button>
            </div>
            <div className="flex items-center justify-between p-3 border rounded-lg">
              <span>Yahoo Mail</span>
              <button className="btn-primary text-sm">Conectar</button>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-medium mb-4">Perfil de Usuario</h3>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Nombre
              </label>
              <input
                type="text"
                className="input-field"
                defaultValue="Usuario"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Email
              </label>
              <input
                type="email"
                className="input-field"
                defaultValue="user@example.com"
              />
            </div>
            <button className="btn-primary">
              Guardar Cambios
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

export default SettingsPage 