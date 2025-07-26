import React from 'react';
import { Row, Col, Card, Statistic, Progress, Typography, Space, List, Tag } from 'antd';
import { 
  UserOutlined, 
  MedicineBoxOutlined, 
  WarningOutlined, 
  BookOutlined,
  SafetyOutlined,
  FileProtectOutlined,
  RiseOutlined,
  FallOutlined
} from '@ant-design/icons';
import { useQuery } from '@tanstack/react-query';
import { dashboardApi } from '@/services/api/dashboard';
import { formatDate } from '@/utils/formatters';

const { Title, Text } = Typography;

const Dashboard: React.FC = () => {
  // 대시보드 통계
  const { data: stats } = useQuery({
    queryKey: ['dashboard-stats'],
    queryFn: () => dashboardApi.getStats(),
  });

  // 최근 활동
  const { data: recentActivities } = useQuery({
    queryKey: ['recent-activities'],
    queryFn: () => dashboardApi.getRecentActivities(),
  });

  // 다가오는 일정
  const { data: upcomingSchedules } = useQuery({
    queryKey: ['upcoming-schedules'],
    queryFn: () => dashboardApi.getUpcomingSchedules(),
  });

  return (
    <div>
      <Title level={2}>대시보드</Title>

      {/* 주요 지표 */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="전체 근로자"
              value={stats?.total_workers || 0}
              suffix="명"
              prefix={<UserOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
            <div style={{ marginTop: 8 }}>
              <Text type="secondary">전월 대비</Text>
              <span style={{ marginLeft: 8, color: (stats?.worker_change || 0) >= 0 ? '#52c41a' : '#f5222d' }}>
                {(stats?.worker_change || 0) >= 0 ? <RiseOutlined /> : <FallOutlined />}
                {Math.abs(stats?.worker_change || 0)}명
              </span>
            </div>
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="건강검진 대상"
              value={stats?.pending_health_exams || 0}
              suffix="명"
              prefix={<MedicineBoxOutlined />}
              valueStyle={{ color: '#fa8c16' }}
            />
            <Progress 
              percent={stats?.health_exam_completion_rate || 0} 
              size="small" 
              showInfo={false}
              strokeColor="#fa8c16"
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="월간 사고"
              value={stats?.monthly_accidents || 0}
              suffix="건"
              prefix={<WarningOutlined />}
              valueStyle={{ color: (stats?.monthly_accidents || 0) > 0 ? '#f5222d' : '#52c41a' }}
            />
            <div style={{ marginTop: 8 }}>
              <Text type="secondary">LTIFR</Text>
              <span style={{ marginLeft: 8 }}>{stats?.ltifr || 0}</span>
            </div>
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="법규 준수율"
              value={stats?.compliance_rate || 0}
              suffix="%"
              prefix={<SafetyOutlined />}
              valueStyle={{ 
                color: (stats?.compliance_rate || 0) >= 95 ? '#52c41a' : 
                       (stats?.compliance_rate || 0) >= 80 ? '#faad14' : '#f5222d' 
              }}
            />
            <Progress 
              percent={stats?.compliance_rate || 0} 
              size="small" 
              showInfo={false}
              strokeColor={
                (stats?.compliance_rate || 0) >= 95 ? '#52c41a' : 
                (stats?.compliance_rate || 0) >= 80 ? '#faad14' : '#f5222d'
              }
            />
          </Card>
        </Col>
      </Row>

      {/* 두 번째 줄 지표 */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Space direction="vertical" style={{ width: '100%' }}>
              <Space>
                <BookOutlined style={{ fontSize: 20, color: '#722ed1' }} />
                <Text strong>교육 이수율</Text>
              </Space>
              <Statistic 
                value={stats?.education_completion_rate || 0} 
                suffix="%" 
                valueStyle={{ fontSize: 24 }}
              />
              <Text type="secondary">
                {stats?.completed_educations || 0}/{stats?.total_educations || 0}명 완료
              </Text>
            </Space>
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Space direction="vertical" style={{ width: '100%' }}>
              <Space>
                <FileProtectOutlined style={{ fontSize: 20, color: '#13c2c2' }} />
                <Text strong>작업환경측정</Text>
              </Space>
              <Statistic 
                value={stats?.work_environment_status || 0} 
                suffix="%" 
                valueStyle={{ fontSize: 24 }}
              />
              <Text type="secondary">다음 측정일: {formatDate(stats?.next_measurement_date)}</Text>
            </Space>
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Space direction="vertical" style={{ width: '100%' }}>
              <Text strong>특수건강진단 대상</Text>
              <Statistic 
                value={stats?.special_exam_targets || 0} 
                suffix="명" 
                valueStyle={{ fontSize: 24 }}
              />
              <Tag color="orange">주의 필요</Tag>
            </Space>
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Space direction="vertical" style={{ width: '100%' }}>
              <Text strong>MSDS 등록</Text>
              <Statistic 
                value={stats?.msds_registered || 0} 
                suffix="종" 
                valueStyle={{ fontSize: 24 }}
              />
              <Text type="secondary">미등록: {stats?.msds_pending || 0}종</Text>
            </Space>
          </Card>
        </Col>
      </Row>

      <Row gutter={[16, 16]}>
        {/* 최근 활동 */}
        <Col xs={24} md={12}>
          <Card title="최근 활동" style={{ height: 400 }}>
            <List
              size="small"
              dataSource={(recentActivities || []) as any[]}
              renderItem={(item) => (
                <List.Item>
                  <List.Item.Meta
                    avatar={
                      <Tag color={
                        item.type === 'exam' ? 'blue' :
                        item.type === 'accident' ? 'red' :
                        item.type === 'education' ? 'green' :
                        'default'
                      }>
                        {item.type === 'exam' ? '검진' :
                         item.type === 'accident' ? '사고' :
                         item.type === 'education' ? '교육' :
                         '기타'}
                      </Tag>
                    }
                    title={item.title}
                    description={
                      <Space direction="vertical" size={0}>
                        <Text type="secondary" style={{ fontSize: 12 }}>
                          {item.description}
                        </Text>
                        <Text type="secondary" style={{ fontSize: 12 }}>
                          {formatDate(item.created_at, 'YYYY-MM-DD HH:mm')}
                        </Text>
                      </Space>
                    }
                  />
                </List.Item>
              )}
            />
          </Card>
        </Col>

        {/* 다가오는 일정 */}
        <Col xs={24} md={12}>
          <Card title="다가오는 일정" style={{ height: 400 }}>
            <List
              size="small"
              dataSource={(upcomingSchedules || []) as any[]}
              renderItem={(item) => (
                <List.Item>
                  <List.Item.Meta
                    avatar={
                      <div style={{ 
                        background: '#f0f2f5', 
                        borderRadius: 4, 
                        padding: '4px 8px',
                        textAlign: 'center',
                        minWidth: 60
                      }}>
                        <div style={{ fontSize: 10, color: '#999' }}>
                          {formatDate(item.scheduled_date, 'MM/DD')}
                        </div>
                        <div style={{ fontSize: 12, fontWeight: 'bold' }}>
                          {item.days_remaining === 0 ? 'D-Day' : `D-${item.days_remaining}`}
                        </div>
                      </div>
                    }
                    title={item.title}
                    description={
                      <Space direction="vertical" size={0}>
                        <Text type="secondary" style={{ fontSize: 12 }}>
                          {item.target_info}
                        </Text>
                        <Tag color={
                          item.category === 'health_exam' ? 'blue' :
                          item.category === 'education' ? 'green' :
                          item.category === 'work_environment' ? 'orange' :
                          'default'
                        } style={{ fontSize: 10 }}>
                          {item.category === 'health_exam' ? '건강검진' :
                           item.category === 'education' ? '안전교육' :
                           item.category === 'work_environment' ? '작업환경측정' :
                           '기타'}
                        </Tag>
                      </Space>
                    }
                  />
                </List.Item>
              )}
            />
          </Card>
        </Col>
      </Row>
    </div>
  );
};

export default Dashboard;
