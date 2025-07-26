import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { healthExamApi } from '../services/healthExamApi';
import { ExamPlan } from '../types';

export const useExamPlans = (year?: number) => {
  return useQuery({
    queryKey: ['examPlans', year],
    queryFn: () => healthExamApi.getPlans({ year }),
    select: (data) => data.filter(plan => plan.plan_status !== 'cancelled'),
  });
};

export const useCreateExamPlan = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (data: Omit<ExamPlan, 'id' | 'created_at' | 'updated_at'>) => 
      healthExamApi.createPlan(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['examPlans'] });
    },
  });
};

export const useApprovePlan = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (planId: number) => healthExamApi.approvePlan(planId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['examPlans'] });
    },
  });
};