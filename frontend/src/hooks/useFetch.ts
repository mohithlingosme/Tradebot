import { useQuery, useMutation, useQueryClient } from 'react-query';
import { api } from '../lib/api';

export const useFetch = () => {
  const queryClient = useQueryClient();

  const fetchData = (key: string, url: string, options?: any) => {
    return useQuery(key, () => api.get(url, options), {
      staleTime: 5 * 60 * 1000, // 5 minutes
      cacheTime: 10 * 60 * 1000, // 10 minutes
    });
  };

  const mutateData = (url: string, method: 'post' | 'put' | 'delete' = 'post') => {
    return useMutation((data: any) => api[method](url, data), {
      onSuccess: () => {
        queryClient.invalidateQueries();
      },
    });
  };

  return { fetchData, mutateData };
};
