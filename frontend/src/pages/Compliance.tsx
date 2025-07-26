import React, { useState } from 'react';
import { Card, Row, Col, Typography, Progress, List, Tag, Space, Button, Alert, Timeline } from 'antd';
import { 
  CheckCircleOutlined, 
  WarningOutlined, 
  CloseCircleOutlined,
  FileProtectOutlined,
  CalendarOutlined,
  TeamOutlined,
  SafetyOutlined,
  BarChartOutlined
} from '@ant-design/icons';
import { useQuery } from '@tanstack/react-query';
import { complianceApi } from '@/services/api/compliance';
import { formatDate } from '@/utils/formatters';

const { Title, Text } = Typography;

const Compliance: React.FC = () => {
  const [selectedPeriod, setSelectedPeriod] = useState<'month' | 'quarter' | 'year'>('month');

  // 컴플라이언스 대시보드 데이터
  const { data: dashboardData } = useQuery({
    queryKey: ['compliance-dashboard', selectedPeriod],
    queryFn: () => complianceApi.getDashboard(selectedPeriod),
  });

  // 미준수 항목 목록
  const { data: violations } = useQuery({
    queryKey: ['compliance-violations'],
    queryFn: () => complianceApi.getViolations(),
  });

  // 다가오는 만료 항목
  const { data: upcomingExpiries } = useQuery({
    queryKey: ['compliance-expiries'],
    queryFn: () => complianceApi.getUpcomingExpiries(),
  });

  const getComplianceColor = (rate: number) => {
    if (rate >= 95) return '#52c41a';
    if (rate >= 80) return '#faad14';
    return '#f5222d';
  };

  const getComplianceStatus = (rate: number) => {
    if (rate >= 95) return { icon: <CheckCircleOutlined />, text: '양호', color: 'success' };
    if (rate >= 80) return { icon: <WarningOutlined />, text: '주의', color: 'warning' };
    return { icon: <CloseCircleOutlined />, text: '위험', color: 'error' };
  };

  return (
    <div>
      <Title level={2}>법규 준수 현황</Title>

      {/* 전체 준수율 */}
      <Card style={{ marginBottom: 24 }}>
        <Row align="middle" gutter={24}>
          <Col xs={24} md={8}>
            <div style={{ textAlign: 'center' }}>
              <Progress
                type="circle"
                percent={dashboardData?.overall_compliance_rate || 0}
                strokeColor={getComplianceColor(dashboardData?.overall_compliance_rate || 0)}
                format={(percent) => (
                  <div>
                    <div style={{ fontSize: 32, fontWeight: 'bold' }}>{percent}%</div>
                    <div style={{ fontSize: 14, color: '#999' }}>전체 준수율</div>
                  </div>
                )}
                width={180}
              />
            </div>
          </Col>
          <Col xs={24} md={16}>
            <Space direction="vertical" size="large" style={{ width: '100%' }}>
              <div>
                <Text strong style={{ fontSize: 16 }}>법규 준수 상태</Text>
                <div style={{ marginTop: 8 }}>
                  {getComplianceStatus(dashboardData?.overall_compliance_rate || 0).icon}
                  <Tag color={getComplianceStatus(dashboardData?.overall_compliance_rate || 0).color} style={{ marginLeft: 8 }}>
                    {getComplianceStatus(dashboardData?.overall_compliance_rate || 0).text}
                  </Tag>
                </div>
              </div>
              <Alert
                message={dashboardData?.compliance_message || "법규 준수율을 지속적으로 모니터링하고 있습니다."}
                type={(dashboardData?.overall_compliance_rate || 0) >= 95 ? 'success' : 'warning'}
                showIcon
              />
            </Space>
          </Col>
        </Row>
      </Card>

      {/* 영역별 준수율 */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Space direction="vertical" style={{ width: '100%' }}>
              <Space>
                <FileProtectOutlined style={{ fontSize: 24, color: '#1890ff' }} />
                <Text strong>건강진단</Text>
              </Space>
              <Progress 
                percent={dashboardData?.health_exam_compliance || 0} 
                strokeColor={getComplianceColor(dashboardData?.health_exam_compliance || 0)}
              />
              <Text type="secondary">
                {dashboardData?.health_exam_stats?.completed || 0}/
                {dashboardData?.health_exam_stats?.required || 0}명 완료
              </Text>
            </Space>
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Space direction="vertical" style={{ width: '100%' }}>
              <Space>
                <TeamOutlined style={{ fontSize: 24, color: '#52c41a' }} />
                <Text strong>안전교육</Text>
              </Space>
              <Progress 
                percent={dashboardData?.education_compliance || 0} 
                strokeColor={getComplianceColor(dashboardData?.education_compliance || 0)}
              />
              <Text type="secondary">
                {dashboardData?.education_stats?.completed || 0}/
                {dashboardData?.education_stats?.required || 0}명 이수
              </Text>
            </Space>
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Space direction="vertical" style={{ width: '100%' }}>
              <Space>
                <SafetyOutlined style={{ fontSize: 24, color: '#fa8c16' }} />
                <Text strong>작업환경측정</Text>
              </Space>
              <Progress 
                percent={dashboardData?.work_environment_compliance || 0} 
                strokeColor={getComplianceColor(dashboardData?.work_environment_compliance || 0)}
              />
              <Text type="secondary">
                {dashboardData?.work_environment_stats?.measured || 0}/
                {dashboardData?.work_environment_stats?.required || 0}개소 완료
              </Text>
            </Space>
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Space direction="vertical" style={{ width: '100%' }}>
              <Space>
                <BarChartOutlined style={{ fontSize: 24, color: '#722ed1' }} />
                <Text strong>보고서 제출</Text>
              </Space>
              <Progress 
                percent={dashboardData?.report_compliance || 0} 
                strokeColor={getComplianceColor(dashboardData?.report_compliance || 0)}
              />
              <Text type="secondary">
                {dashboardData?.report_stats?.submitted || 0}/
                {dashboardData?.report_stats?.required || 0}건 제출
              </Text>
            </Space>
          </Card>
        </Col>
      </Row>

      <Row gutter={[16, 16]}>
        {/* 미준수 항목 */}
        <Col xs={24} md={12}>
          <Card 
            title="미준수 항목" 
            extra={<Tag color="error">{violations?.length || 0}건</Tag>}
          >
            <List
              dataSource={(violations || []) as any[]}
              renderItem={item => (
                <List.Item
                  actions={[
                    <Button type="link" size="small">조치</Button>
                  ]}
                >
                  <List.Item.Meta
                    avatar={<WarningOutlined style={{ color: '#f5222d' }} />}
                    title={item.title}
                    description={
                      <Space direction="vertical" size={0}>
                        <Text type="secondary">{item.requirement}</Text>
                        <Text type="danger" style={{ fontSize: 12 }}>
                          만료: {formatDate(item.due_date)}
                        </Text>
                      </Space>
                    }
                  />
                </List.Item>
              )}
            />
            {(!violations || violations.length === 0) && (
              <div style={{ textAlign: 'center', padding: '20px 0', color: '#999' }}>
                미준수 항목이 없습니다
              </div>
            )}
          </Card>
        </Col>

        {/* 다가오는 만료 */}
        <Col xs={24} md={12}>
          <Card 
            title="다가오는 만료 항목" 
            extra={
              <Space>
                <CalendarOutlined />
                <Text>30일 이내</Text>
              </Space>
            }
          >
            <Timeline mode="left">
              {upcomingExpiries?.map((item: any, index: number) => (
                <Timeline.Item 
                  key={index}
                  color={item.days_remaining <= 7 ? 'red' : item.days_remaining <= 14 ? 'orange' : 'blue'}
                  label={formatDate(item.expiry_date)}
                >
                  <Space direction="vertical" size={0}>
                    <Text strong>{item.title}</Text>
                    <Text type="secondary" style={{ fontSize: 12 }}>
                      {item.description}
                    </Text>
                    <Tag color={item.days_remaining <= 7 ? 'error' : 'warning'}>
                      {item.days_remaining}일 남음
                    </Tag>
                  </Space>
                </Timeline.Item>
              ))}
            </Timeline>
            {(!upcomingExpiries || upcomingExpiries.length === 0) && (
              <div style={{ textAlign: 'center', padding: '20px 0', color: '#999' }}>
                30일 이내 만료 예정 항목이 없습니다
              </div>
            )}
          </Card>
        </Col>
      </Row>

      {/* 기간 선택 버튼 */}
      <div style={{ position: 'fixed', bottom: 24, right: 24 }}>
        <Space>
          <Button 
            type={selectedPeriod === 'month' ? 'primary' : 'default'}
            onClick={() => setSelectedPeriod('month')}
          >
            월간
          </Button>
          <Button 
            type={selectedPeriod === 'quarter' ? 'primary' : 'default'}
            onClick={() => setSelectedPeriod('quarter')}
          >
            분기
          </Button>
          <Button 
            type={selectedPeriod === 'year' ? 'primary' : 'default'}
            onClick={() => setSelectedPeriod('year')}
          >
            연간
          </Button>
        </Space>
      </div>
    </div>
  );
};

export default Compliance;