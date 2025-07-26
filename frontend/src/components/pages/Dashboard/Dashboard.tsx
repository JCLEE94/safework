import React from 'react';
import { Row, Col, Card, Statistic, Progress, Timeline, List, Tag, Space, Typography } from 'antd';
import {
  MedicineBoxOutlined,
  AlertOutlined,
  CheckCircleOutlined,
  ClockCircleOutlined,
  SafetyOutlined,
  TeamOutlined,
} from '@ant-design/icons';
import styled from 'styled-components';
import { designTokens } from '../../../styles/theme';
import { quickActions } from '../../../constants/navigation';

const { Title, Text } = Typography;

const DashboardContainer = styled.div`
  .welcome-section {
    margin-bottom: ${designTokens.spacing.lg}px;
  }
  
  .quick-actions {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
    gap: ${designTokens.spacing.md}px;
    margin-bottom: ${designTokens.spacing.xl}px;
  }
  
  .stat-card {
    cursor: pointer;
    transition: all ${designTokens.transitions.base};
    
    &:hover {
      transform: translateY(-4px);
      box-shadow: ${designTokens.shadows.lg};
    }
  }
  
  .timeline-card {
    .ant-timeline-item-content {
      cursor: pointer;
      
      &:hover {
        color: ${designTokens.colors.primary[600]};
      }
    }
  }
`;

const QuickActionCard = styled(Card)`
  text-align: center;
  cursor: pointer;
  transition: all ${designTokens.transitions.base};
  border: 2px solid transparent;
  
  &:hover {
    border-color: ${props => props.color || designTokens.colors.primary[500]};
    transform: translateY(-2px);
    box-shadow: ${designTokens.shadows.md};
  }
  
  .anticon {
    font-size: 32px;
    color: ${props => props.color || designTokens.colors.primary[500]};
    margin-bottom: ${designTokens.spacing.sm}px;
  }
`;

const StatusTag = styled(Tag)`
  border-radius: ${designTokens.borderRadius.full}px;
  padding: 2px 12px;
  font-weight: ${designTokens.typography.fontWeight.medium};
`;

// 더미 데이터
const statistics = {
  totalWorkers: 245,
  activeWorkers: 238,
  pendingExams: 12,
  monthlyAccidents: 2,
  completionRate: 94.5,
};

const recentActivities = [
  {
    time: '10:30',
    content: '김철수 근로자 건강진단 완료',
    type: 'success',
  },
  {
    time: '09:45',
    content: '3층 작업장 안전점검 실시',
    type: 'info',
  },
  {
    time: '09:00',
    content: '신규 근로자 5명 안전교육 예정',
    type: 'warning',
  },
  {
    time: '어제',
    content: '월간 보건관리 보고서 작성 완료',
    type: 'success',
  },
];

const upcomingTasks = [
  {
    title: '정기 건강진단',
    description: '15명 대상',
    date: '2025-08-15',
    status: 'pending',
  },
  {
    title: '안전보건교육',
    description: '신규 입사자 대상',
    date: '2025-08-10',
    status: 'scheduled',
  },
  {
    title: '작업환경측정',
    description: '2공장 전 구역',
    date: '2025-08-20',
    status: 'pending',
  },
];

export const Dashboard: React.FC = () => {
  return (
    <DashboardContainer>
      <div className="welcome-section">
        <Title level={2}>안녕하세요, 홍길동님</Title>
        <Text type="secondary">오늘도 안전한 작업장을 만들어갑니다</Text>
      </div>

      <div className="quick-actions">
        {quickActions.map(action => (
          <QuickActionCard
            key={action.key}
            size="small"
            color={action.color}
            onClick={() => console.log('Navigate to:', action.path)}
          >
            {action.icon}
            <div>{action.label}</div>
          </QuickActionCard>
        ))}
      </div>

      <Row gutter={[16, 16]}>
        <Col xs={24} sm={12} lg={6}>
          <Card className="stat-card">
            <Statistic
              title="전체 근로자"
              value={statistics.totalWorkers}
              suffix="명"
              prefix={<TeamOutlined />}
            />
            <Progress
              percent={(statistics.activeWorkers / statistics.totalWorkers) * 100}
              showInfo={false}
              strokeColor={designTokens.colors.primary[500]}
            />
            <Text type="secondary">활동: {statistics.activeWorkers}명</Text>
          </Card>
        </Col>
        
        <Col xs={24} sm={12} lg={6}>
          <Card className="stat-card">
            <Statistic
              title="검진 대기"
              value={statistics.pendingExams}
              suffix="건"
              prefix={<MedicineBoxOutlined />}
              valueStyle={{ color: designTokens.colors.warning[600] }}
            />
          </Card>
        </Col>
        
        <Col xs={24} sm={12} lg={6}>
          <Card className="stat-card">
            <Statistic
              title="월간 사고"
              value={statistics.monthlyAccidents}
              suffix="건"
              prefix={<AlertOutlined />}
              valueStyle={{ color: designTokens.colors.error[600] }}
            />
          </Card>
        </Col>
        
        <Col xs={24} sm={12} lg={6}>
          <Card className="stat-card">
            <Statistic
              title="교육 이수율"
              value={statistics.completionRate}
              suffix="%"
              prefix={<CheckCircleOutlined />}
              valueStyle={{ color: designTokens.colors.success[600] }}
            />
          </Card>
        </Col>
      </Row>

      <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
        <Col xs={24} lg={12}>
          <Card
            title="최근 활동"
            extra={<a href="#">전체보기</a>}
            className="timeline-card"
          >
            <Timeline>
              {recentActivities.map((activity, index) => (
                <Timeline.Item
                  key={index}
                  color={
                    activity.type === 'success' ? 'green' :
                    activity.type === 'warning' ? 'orange' :
                    'blue'
                  }
                >
                  <Space direction="vertical" size={0}>
                    <Text type="secondary">{activity.time}</Text>
                    <Text>{activity.content}</Text>
                  </Space>
                </Timeline.Item>
              ))}
            </Timeline>
          </Card>
        </Col>
        
        <Col xs={24} lg={12}>
          <Card
            title="예정된 작업"
            extra={<a href="#">전체보기</a>}
          >
            <List
              dataSource={upcomingTasks}
              renderItem={task => (
                <List.Item
                  actions={[
                    <StatusTag
                      color={task.status === 'scheduled' ? 'blue' : 'orange'}
                    >
                      {task.status === 'scheduled' ? '예정' : '대기'}
                    </StatusTag>
                  ]}
                >
                  <List.Item.Meta
                    avatar={
                      task.title.includes('건강진단') ? <MedicineBoxOutlined /> :
                      task.title.includes('교육') ? <SafetyOutlined /> :
                      <ClockCircleOutlined />
                    }
                    title={task.title}
                    description={
                      <Space size="small">
                        <Text type="secondary">{task.description}</Text>
                        <Text type="secondary">•</Text>
                        <Text type="secondary">{task.date}</Text>
                      </Space>
                    }
                  />
                </List.Item>
              )}
            />
          </Card>
        </Col>
      </Row>
    </DashboardContainer>
  );
};