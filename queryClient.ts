/**
 * React Query Client Configuration
 * Handles caching and state management for API calls
 */
import { QueryClient } from '@tanstack/react-query';

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      // Retry failed requests
      retry: 1,
      
      // Refetch on window focus
      refetchOnWindowFocus: false,
      
      // Stale time: 5 minutes
      staleTime: 5 * 60 * 1000,
      
      // Cache time: 10 minutes
      gcTime: 10 * 60 * 1000,
      
      // Error handling
      onError: (error) => {
        console.error('Query error:', error);
      }
    },
    mutations: {
      // Retry failed mutations
      retry: 0,
      
      // Error handling
      onError: (error) => {
        console.error('Mutation error:', error);
      }
    }
  }
});
