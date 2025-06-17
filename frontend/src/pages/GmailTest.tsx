import { useState } from 'react'
import { useAuth } from '../hooks/useAuth'

interface GmailConnectionData {
  success: boolean
  email?: string
  messages_total?: number
  threads_total?: number
  error?: string
}

interface GmailMessage {
  id: string
  subject: string
  sender: string
  timestamp: string
  snippet: string
  body?: string
}

interface Integration {
  id: number
  provider: string
  email_address: string
  is_active: boolean
}

interface BankingAnalysis {
  total_messages: number
  date_range: {
    start: string
    end: string
  }
  senders: Record<string, number>
  integrations: Array<{ id: number; email_address: string }>
}

interface ProcessingResults {
  total_messages_found: number
  processed_messages: number
  potential_transactions: Array<{
    message_id: string
    sender: string
    subject: string
    timestamp: string
    transaction_data: Record<string, unknown>
  }>
  errors: Array<{ message_id: string; error: string }>
}

const GmailTestPage = () => {
  const { makeAuthenticatedRequest } = useAuth()
  const [activeTab, setActiveTab] = useState<'connection' | 'messages' | 'banking' | 'processing'>('connection')
  
  // Connection Test State
  const [connectionData, setConnectionData] = useState<GmailConnectionData | null>(null)
  const [connectionLoading, setConnectionLoading] = useState(false)
  
  // Messages State
  const [messages, setMessages] = useState<GmailMessage[]>([])
  const [messagesLoading, setMessagesLoading] = useState(false)
  const [messageFilters, setMessageFilters] = useState({ max_results: 20, days_back: 7 })
  
  // Banking Messages State
  const [bankingMessages, setBankingMessages] = useState<GmailMessage[]>([])
  const [bankingLoading, setBankingLoading] = useState(false)
  const [bankingFilters, setBankingFilters] = useState({ max_results: 50, days_back: 30 })
  const [bankingAnalysis, setBankingAnalysis] = useState<BankingAnalysis | null>(null)
  
  // Processing State
  const [processingResults, setProcessingResults] = useState<ProcessingResults | null>(null)
  const [processingLoading, setProcessingLoading] = useState(false)
  const [processingFilters, setProcessingFilters] = useState({ days_back: 30 })

  const testConnection = async () => {
    setConnectionLoading(true)
    try {
      // Get user integrations first to test connection
      const integrationsResponse = await makeAuthenticatedRequest('/api/core/integrations/')
      const integrationsData = await integrationsResponse.json()
      
      if (!integrationsData.results || !integrationsData.results.length) {
        setConnectionData({ success: false, error: 'No Gmail integrations found. Please connect your Gmail account first.' })
        setConnectionLoading(false)
        return
      }
      
      // Test connection for the first Gmail integration
      const gmailIntegration = integrationsData.results.find((integration: Integration) => integration.provider === 'gmail')
      if (!gmailIntegration) {
        setConnectionData({ success: false, error: 'No Gmail integration found. Please connect your Gmail account first.' })
        setConnectionLoading(false)
        return
      }
      
      const response = await makeAuthenticatedRequest(`/api/core/integrations/${gmailIntegration.id}/test_connection/`, {
        method: 'POST'
      })
      const data = await response.json()
      setConnectionData(data.data || data)
    } catch (error) {
      setConnectionData({ success: false, error: `Connection failed: ${error}` })
    }
    setConnectionLoading(false)
  }

  const fetchRecentMessages = async () => {
    setMessagesLoading(true)
    try {
      const params = new URLSearchParams({
        max_results: messageFilters.max_results.toString(),
        days_back: messageFilters.days_back.toString()
      })
      
      const response = await makeAuthenticatedRequest(`/api/core/gmail/messages/recent/?${params}`)
      const data = await response.json()
      
      if (data.success) {
        setMessages(data.messages)
      }
    } catch (error) {
      console.error('Error fetching messages:', error)
    }
    setMessagesLoading(false)
  }

  const fetchBankingMessages = async () => {
    setBankingLoading(true)
    try {
      const params = new URLSearchParams({
        max_results: bankingFilters.max_results.toString(),
        days_back: bankingFilters.days_back.toString()
      })
      
      const response = await makeAuthenticatedRequest(`/api/core/gmail/messages/banking/?${params}`)
      const data = await response.json()
      
      if (data.success) {
        setBankingMessages(data.messages)
        setBankingAnalysis(data.analysis)
      }
    } catch (error) {
      console.error('Error fetching banking messages:', error)
    }
    setBankingLoading(false)
  }

  const processMessages = async () => {
    setProcessingLoading(true)
    try {
      const response = await makeAuthenticatedRequest('/api/core/gmail/import/', {
        method: 'POST',
        body: JSON.stringify({
          days_back: processingFilters.days_back,
          process_all: false
        })
      })
      
      const data = await response.json()
      
      if (data.success) {
        setProcessingResults(data.results)
      }
    } catch (error) {
      console.error('Error processing messages:', error)
    }
    setProcessingLoading(false)
  }

  const tabs = [
    { id: 'connection', name: 'Connection Test', icon: '🔗' },
    { id: 'messages', name: 'Recent Messages', icon: '📧' },
    { id: 'banking', name: 'Banking Detection', icon: '🏦' },
    { id: 'processing', name: 'Transaction Processing', icon: '⚙️' }
  ]

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-2xl font-bold mb-2">Gmail API Testing</h2>
        <p className="text-gray-600">
          Test Gmail API integration, email detection, and transaction processing capabilities.
        </p>
      </div>

      {/* Tabs */}
      <div className="bg-white rounded-lg shadow">
        <div className="border-b border-gray-200">
          <nav className="-mb-px flex space-x-8 px-6">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as any)}
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
          {/* Connection Test Tab */}
          {activeTab === 'connection' && (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-medium">Test Gmail API Connection</h3>
                <button
                  onClick={testConnection}
                  disabled={connectionLoading}
                  className="btn-primary"
                >
                  {connectionLoading ? 'Testing...' : 'Test Connection'}
                </button>
              </div>

              {connectionData && (
                <div className={`p-4 rounded-lg ${
                  connectionData.success ? 'bg-green-50 border border-green-200' : 'bg-red-50 border border-red-200'
                }`}>
                  <div className="flex items-center mb-2">
                    <span className={`w-3 h-3 rounded-full mr-2 ${
                      connectionData.success ? 'bg-green-500' : 'bg-red-500'
                    }`}></span>
                    <h4 className="font-medium">
                      {connectionData.success ? 'Connection Successful' : 'Connection Failed'}
                    </h4>
                  </div>
                  
                  {connectionData.success ? (
                    <div className="space-y-1 text-sm text-gray-700">
                      <p><strong>Email:</strong> {connectionData.email}</p>
                      <p><strong>Total Messages:</strong> {connectionData.messages_total?.toLocaleString()}</p>
                      <p><strong>Total Threads:</strong> {connectionData.threads_total?.toLocaleString()}</p>
                    </div>
                  ) : (
                    <p className="text-sm text-red-700">{connectionData.error}</p>
                  )}
                </div>
              )}
            </div>
          )}

          {/* Recent Messages Tab */}
          {activeTab === 'messages' && (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-medium">Recent Gmail Messages</h3>
                <div className="flex items-center space-x-4">
                  <div className="flex items-center space-x-2">
                    <label className="text-sm text-gray-600">Max Results:</label>
                    <input
                      type="number"
                      value={messageFilters.max_results}
                      onChange={(e) => setMessageFilters({...messageFilters, max_results: parseInt(e.target.value) || 20})}
                      className="w-16 px-2 py-1 border rounded text-sm"
                      min="1"
                      max="100"
                    />
                  </div>
                  <div className="flex items-center space-x-2">
                    <label className="text-sm text-gray-600">Days Back:</label>
                    <input
                      type="number"
                      value={messageFilters.days_back}
                      onChange={(e) => setMessageFilters({...messageFilters, days_back: parseInt(e.target.value) || 7})}
                      className="w-16 px-2 py-1 border rounded text-sm"
                      min="1"
                      max="90"
                    />
                  </div>
                  <button
                    onClick={fetchRecentMessages}
                    disabled={messagesLoading}
                    className="btn-primary"
                  >
                    {messagesLoading ? 'Loading...' : 'Fetch Messages'}
                  </button>
                </div>
              </div>

              {messages.length > 0 && (
                <div className="space-y-3">
                  <p className="text-sm text-gray-600">Found {messages.length} messages</p>
                  {messages.map((message) => (
                    <div key={message.id} className="border rounded-lg p-4">
                      <div className="flex justify-between items-start mb-2">
                        <h4 className="font-medium truncate flex-1 mr-4">{message.subject || '(No Subject)'}</h4>
                        <span className="text-xs text-gray-500 whitespace-nowrap">
                          {new Date(message.timestamp).toLocaleDateString()}
                        </span>
                      </div>
                      <p className="text-sm text-gray-600 mb-2">From: {message.sender}</p>
                      <p className="text-sm text-gray-700">{message.snippet}</p>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Banking Detection Tab */}
          {activeTab === 'banking' && (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-medium">Banking Message Detection</h3>
                <div className="flex items-center space-x-4">
                  <div className="flex items-center space-x-2">
                    <label className="text-sm text-gray-600">Max Results:</label>
                    <input
                      type="number"
                      value={bankingFilters.max_results}
                      onChange={(e) => setBankingFilters({...bankingFilters, max_results: parseInt(e.target.value) || 50})}
                      className="w-16 px-2 py-1 border rounded text-sm"
                      min="1"
                      max="200"
                    />
                  </div>
                  <div className="flex items-center space-x-2">
                    <label className="text-sm text-gray-600">Days Back:</label>
                    <input
                      type="number"
                      value={bankingFilters.days_back}
                      onChange={(e) => setBankingFilters({...bankingFilters, days_back: parseInt(e.target.value) || 30})}
                      className="w-16 px-2 py-1 border rounded text-sm"
                      min="1"
                      max="90"
                    />
                  </div>
                  <button
                    onClick={fetchBankingMessages}
                    disabled={bankingLoading}
                    className="btn-primary"
                  >
                    {bankingLoading ? 'Detecting...' : 'Detect Banking'}
                  </button>
                </div>
              </div>

              {bankingAnalysis && (
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                  <h4 className="font-medium mb-2">Analysis Results</h4>
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <span className="text-gray-600">Total Messages:</span>
                      <span className="ml-2 font-medium">{bankingAnalysis.total_messages}</span>
                    </div>
                    <div>
                      <span className="text-gray-600">Unique Senders:</span>
                      <span className="ml-2 font-medium">{Object.keys(bankingAnalysis.senders).length}</span>
                    </div>
                  </div>
                  
                  {Object.keys(bankingAnalysis.senders).length > 0 && (
                    <div className="mt-3">
                      <p className="text-sm font-medium text-gray-700 mb-1">Top Senders:</p>
                      <div className="space-y-1">
                        {Object.entries(bankingAnalysis.senders)
                          .sort(([,a], [,b]) => (b as number) - (a as number))
                          .slice(0, 5)
                          .map(([sender, count]) => (
                            <div key={sender} className="text-xs text-gray-600">
                              <span className="font-mono">{sender}</span>
                              <span className="ml-2 text-blue-600">({count} messages)</span>
                            </div>
                          ))}
                      </div>
                    </div>
                  )}
                </div>
              )}

              {bankingMessages.length > 0 && (
                <div className="space-y-3">
                  <p className="text-sm text-gray-600">Found {bankingMessages.length} potential banking messages</p>
                  {bankingMessages.map((message) => (
                    <div key={message.id} className="border rounded-lg p-4 bg-yellow-50">
                      <div className="flex justify-between items-start mb-2">
                        <h4 className="font-medium truncate flex-1 mr-4">{message.subject || '(No Subject)'}</h4>
                        <span className="text-xs text-gray-500 whitespace-nowrap">
                          {new Date(message.timestamp).toLocaleDateString()}
                        </span>
                      </div>
                      <p className="text-sm text-gray-600 mb-2">From: {message.sender}</p>
                      <p className="text-sm text-gray-700">{message.snippet}</p>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Transaction Processing Tab */}
          {activeTab === 'processing' && (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-medium">Transaction Processing</h3>
                <div className="flex items-center space-x-4">
                  <div className="flex items-center space-x-2">
                    <label className="text-sm text-gray-600">Days Back:</label>
                    <input
                      type="number"
                      value={processingFilters.days_back}
                      onChange={(e) => setProcessingFilters({...processingFilters, days_back: parseInt(e.target.value) || 30})}
                      className="w-16 px-2 py-1 border rounded text-sm"
                      min="1"
                      max="90"
                    />
                  </div>
                  <button
                    onClick={processMessages}
                    disabled={processingLoading}
                    className="btn-primary"
                  >
                    {processingLoading ? 'Processing...' : 'Process Transactions'}
                  </button>
                </div>
              </div>

              {processingResults && (
                <div className="space-y-4">
                  <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                    <h4 className="font-medium mb-2">Processing Summary</h4>
                    <div className="grid grid-cols-3 gap-4 text-sm">
                      <div>
                        <span className="text-gray-600">Messages Found:</span>
                        <span className="ml-2 font-medium">{processingResults.total_messages_found}</span>
                      </div>
                      <div>
                        <span className="text-gray-600">Processed:</span>
                        <span className="ml-2 font-medium">{processingResults.processed_messages}</span>
                      </div>
                      <div>
                        <span className="text-gray-600">Transactions:</span>
                        <span className="ml-2 font-medium text-green-600">{processingResults.potential_transactions.length}</span>
                      </div>
                    </div>
                  </div>

                  {processingResults.potential_transactions.length > 0 && (
                    <div className="space-y-3">
                      <h4 className="font-medium">Extracted Transactions</h4>
                      {processingResults.potential_transactions.map((transaction, index) => (
                        <div key={transaction.message_id} className="border rounded-lg p-4 bg-green-50">
                          <div className="flex justify-between items-start mb-2">
                            <h5 className="font-medium truncate flex-1 mr-4">{transaction.subject}</h5>
                            <span className="text-xs text-gray-500 whitespace-nowrap">
                              {new Date(transaction.timestamp).toLocaleDateString()}
                            </span>
                          </div>
                          <p className="text-sm text-gray-600 mb-2">From: {transaction.sender}</p>
                          
                          <div className="bg-white rounded p-3 text-sm">
                            <h6 className="font-medium mb-1">Transaction Data:</h6>
                            <pre className="text-xs text-gray-700 whitespace-pre-wrap">
                              {JSON.stringify(transaction.transaction_data, null, 2)}
                            </pre>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}

                  {processingResults.errors.length > 0 && (
                    <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                      <h4 className="font-medium text-red-800 mb-2">Processing Errors ({processingResults.errors.length})</h4>
                      <div className="space-y-2">
                        {processingResults.errors.slice(0, 5).map((error, index) => (
                          <div key={index} className="text-sm text-red-700">
                            <span className="font-mono">{error.message_id}:</span>
                            <span className="ml-2">{error.error}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default GmailTestPage 