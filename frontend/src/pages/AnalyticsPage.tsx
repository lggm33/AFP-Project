const AnalyticsPage = () => {
  return (
    <div className="space-y-6">
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-semibold mb-2">Análisis Financiero</h2>
        <p className="text-gray-600">
          Próximamente: Gráficos y análisis detallados de tus transacciones multi-proveedor.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-medium mb-4">Gastos por Categoría</h3>
          <div className="h-48 bg-gray-100 rounded-lg flex items-center justify-center">
            <span className="text-gray-500">Gráfico de dona aquí</span>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-medium mb-4">Tendencia Mensual</h3>
          <div className="h-48 bg-gray-100 rounded-lg flex items-center justify-center">
            <span className="text-gray-500">Gráfico de líneas aquí</span>
          </div>
        </div>
      </div>
    </div>
  )
}

export default AnalyticsPage 