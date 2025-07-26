import React from 'react';
import { Card, Tag, Typography, Space, Button } from 'antd';
import { CalendarOutlined, CheckCircleOutlined, ClockCircleOutlined } from '@ant-design/icons';
import { ExamPlan, ExamPlanStatus, ExamCategory } from '../types';
import dayjs from 'dayjs';

const { Title, Text } = Typography;

interface ExamPlanCardProps {
  plan: ExamPlan;
  onView: (plan: ExamPlan) => void;
  onApprove?: (plan: ExamPlan) => void;
}

const statusConfig = {
  [ExamPlanStatus.DRAFT]: { color: 'default', text: '초안' },
  [ExamPlanStatus.PENDING_APPROVAL]: { color: 'warning', text: '승인 대기' },
  [ExamPlanStatus.APPROVED]: { color: 'success', text: '승인됨' },
  [ExamPlanStatus.IN_PROGRESS]: { color: 'processing', text: '진행 중' },
  [ExamPlanStatus.COMPLETED]: { color: 'success', text: '완료' },
  [ExamPlanStatus.CANCELLED]: { color: 'error', text: '취소됨' },
};

const categoryConfig = {
  [ExamCategory.GENERAL]: { text: '일반건강진단' },
  [ExamCategory.SPECIAL]: { text: '특수건강진단' },
  [ExamCategory.PLACEMENT]: { text: '배치전건강진단' },
  [ExamCategory.RETURN_TO_WORK]: { text: '복직건강진단' },
};

export const ExamPlanCard: React.FC<ExamPlanCardProps> = ({ plan, onView, onApprove }) => {
  const status = statusConfig[plan.plan_status];
  const category = categoryConfig[plan.category];

  return (
    <Card
      hoverable
      onClick={() => onView(plan)}
      extra={
        <Space>
          {plan.plan_status === ExamPlanStatus.PENDING_APPROVAL && onApprove && (
            <Button 
              type="primary" 
              size="small" 
              icon={<CheckCircleOutlined />}
              onClick={(e) => {
                e.stopPropagation();
                onApprove(plan);
              }}
            >
              승인
            </Button>
          )}
          <Tag color={status.color}>{status.text}</Tag>
        </Space>
      }
    >
      <Space direction="vertical" size={8} style={{ width: '100%' }}>
        <Title level={5}>{plan.year}년 {category.text}</Title>
        
        <Space size={16}>
          <Text type="secondary">
            <CalendarOutlined /> 생성일: {dayjs(plan.created_at).format('YYYY-MM-DD')}
          </Text>
          {plan.approved_at && (
            <Text type="secondary">
              <CheckCircleOutlined /> 승인일: {dayjs(plan.approved_at).format('YYYY-MM-DD')}
            </Text>
          )}
        </Space>

        {plan.plan_status === ExamPlanStatus.IN_PROGRESS && (
          <Text>
            <ClockCircleOutlined /> 현재 진행 중인 건강검진 계획입니다.
          </Text>
        )}
      </Space>
    </Card>
  );
};