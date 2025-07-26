import { useQuery } from '@tanstack/react-query';
import { healthExamApi } from '../services/healthExamApi';

export const useExamStats = (year?: number) => {
  return useQuery({
    queryKey: ['examStats', year],
    queryFn: () => healthExamApi.getExamStats(year),
    refetchInterval: 1000 * 60 * 5, // Refetch every 5 minutes
  });
};