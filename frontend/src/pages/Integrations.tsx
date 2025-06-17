import { useState, useEffect } from 'react'
import { useAuth } from '../hooks/useAuth'
import { useProviderAuth } from '../hooks/useProviderAuth'

interface Integration {
  id: number
  user: string
  provider: string
  provider_display: string
  email_address: string
  is_active: boolean
  created_at: string
  updated_at: string
  updated_by: string
  updated_message?: string
}

interface GmailMessage {
  id: number
  integration: {
    id: number
    email_address: string
    provider: string
  }
  provider_message_id: string
  sender: string
  recipient: string
  subject: string
  body: string
  attachment_count: number
  created_at: string
  processed_at?: string
  process_by?: string
  // Campos calculados para compatibilidad
  timestamp?: string
  snippet?: string
}

interface BankSender {
  id: number
  user: number
  integration: number
  integration_email: string
  bank_sender: number
  bank_sender_details: {
    id: number
    bank_name: string
    bank_country: string
    sender_email: string
    sender_name: string
    sender_domain: string
    is_verified: boolean
    confidence_score: number
    total_emails_processed: number
  }
  is_active: boolean
  custom_confidence?: number
  custom_name: string
  emails_processed: number
  last_email_at?: string
  added_at: string
  updated_at: string
  notes: string
  effective_confidence: number
  display_name: string
}

interface EmailFilters {
  page_size: number
  days_back: number
  sender_filter: string
  only_bank_senders: boolean
  search_type: 'all' | 'bank_senders'
}

interface PaginationData {
  total_count: number
  page: number
  page_size: number
  total_pages: number
  has_next: boolean
  has_previous: boolean
}

interface TestResult {
  loading: boolean
  result?: {
    email: string
    messages_total: number
    threads_total: number
    history_id?: string
  }
  error?: string
}

const IntegrationsPage = () => {
  const { makeAuthenticatedRequest } = useAuth()
  const [activeTab, setActiveTab] = useState<'integrations' | 'senders' | 'emails'>('integrations')
  
  // Integrations State
  const [integrations, setIntegrations] = useState<Integration[]>([])
  const [integrationsLoading, setIntegrationsLoading] = useState(false)
  const [selectedIntegration, setSelectedIntegration] = useState<Integration | null>(null)
  const [testResults, setTestResults] = useState<Record<number, TestResult>>({})
  const [testingIntegration, setTestingIntegration] = useState<number | null>(null)
  
  // Provider Auth State - Siempre llamar al hook, pero solo usar sus funciones cuando hay una integración seleccionada
  const providerAuth = useProviderAuth(selectedIntegration?.id.toString() || '0');
  
  // Bank Senders State
  const [bankSenders, setBankSenders] = useState<BankSender[]>([])
  const [sendersLoading, setSendersLoading] = useState(false)
  const [newSender, setNewSender] = useState({
    sender_email: '',
    sender_name: '',
    bank_name: ''
  })
  
  // Emails State
  const [emails, setEmails] = useState<GmailMessage[]>([])
  const [emailsLoading, setEmailsLoading] = useState(false)
  const [emailFilters, setEmailFilters] = useState<EmailFilters>({
    page_size: 50,
    days_back: 30,
    sender_filter: '',
    only_bank_senders: false,
    search_type: 'all'
  })
  const [emailStats, setEmailStats] = useState({
    total_emails: 0,
    bank_emails: 0,
    unique_senders: 0
  })
  const [pagination, setPagination] = useState<PaginationData>({
    total_count: 0,
    page: 1,
    page_size: 50,
    total_pages: 0,
    has_next: false,
    has_previous: false
  })
  const [currentPage, setCurrentPage] = useState(1)

  // Load integrations on component mount
  useEffect(() => {
    loadIntegrations()
  }, [])

  // Load bank senders when selected integration changes
  useEffect(() => {
    if (selectedIntegration) {
      loadBankSenders(selectedIntegration.id)
    } else {
      setBankSenders([])
    }
  }, [selectedIntegration])

  // Load bank senders when integration is selected
  useEffect(() => {
    if (selectedIntegration) {
      loadBankSenders(selectedIntegration.id)
    }
  }, [selectedIntegration])

  const loadIntegrations = async () => {
    setIntegrationsLoading(true)
    try {
      const response = await makeAuthenticatedRequest('/api/core/integrations/')
      const data = await response.json()
      setIntegrations(data.results || [])
      
      // Auto-select first active integration
      const activeIntegration = data.results?.find((int: Integration) => int.is_active)
      if (activeIntegration && !selectedIntegration) {
        setSelectedIntegration(activeIntegration)
      }
    } catch (error) {
      console.error('Error loading integrations:', error)
    }
    setIntegrationsLoading(false)
  }

  const testIntegrationConnection = async (integrationId: number) => {
    setTestingIntegration(integrationId)
    setTestResults(prev => ({
      ...prev,
      [integrationId]: { loading: true }
    }))

    try {
      const response = await makeAuthenticatedRequest(`/api/core/integrations/${integrationId}/test_connection/`, {
        method: 'POST'
      })
      const data = await response.json()
      
      setTestResults(prev => ({
        ...prev,
        [integrationId]: {
          loading: false,
          result: data.success ? data.data : null,
          error: data.success ? undefined : (data.error || 'Unknown error')
        }
      }))
    } catch (error) {
      setTestResults(prev => ({
        ...prev,
        [integrationId]: {
          loading: false,
          error: `Connection test failed: ${error}`
        }
      }))
    } finally {
      setTestingIntegration(null)
    }
  }

  const toggleIntegrationStatus = async (integrationId: number, currentStatus: boolean) => {
    try {
      const response = await makeAuthenticatedRequest(`/api/core/integrations/${integrationId}/`, {
        method: 'PATCH',
        body: JSON.stringify({
          is_active: !currentStatus
        })
      })
      
      if (response.ok) {
        loadIntegrations() // Reload to get updated data
      }
    } catch (error) {
      console.error('Error toggling integration status:', error)
    }
  }

  const loadBankSenders = async (integrationId: number) => {
    setSendersLoading(true)
    try {
      const response = await makeAuthenticatedRequest(`/api/core/user-bank-senders/by_integration/?integration_id=${integrationId}`)
      const data = await response.json()
      
      if (data.success) {
        setBankSenders(data.results || [])
      }
    } catch (error) {
      console.error('Error loading bank senders:', error)
    }
    setSendersLoading(false)
  }

  const addBankSender = async () => {
    if (!selectedIntegration || !newSender.sender_email || !newSender.bank_name) {
      alert('Please fill in all required fields')
      return
    }

    try {
      const response = await makeAuthenticatedRequest('/api/core/user-bank-senders/add_by_email/', {
        method: 'POST',
        body: JSON.stringify({
          sender_email: newSender.sender_email,
          sender_name: newSender.sender_name,
          bank_name: newSender.bank_name,
          integration_id: selectedIntegration.id
        })
      })
      
      const data = await response.json()
      
      if (data.success) {
        alert(data.message)
        
        // Reset form
        setNewSender({
          sender_email: '',
          sender_name: '',
          bank_name: ''
        })
        
        // Reload senders
        loadBankSenders(selectedIntegration.id)
      } else {
        alert(`Error: ${data.error}`)
      }
    } catch (error) {
      console.error('Error adding bank sender:', error)
      alert('Failed to add bank sender')
    }
  }

  const loadEmails = async (page: number = 1) => {
    if (!selectedIntegration) return;

    setEmailsLoading(true);
    try {
      // Verificar el estado del token antes de cargar los emails
      await providerAuth?.getTokenStatus();
      
      // Calcular offset y limit para paginación tipo backend
      const limit = emailFilters.page_size;
      const offset = (page - 1) * limit;
      const params = new URLSearchParams({
        integration_id: selectedIntegration.id.toString(),
        limit: limit.toString(),
        offset: offset.toString(),
        type: emailFilters.search_type,
        days_back: emailFilters.days_back.toString(),
        page: page.toString(),
        page_size: limit.toString(),
        sender_filter: emailFilters.sender_filter,
        only_bank_senders: emailFilters.only_bank_senders ? 'true' : ''
      });

			console.log(`/api/core/integrations/${selectedIntegration.id}/messages/live/?${params.toString()}`)      
      const response = await makeAuthenticatedRequest(
        `/api/core/integrations/${selectedIntegration.id}/messages/live/?${params.toString()}`
      );
      const data = await response.json();

			console.log(data);
      
      // Procesar emails para agregar campos de compatibilidad
      const processedEmails = (data.emails || []).map((email: GmailMessage) => ({
        ...email,
        timestamp: email.created_at, // Mapear created_at a timestamp para compatibilidad
        snippet: email.body ? email.body.substring(0, 150) + '...' : '' // Crear snippet del body
      }));
      
      setEmails(processedEmails);
      
      // Corregir cálculo de paginación
      setPagination({
        total_count: data.total_count || 0,
        page: Math.floor((data.offset || 0) / (data.limit || limit)) + 1,
        page_size: data.limit || limit,
        total_pages: Math.ceil((data.total_count || 1) / (data.limit || limit)),
        has_next: (data.offset || 0) + (data.count || 0) < (data.total_count || 0),
        has_previous: (data.offset || 0) > 0
      });
      
      setCurrentPage(Math.floor((data.offset || 0) / (data.limit || limit)) + 1);
      
      // Actualizar estadísticas
      setEmailStats({
        total_emails: data.total_count || 0,
        bank_emails: processedEmails.filter((msg: GmailMessage) => 
          msg.sender && (msg.sender.includes('bank') || msg.sender.includes('banco'))
        ).length,
        unique_senders: new Set(processedEmails.map((msg: GmailMessage) => msg.sender)).size
      });
    } catch (error) {
      console.error('Error loading emails:', error);
      // Si hay un error de autenticación, intentar refrescar el token
      if (error instanceof Error && error.message === 'Authentication expired') {
        try {
          await providerAuth?.refreshTokens();
          // Reintentar la carga de emails
          await loadEmails(page);
        } catch (refreshError) {
          console.error('Error refreshing provider tokens:', refreshError);
        }
      }
    } finally {
      setEmailsLoading(false);
    }
  };

  const importEmailsFromGmail = async () => {
    if (!selectedIntegration) return;

    setEmailsLoading(true);
    try {
      // Verificar el estado del token antes de importar
      await providerAuth?.getTokenStatus();
      
      const response = await makeAuthenticatedRequest('/api/core/gmail/import/', {
        method: 'POST',
        body: JSON.stringify({
          integration_id: selectedIntegration.id,
          days_back: emailFilters.days_back,
          max_results: 100,
          import_type: emailFilters.only_bank_senders ? 'banking' : 'all'
        })
      });
      
      const data = await response.json();
      
      if (data.success) {
        alert(`✅ Importación exitosa: ${data.results.emails_imported} emails importados`);
        // Recargar emails después de la importación
        await loadEmails();
      } else {
        alert(`❌ Error en la importación: ${data.message}`);
      }
    } catch (error) {
      console.error('Error importing emails:', error);
      alert('❌ Error al importar emails desde Gmail');
    } finally {
      setEmailsLoading(false);
    }
  };

  const goToPage = (page: number) => {
    if (page >= 1 && page <= pagination.total_pages) {
      loadEmails(page)
    }
  }

  const goToNextPage = () => {
    if (pagination.has_next) {
      goToPage(currentPage + 1)
    }
  }

  const goToPreviousPage = () => {
    if (pagination.has_previous) {
      goToPage(currentPage - 1)
    }
  }

  const tabs = [
    { id: 'integrations', name: 'Integraciones', icon: '🔗' },
    { id: 'senders', name: 'Remitentes Bancarios', icon: '🏦' },
    { id: 'emails', name: 'Gestión de Emails', icon: '📧' }
  ]

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-2xl font-bold mb-2">Gestión de Integraciones de Email</h2>
        <p className="text-gray-600">
          Administra tus integraciones de email, configura remitentes bancarios y previsualiza el procesamiento de emails.
        </p>
      </div>

      {/* Integration Selector */}
      {integrations.length > 0 && (
        <div className="bg-white rounded-lg shadow p-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <label className="text-sm font-medium text-gray-700">Integración Activa:</label>
              <select
                value={selectedIntegration?.id || ''}
                onChange={(e) => {
                  const integration = integrations.find(int => int.id === parseInt(e.target.value))
                  setSelectedIntegration(integration || null)
                }}
                className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">Seleccionar Integración</option>
                {integrations.map(integration => (
                  <option key={integration.id} value={integration.id}>
                    {integration.provider_display} - {integration.email_address}
                    {integration.is_active ? ' (Activa)' : ' (Inactiva)'}
                  </option>
                ))}
              </select>
            </div>
            
            {selectedIntegration && (
              <div className="flex items-center space-x-2">
                <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                  selectedIntegration.is_active 
                    ? 'bg-green-100 text-green-800' 
                    : 'bg-red-100 text-red-800'
                }`}>
                  {selectedIntegration.is_active ? 'Active' : 'Inactive'}
                </span>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Agregar indicador de estado del token */}
      {selectedIntegration && providerAuth?.tokenStatus && (
        <div className={`mb-4 p-3 rounded ${
          providerAuth.tokenStatus.status === 'active' ? 'bg-green-100 text-green-800' :
          providerAuth.tokenStatus.status === 'expired' ? 'bg-yellow-100 text-yellow-800' :
          'bg-red-100 text-red-800'
        }`}>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium">
                Estado del token: {providerAuth.tokenStatus.status}
                {providerAuth.tokenStatus.expiresAt && (
                  <span className="ml-2 font-normal">
                    (Expira: {new Date(providerAuth.tokenStatus.expiresAt).toLocaleString()})
                  </span>
                )}
              </p>
              {providerAuth.tokenStatus.errorMessage && (
                <p className="text-xs mt-1 opacity-75">
                  {providerAuth.tokenStatus.errorMessage}
                </p>
              )}
            </div>
            {providerAuth.tokenStatus.status !== 'active' && (
              <button
                onClick={async () => {
                  try {
                    await providerAuth.refreshTokens();
                    await providerAuth.getTokenStatus();
                  } catch (error) {
                    console.error('Error refreshing token:', error);
                  }
                }}
                disabled={providerAuth.isRefreshing}
                className="px-3 py-1 bg-blue-600 text-white text-xs rounded hover:bg-blue-700 disabled:bg-gray-400"
              >
                {providerAuth.isRefreshing ? 'Refrescando...' : 'Refrescar Token'}
              </button>
            )}
          </div>
        </div>
      )}

      {/* Tabs */}
      <div className="bg-white rounded-lg shadow">
        <div className="border-b border-gray-200">
          <nav className="-mb-px flex space-x-8 px-6">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as 'integrations' | 'senders' | 'emails')}
                className={`py-4 px-1 border-b-2 font-medium text-sm ${
                  activeTab === tab.id
                    ? 'border-primary-500 text-primary-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                <span className="mr-2">{tab.icon}</span>
                {tab.name}
              </button>
            ))}
          </nav>
        </div>

        <div className="p-6">
          {/* Integrations Tab */}
          {activeTab === 'integrations' && (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-medium">Email Integrations</h3>
                <button
                  onClick={loadIntegrations}
                  disabled={integrationsLoading}
                  className="btn-primary"
                >
                  {integrationsLoading ? 'Loading...' : 'Refresh'}
                </button>
              </div>

              {integrations.length === 0 ? (
                <div className="text-center py-8">
                  <p className="text-gray-500 mb-4">No integrations found</p>
                  <p className="text-sm text-gray-400">
                    Connect your email accounts through the OAuth login process
                  </p>
                </div>
              ) : (
                <div className="space-y-4">
                  {integrations.map((integration) => {
                    const testResult = testResults[integration.id]
                    const isTestingThis = testingIntegration === integration.id
                    
                    return (
                      <div key={integration.id} className="border rounded-lg p-4">
                        <div className="flex items-center justify-between">
                          <div className="flex-1">
                            <div className="flex items-center space-x-3">
                              <h4 className="font-medium">{integration.provider_display}</h4>
                              <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                                integration.is_active 
                                  ? 'bg-green-100 text-green-800' 
                                  : 'bg-red-100 text-red-800'
                              }`}>
                                {integration.is_active ? 'Active' : 'Inactive'}
                              </span>
                            </div>
                            <p className="text-sm text-gray-600 mt-1">{integration.email_address}</p>
                            <p className="text-xs text-gray-400 mt-1">
                              Created: {new Date(integration.created_at).toLocaleDateString()}
                              {integration.updated_message && ` • ${integration.updated_message}`}
                            </p>
                          </div>
                          
                          <div className="flex items-center space-x-2">
                            <button
                              onClick={() => testIntegrationConnection(integration.id)}
                              disabled={isTestingThis}
                              className={`px-3 py-1 rounded text-sm ${
                                isTestingThis
                                  ? 'bg-gray-400 text-white cursor-not-allowed'
                                  : 'bg-blue-500 text-white hover:bg-blue-600'
                              }`}
                            >
                              {isTestingThis ? 'Testing...' : 'Test'}
                            </button>
                            <button
                              onClick={() => toggleIntegrationStatus(integration.id, integration.is_active)}
                              className={`px-3 py-1 rounded text-sm ${
                                integration.is_active
                                  ? 'bg-red-500 text-white hover:bg-red-600'
                                  : 'bg-green-500 text-white hover:bg-green-600'
                              }`}
                            >
                              {integration.is_active ? 'Deactivate' : 'Activate'}
                            </button>
                          </div>
                        </div>

                        {/* Test Results Display */}
                        {testResult && !testResult.loading && (
                          <div className={`mt-4 p-3 rounded-lg ${
                            testResult.error 
                              ? 'bg-red-50 border border-red-200' 
                              : 'bg-green-50 border border-green-200'
                          }`}>
                            <div className="flex items-center mb-2">
                              <span className={`w-3 h-3 rounded-full mr-2 ${
                                testResult.error ? 'bg-red-500' : 'bg-green-500'
                              }`}></span>
                              <h5 className="font-medium">
                                {testResult.error ? 'Connection Failed' : 'Connection Successful'}
                              </h5>
                            </div>
                            
                            {testResult.error ? (
                              <p className="text-sm text-red-700">{testResult.error}</p>
                            ) : testResult.result && (
                              <div className="space-y-1 text-sm text-gray-700">
                                <p><strong>Email:</strong> {testResult.result.email}</p>
                                <p><strong>Total Messages:</strong> {testResult.result.messages_total?.toLocaleString()}</p>
                                <p><strong>Total Threads:</strong> {testResult.result.threads_total?.toLocaleString()}</p>
                                {testResult.result.history_id && (
                                  <p><strong>History ID:</strong> {testResult.result.history_id}</p>
                                )}
                              </div>
                            )}
                          </div>
                        )}
                      </div>
                    )
                  })}
                </div>
              )}
            </div>
          )}

          {/* Bank Senders Tab */}
          {activeTab === 'senders' && (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-medium">Bank Senders Configuration</h3>
                {!selectedIntegration && (
                  <p className="text-sm text-red-600">Please select an integration first</p>
                )}
              </div>

              {selectedIntegration && (
                <>
                  {/* Add New Sender Form */}
                  <div className="bg-gray-50 rounded-lg p-4">
                    <h4 className="font-medium mb-3">Add Bank Sender</h4>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          Sender Email *
                        </label>
                        <input
                          type="email"
                          value={newSender.sender_email}
                          onChange={(e) => setNewSender({...newSender, sender_email: e.target.value})}
                          placeholder="notifications@bank.com"
                          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          Sender Name
                        </label>
                        <input
                          type="text"
                          value={newSender.sender_name}
                          onChange={(e) => setNewSender({...newSender, sender_name: e.target.value})}
                          placeholder="Bank Notifications"
                          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          Bank Name *
                        </label>
                        <input
                          type="text"
                          value={newSender.bank_name}
                          onChange={(e) => setNewSender({...newSender, bank_name: e.target.value})}
                          placeholder="Bank of America"
                          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                        />
                      </div>
                    </div>
                    <div className="mt-4">
                      <button
                        onClick={addBankSender}
                        className="btn-primary"
                      >
                        Add Sender
                      </button>
                    </div>
                  </div>

                  {/* Bank Senders List */}
                  <div>
                    <h4 className="font-medium mb-3">Configured Bank Senders</h4>
                    {sendersLoading ? (
                      <p className="text-gray-500">Loading senders...</p>
                    ) : bankSenders.length === 0 ? (
                      <p className="text-gray-500">No bank senders configured yet</p>
                    ) : (
                      <div className="space-y-2">
                        {bankSenders.map((sender) => (
                          <div key={sender.id} className="flex items-center justify-between p-3 border rounded">
                            <div>
                                              <p className="font-medium">{sender.bank_sender_details.bank_name}</p>
                <p className="text-sm text-gray-600">{sender.bank_sender_details.sender_email}</p>
                {sender.display_name && (
                  <p className="text-xs text-gray-500">{sender.display_name}</p>
                              )}
                            </div>
                            <div className="flex items-center space-x-2">
                              <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                                sender.is_active 
                                  ? 'bg-green-100 text-green-800' 
                                  : 'bg-red-100 text-red-800'
                              }`}>
                                {sender.is_active ? 'Active' : 'Inactive'}
                              </span>
                              <button className="text-red-600 hover:text-red-800 text-sm">
                                Remove
                              </button>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </>
              )}
            </div>
          )}

          {/* Emails Tab */}
          {activeTab === 'emails' && (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-medium">Email Management</h3>
                {!selectedIntegration && (
                  <p className="text-sm text-red-600">Please select an integration first</p>
                )}
              </div>

              {selectedIntegration && (
                <>
                  {/* Email Filters */}
                  <div className="bg-gray-50 rounded-lg p-4">
                    <h4 className="font-medium mb-3">Filtros de Email</h4>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          Emails por Página
                        </label>
                        <input
                          type="number"
                          value={emailFilters.page_size}
                          onChange={(e) => setEmailFilters({...emailFilters, page_size: parseInt(e.target.value) || 50})}
                          min="1"
                          max="100"
                          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          Días Atrás
                        </label>
                        <input
                          type="number"
                          value={emailFilters.days_back}
                          onChange={(e) => setEmailFilters({...emailFilters, days_back: parseInt(e.target.value) || 30})}
                          min="1"
                          max="90"
                          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          Filtro por Remitente
                        </label>
                        <input
                          type="text"
                          value={emailFilters.sender_filter}
                          onChange={(e) => setEmailFilters({...emailFilters, sender_filter: e.target.value})}
                          placeholder="@banco.com"
                          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                        />
                      </div>
                      <div className="flex items-end">
                        <label className="flex items-center space-x-2">
                          <input
                            type="checkbox"
                            checked={emailFilters.only_bank_senders}
                            onChange={(e) => setEmailFilters({...emailFilters, only_bank_senders: e.target.checked})}
                            className="rounded"
                          />
                          <span className="text-sm text-gray-700">
                            Solo mis remitentes bancarios
                            <span className="text-xs text-gray-500 block">
                              ({bankSenders.filter(s => s.is_active).length} activos)
                            </span>
                          </span>
                        </label>
                      </div>
                    </div>
                    <div className="mt-4 flex space-x-4">
                      <button
                        onClick={() => loadEmails()}
                        disabled={emailsLoading}
                        className="btn-primary"
                      >
                        {emailsLoading ? 'Cargando...' : 'Cargar Emails'}
                      </button>
                      <button
                        onClick={importEmailsFromGmail}
                        disabled={emailsLoading || !selectedIntegration}
                        className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
                      >
                        {emailsLoading ? 'Importando...' : 'Importar desde Gmail'}
                      </button>
                    </div>
                  </div>

                  {/* Email Stats */}
                  {emails.length > 0 && (
                    <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                      <h4 className="font-medium mb-2">Estadísticas de Emails</h4>
                      <div className="grid grid-cols-3 gap-4 text-sm">
                        <div>
                          <span className="text-gray-600">Total Emails:</span>
                          <span className="ml-2 font-medium">{emailStats.total_emails}</span>
                        </div>
                        <div>
                          <span className="text-gray-600">Remitentes Únicos:</span>
                          <span className="ml-2 font-medium">{emailStats.unique_senders}</span>
                        </div>
                        <div>
                          <span className="text-gray-600">Emails Bancarios:</span>
                          <span className="ml-2 font-medium text-green-600">{emailStats.bank_emails}</span>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Mensaje cuando no hay emails */}
                  {emails.length === 0 && !emailsLoading && (
                    <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6 text-center">
                      <div className="text-yellow-600 mb-2">
                        <svg className="mx-auto h-12 w-12" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-4m-4 0H8m-4 0h4m0 0V9a2 2 0 012-2h4a2 2 0 012 2v4.01" />
                        </svg>
                      </div>
                      <h3 className="text-lg font-medium text-yellow-800 mb-2">
                        No hay emails en la base de datos
                      </h3>
                      <p className="text-yellow-700 mb-4">
                        Para ver emails, primero necesitas importarlos desde Gmail usando el botón "Importar desde Gmail".
                      </p>
                      <p className="text-sm text-yellow-600">
                        💡 Tip: Asegúrate de que el token esté activo antes de importar.
                      </p>
                    </div>
                  )}

                  {/* Emails List */}
                  {emails.length > 0 && (
                    <div className="space-y-3">
                      <h4 className="font-medium">
                        Emails ({emails.length} de {pagination.total_count})
                        {emailFilters.only_bank_senders && (
                          <span className="text-sm font-normal text-green-600 ml-2">
                            • Filtrado por tus remitentes bancarios activos
                          </span>
                        )}
                      </h4>
                      {emails.map((email) => {
                        // Find matching bank sender if filtering by bank senders
                        const matchingBankSender = emailFilters.only_bank_senders 
                          ? bankSenders.find(sender => 
                              sender.is_active && 
                              email.sender.toLowerCase().includes(sender.bank_sender_details.sender_email.toLowerCase())
                            )
                          : null

                        return (
                          <div key={email.id} className={`border rounded-lg p-4 ${
                            emailFilters.only_bank_senders ? 'bg-green-50 border-green-200' : 'bg-white'
                          }`}>
                            <div className="flex justify-between items-start mb-2">
                              <h5 className="font-medium truncate flex-1 mr-4">
                                {email.subject || '(No Subject)'}
                              </h5>
                              <span className="text-xs text-gray-500 whitespace-nowrap">
                                {email.timestamp ? new Date(email.timestamp).toLocaleDateString() : 'No date'}
                              </span>
                            </div>
                            <div className="flex items-center justify-between mb-2">
                              <p className="text-sm text-gray-600">From: {email.sender}</p>
                              {matchingBankSender && (
                                <span className="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded-full">
                                  {matchingBankSender.bank_sender_details.bank_name}
                                </span>
                              )}
                            </div>
                            <p className="text-sm text-gray-700">{email.snippet}</p>
                          </div>
                        )
                      })}
                      
                      {/* Pagination Controls */}
                      {pagination.total_pages > 1 && (
                        <div className="flex items-center justify-between bg-gray-50 px-4 py-3 rounded-lg">
                          <div className="flex items-center space-x-2">
                            <span className="text-sm text-gray-700">
                              Página {currentPage} de {pagination.total_pages}
                            </span>
                            <span className="text-xs text-gray-500">
                              ({pagination.total_count} emails totales)
                            </span>
                          </div>
                          
                          <div className="flex items-center space-x-2">
                            <button
                              onClick={goToPreviousPage}
                              disabled={!pagination.has_previous || emailsLoading}
                              className={`px-3 py-1 rounded text-sm ${
                                pagination.has_previous && !emailsLoading
                                  ? 'bg-blue-500 text-white hover:bg-blue-600'
                                  : 'bg-gray-300 text-gray-500 cursor-not-allowed'
                              }`}
                            >
                              ← Anterior
                            </button>
                            
                            {/* Page numbers */}
                            <div className="flex items-center space-x-1">
                              {Array.from({ length: Math.min(5, pagination.total_pages) }, (_, i) => {
                                let pageNum;
                                if (pagination.total_pages <= 5) {
                                  pageNum = i + 1;
                                } else if (currentPage <= 3) {
                                  pageNum = i + 1;
                                } else if (currentPage >= pagination.total_pages - 2) {
                                  pageNum = pagination.total_pages - 4 + i;
                                } else {
                                  pageNum = currentPage - 2 + i;
                                }
                                
                                return (
                                  <button
                                    key={pageNum}
                                    onClick={() => goToPage(pageNum)}
                                    disabled={emailsLoading}
                                    className={`px-2 py-1 rounded text-sm ${
                                      pageNum === currentPage
                                        ? 'bg-blue-500 text-white'
                                        : 'bg-white text-gray-700 hover:bg-gray-100'
                                    } ${emailsLoading ? 'cursor-not-allowed opacity-50' : ''}`}
                                  >
                                    {pageNum}
                                  </button>
                                );
                              })}
                            </div>
                            
                            <button
                              onClick={goToNextPage}
                              disabled={!pagination.has_next || emailsLoading}
                              className={`px-3 py-1 rounded text-sm ${
                                pagination.has_next && !emailsLoading
                                  ? 'bg-blue-500 text-white hover:bg-blue-600'
                                  : 'bg-gray-300 text-gray-500 cursor-not-allowed'
                              }`}
                            >
                              Siguiente →
                            </button>
                          </div>
                        </div>
                      )}
                    </div>
                  )}
                </>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default IntegrationsPage 