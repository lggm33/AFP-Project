import { useState, useEffect, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'

interface User {
  id: number
  username: string
  email: string
  first_name: string
  last_name: string
  providers: Array<{
    provider: string
    uid: string
    extra_data: Record<string, unknown>
  }>
}

interface AuthState {
  user: User | null
  isAuthenticated: boolean
  isLoading: boolean
  error: string | null
}

const API_BASE_URL = 'http://127.0.0.1:8000'

// Token storage keys
const ACCESS_TOKEN_KEY = 'afp_access_token'
const REFRESH_TOKEN_KEY = 'afp_refresh_token'
const USER_KEY = 'afp_user'

export const useAuth = () => {
  const navigate = useNavigate()
  const [authState, setAuthState] = useState<AuthState>({
    user: null,
    isAuthenticated: false,
    isLoading: true,
    error: null
  })

  // Get stored tokens
  const getStoredTokens = useCallback(() => {
    const accessToken = localStorage.getItem(ACCESS_TOKEN_KEY)
    const refreshToken = localStorage.getItem(REFRESH_TOKEN_KEY)
    const userString = localStorage.getItem(USER_KEY)
    
    return {
      accessToken,
      refreshToken,
      user: userString ? JSON.parse(userString) : null
    }
  }, [])

  // Store tokens securely
  const storeTokens = useCallback((accessToken: string, refreshToken: string, user: User) => {
    localStorage.setItem(ACCESS_TOKEN_KEY, accessToken)
    localStorage.setItem(REFRESH_TOKEN_KEY, refreshToken)
    localStorage.setItem(USER_KEY, JSON.stringify(user))
  }, [])

  // Clear all stored data
  const clearAuth = useCallback(() => {
    localStorage.removeItem(ACCESS_TOKEN_KEY)
    localStorage.removeItem(REFRESH_TOKEN_KEY)
    localStorage.removeItem(USER_KEY)
    // Clear any other auth-related data
    localStorage.removeItem('afp_social_accounts')
  }, [])

  // Make authenticated API request
  const makeAuthenticatedRequest = useCallback(async (url: string, options: RequestInit = {}) => {
    const { accessToken } = getStoredTokens()
    
    if (!accessToken) {
      throw new Error('No access token available')
    }

    const response = await fetch(`${API_BASE_URL}${url}`, {
      ...options,
      headers: {
        'Authorization': `Bearer ${accessToken}`,
        'Content-Type': 'application/json',
        ...options.headers,
      },
    })

    // If token is expired, try to refresh
    if (response.status === 401) {
      const refreshSuccess = await refreshTokens()
      if (refreshSuccess) {
        // Retry the request with new token
        const { accessToken: newAccessToken } = getStoredTokens()
        return fetch(`${API_BASE_URL}${url}`, {
          ...options,
          headers: {
            'Authorization': `Bearer ${newAccessToken}`,
            'Content-Type': 'application/json',
            ...options.headers,
          },
        })
      } else {
        throw new Error('Authentication expired')
      }
    }

    return response
  }, [getStoredTokens])

  // Refresh access token using refresh token
  const refreshTokens = useCallback(async (): Promise<boolean> => {
    try {
      const { refreshToken } = getStoredTokens()
      
      if (!refreshToken) {
        return false
      }

      const response = await fetch(`${API_BASE_URL}/api/auth/refresh/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          refresh_token: refreshToken
        })
      })

      if (response.ok) {
        const data = await response.json()
        const { user } = getStoredTokens()
        
        if (user) {
          storeTokens(data.access_token, data.refresh_token, user)
          return true
        }
      }
      
      return false
    } catch (error) {
      console.error('Token refresh failed:', error)
      return false
    }
  }, [getStoredTokens, storeTokens])

  // Check authentication status
  const checkAuth = useCallback(async () => {
    try {
      setAuthState(prev => ({ ...prev, isLoading: true, error: null }))
      
      const { accessToken, user: storedUser } = getStoredTokens()
      
      if (!accessToken || !storedUser) {
        setAuthState({
          user: null,
          isAuthenticated: false,
          isLoading: false,
          error: null
        })
        return
      }

      // Verify token is still valid
      const response = await makeAuthenticatedRequest('/api/users/me/')
      
      if (response.ok) {
        const userData = await response.json()
        setAuthState({
          user: userData,
          isAuthenticated: true,
          isLoading: false,
          error: null
        })
      } else {
        // Token invalid, clear auth
        clearAuth()
        setAuthState({
          user: null,
          isAuthenticated: false,
          isLoading: false,
          error: 'Session expired'
        })
      }
    } catch (error) {
      console.error('Auth check failed:', error)
      clearAuth()
      setAuthState({
        user: null,
        isAuthenticated: false,
        isLoading: false,
        error: error instanceof Error ? error.message : 'Authentication failed'
      })
    }
  }, [getStoredTokens, makeAuthenticatedRequest, clearAuth])

  // Login with tokens (called from OAuth callback)
  const loginWithTokens = useCallback((accessToken: string, refreshToken: string, userData: {
    user_id?: number
    id?: number
    username: string
    email: string
    first_name?: string
    last_name?: string
    providers?: string
  }) => {
    const user: User = {
      id: userData.user_id || userData.id || 0,
      username: userData.username,
      email: userData.email,
      first_name: userData.first_name || '',
      last_name: userData.last_name || '',
      providers: userData.providers ? userData.providers.split(',').map((p: string) => ({ provider: p, uid: '', extra_data: {} })) : []
    }
    
    storeTokens(accessToken, refreshToken, user)
    setAuthState({
      user,
      isAuthenticated: true,
      isLoading: false,
      error: null
    })
  }, [storeTokens])

  // Logout function
  const logout = useCallback(async () => {
    try {
      const { refreshToken } = getStoredTokens()
      
      // Call backend logout endpoint to blacklist token
      if (refreshToken) {
        try {
          await makeAuthenticatedRequest('/api/auth/logout/', {
            method: 'POST',
            body: JSON.stringify({
              refresh_token: refreshToken
            })
          })
        } catch (error) {
          // Even if backend logout fails, we still clear local data
          console.warn('Backend logout failed, clearing local auth data:', error)
        }
      }
      
      // Clear local auth data
      clearAuth()
      setAuthState({
        user: null,
        isAuthenticated: false,
        isLoading: false,
        error: null
      })
      
      // Redirect to login
      navigate('/login')
      
    } catch (error) {
      console.error('Logout error:', error)
      // Still clear local data even if API call fails
      clearAuth()
      setAuthState({
        user: null,
        isAuthenticated: false,
        isLoading: false,
        error: null
      })
      navigate('/login')
    }
  }, [getStoredTokens, makeAuthenticatedRequest, clearAuth, navigate])

  // Initialize auth on hook mount
  useEffect(() => {
    checkAuth()
  }, [checkAuth])

  // Auto-refresh tokens periodically (every 30 minutes)
  useEffect(() => {
    if (!authState.isAuthenticated) return

    const interval = setInterval(async () => {
      try {
        await refreshTokens()
      } catch (error) {
        console.error('Auto-refresh failed:', error)
      }
    }, 30 * 60 * 1000) // 30 minutes

    return () => clearInterval(interval)
  }, [authState.isAuthenticated, refreshTokens])

  return {
    ...authState,
    loginWithTokens,
    logout,
    checkAuth,
    refreshTokens,
    makeAuthenticatedRequest
  }
} 