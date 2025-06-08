const TransactionsPage = () => {
  const mockTransactions = [
    {
      id: 1,
      date: '2024-01-15',
      description: 'Compra en Supermercado',
      amount: -15450,
      category: 'Alimentación',
      bank: 'Banco Nacional',
      source: 'Gmail'
    },
    {
      id: 2,
      date: '2024-01-14',
      description: 'Transferencia recibida',
      amount: 50000,
      category: 'Ingresos',
      bank: 'Banco Popular',
      source: 'Outlook'
    },
    {
      id: 3,
      date: '2024-01-14',
      description: 'Pago de servicios públicos',
      amount: -22300,
      category: 'Servicios',
      bank: 'BAC San José',
      source: 'Gmail'
    }
  ]

  const formatAmount = (amount: number) => {
    const formatted = Math.abs(amount).toLocaleString('es-CR')
    return amount < 0 ? `-₡${formatted}` : `₡${formatted}`
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-xl font-semibold">Transacciones</h2>
            <p className="text-gray-600">Todas tus transacciones procesadas automáticamente</p>
          </div>
          <div className="flex gap-3">
            <select className="border border-gray-300 rounded-md px-3 py-2 text-sm">
              <option>Todos los bancos</option>
              <option>Banco Nacional</option>
              <option>Banco Popular</option>
              <option>BAC San José</option>
            </select>
            <select className="border border-gray-300 rounded-md px-3 py-2 text-sm">
              <option>Todas las fuentes</option>
              <option>Gmail</option>
              <option>Outlook</option>
              <option>Yahoo</option>
            </select>
          </div>
        </div>
      </div>

      {/* Transactions Table */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-medium">Historial de Transacciones</h3>
        </div>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Fecha
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Descripción
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Categoría
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Banco
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Fuente
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Monto
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {mockTransactions.map((transaction) => (
                <tr key={transaction.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {transaction.date}
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-900">
                    {transaction.description}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                      {transaction.category}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {transaction.bank}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center">
                      <div className={`w-2 h-2 rounded-full mr-2 ${
                        transaction.source === 'Gmail' ? 'bg-red-500' : 
                        transaction.source === 'Outlook' ? 'bg-blue-500' : 'bg-purple-500'
                      }`}></div>
                      <span className="text-sm text-gray-900">{transaction.source}</span>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-right">
                    <span className={`font-medium ${
                      transaction.amount < 0 ? 'text-red-600' : 'text-green-600'
                    }`}>
                      {formatAmount(transaction.amount)}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Pagination */}
      <div className="bg-white rounded-lg shadow p-4">
        <div className="flex items-center justify-between">
          <p className="text-sm text-gray-700">
            Mostrando <span className="font-medium">1</span> a <span className="font-medium">3</span> de{' '}
            <span className="font-medium">147</span> transacciones
          </p>
          <div className="flex gap-2">
            <button className="btn-secondary text-sm px-3 py-2">Anterior</button>
            <button className="btn-primary text-sm px-3 py-2">Siguiente</button>
          </div>
        </div>
      </div>
    </div>
  )
}

export default TransactionsPage 