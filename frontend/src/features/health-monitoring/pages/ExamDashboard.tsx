import React from 'react';
import { Row, Col, Card, Statistic, Typography, Spin, Alert } from 'antd';
import { 
  TeamOutlined, 
  CheckCircleOutlined, 
  ClockCircleOutlined, 
  ExclamationCircleOutlined 
} from '@ant-design/icons';
import { useExamStats } from '../hooks/useExamStats';
import { ExamPlanCard } from '../components/ExamPlanCard';
import { WorkerExamStatusTable } from '../components/WorkerExamStatusTable';
import { useExamPlans } from '../hooks/useExamPlans';
import { useQuery } from '@tanstack/react-query';
import { healthExamApi } from '../services/healthExamApi';

const { Title } = Typography;

export const ExamDashboard: React.FC = () => {
  const currentYear = new Date().getFullYear();
  const { data: stats, isLoading: statsLoading } = useExamStats(currentYear);
  const { data: plans = [], isLoading: plansLoading } = useExamPlans(currentYear);
  const { data: workerStatuses = [], isLoading: workersLoading } = useQuery({
    queryKey: ['workerStatuses'],
    queryFn: () => healthExamApi.getWorkerStatuses(),
  });

  if (statsLoading || plansLoading) {
    return (
      <div style={{ textAlign: 'center', padding: '50px' }}>
        <Spin size="large" />
      </div>
    );
  }

  const activePlans = plans.filter(plan => 
    ['approved', 'in_progress'].includes(plan.plan_status)
  );

  const overdueWorkers = workerStatuses.filter(w => w.exam_status === 'overdue');

  return (
    <div>
      <Title level={2}>건강검진 관리 대시보드</Title>
      
      {/* Statistics Cards */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={12} sm={12} md={6}>
          <Card>
            <Statistic
              title="전체 근로자"
              value={stats?.total_workers || 0}
              prefix={<TeamOutlined />}
            />
          </Card>
        </Col>
        <Col xs={12} sm={12} md={6}>
          <Card>
            <Statistic
              title="검진 완료"
              value={stats?.completed_exams || 0}
              prefix={<CheckCircleOutlined />}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col xs={12} sm={12} md={6}>
          <Card>
            <Statistic
              title="검진 예정"
              value={stats?.scheduled_exams || 0}
              prefix={<ClockCircleOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col xs={12} sm={12} md={6}>
          <Card>
            <Statistic
              title="기한 초과"
              value={stats?.overdue_exams || 0}
              prefix={<ExclamationCircleOutlined />}
              valueStyle={{ color: '#f5222d' }}
            />
          </Card>
        </Col>
      </Row>

      {/* Alert for overdue exams */}
      {overdueWorkers.length > 0 && (
        <Alert
          message={`${overdueWorkers.length}명의 근로자가 건강검진 기한을 초과했습니다.`}
          description="즉시 건강검진 일정을 예약해주세요."
          type="warning"
          showIcon
          closable
          style={{ marginBottom: 24 }}
        />
      )}

      {/* Active Plans */}
      <Title level={4} style={{ marginBottom: 16 }}>진행 중인 검진 계획</Title>
      <Row gutter={[16, 16]} style={{ marginBottom: 32 }}>
        {activePlans.length > 0 ? (
          activePlans.map(plan => (
            <Col xs={24} md={12} lg={8} key={plan.id}>
              <ExamPlanCard 
                plan={plan} 
                onView={(plan) => console.log('View plan:', plan)}
              />
            </Col>
          ))
        ) : (
          <Col span={24}>
            <Card>
              <Alert
                message="진행 중인 검진 계획이 없습니다"
                description="새로운 건강검진 계획을 생성해주세요."
                type="info"
                showIcon
              />
            </Card>
          </Col>
        )}
      </Row>

      {/* Worker Status Table */}
      <Title level={4} style={{ marginBottom: 16 }}>근로자 검진 현황</Title>
      <Card>
        <WorkerExamStatusTable 
          data={workerStatuses} 
          loading={workersLoading}
        />
      </Card>
    </div>
  );
};

export default ExamDashboard;