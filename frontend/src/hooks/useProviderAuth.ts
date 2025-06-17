import { useState, useCallback } from 'react';
import { useAuth } from './useAuth';

interface ProviderTokenStatus {
  status: 'active' | 'expired' | 'revoked' | 'error';
  expiresAt?: string;
  refreshedAt?: string;
  errorMessage?: string;
}

export const useProviderAuth = (integrationId: string) => {
  const { makeAuthenticatedRequest } = useAuth();
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [tokenStatus, setTokenStatus] = useState<ProviderTokenStatus | null>(null);

  const refreshTokens = useCallback(async () => {
    if (integrationId === '0') return null;
    
    try {
      setIsRefreshing(true);
      const response = await makeAuthenticatedRequest(
        `/api/core/integrations/${integrationId}/refresh-tokens/`,
        {
          method: 'POST',
        }
      );
      const data = await response.json();
      setTokenStatus(data);
      return data;
    } catch (error) {
      console.error('Error refreshing provider tokens:', error);
      throw error;
    } finally {
      setIsRefreshing(false);
    }
  }, [integrationId, makeAuthenticatedRequest]);

  const getTokenStatus = useCallback(async () => {
    if (integrationId === '0') return null;
    
    try {
      const response = await makeAuthenticatedRequest(
        `/api/core/integrations/${integrationId}/token-status/`,
        {
          method: 'GET',
        }
      );
      const data = await response.json();
      setTokenStatus(data);
      return data;
    } catch (error) {
      console.error('Error getting provider token status:', error);
      throw error;
    }
  }, [integrationId, makeAuthenticatedRequest]);

  const revokeTokens = useCallback(async () => {
    if (integrationId === '0') return null;
    
    try {
      const response = await makeAuthenticatedRequest(
        `/api/core/integrations/${integrationId}/revoke-tokens/`,
        {
          method: 'POST',
        }
      );
      const data = await response.json();
      setTokenStatus(data);
      return data;
    } catch (error) {
      console.error('Error revoking provider tokens:', error);
      throw error;
    }
  }, [integrationId, makeAuthenticatedRequest]);

  return {
    isRefreshing,
    tokenStatus,
    refreshTokens,
    getTokenStatus,
    revokeTokens,
  };
}; 