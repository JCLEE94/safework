import { useState, useCallback } from 'react';
import { API_BASE_URL } from '../constants';

interface ApiOptions extends RequestInit {
  params?: Record<string, string>;
}

export function useApi() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const fetchApi = useCallback(async <T = any>(
    endpoint: string,
    options: ApiOptions = {}
  ): Promise<T> => {
    const { params, ...fetchOptions } = options;
    
    try {
      setLoading(true);
      setError(null);
      
      let url = `${API_BASE_URL}/api/v1${endpoint}`;
      
      if (params) {
        const searchParams = new URLSearchParams(params);
        url += `?${searchParams.toString()}`;
      }
      
      const response = await fetch(url, {
        ...fetchOptions,
        headers: {
          'Content-Type': 'application/json',
          ...fetchOptions.headers,
        },
      });
      
      if (!response.ok) {
        throw new Error(`API Error: ${response.status} ${response.statusText}`);
      }
      
      const data = await response.json();
      return data;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : '알 수 없는 오류가 발생했습니다.';
      setError(errorMessage);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);
  
  return { fetchApi, loading, error };
}