import React, { useState } from 'react';
import { 
  Table, 
  Card, 
  Button, 
  Space, 
  Input, 
  Select, 
  Tag, 
  Dropdown,
  Typography,
  Row,
  Col,
  Avatar,
  Tooltip,
  Badge,
  Segmented,
} from 'antd';
import {
  PlusOutlined,
  SearchOutlined,
  FilterOutlined,
  DownloadOutlined,
  MoreOutlined,
  EditOutlined,
  DeleteOutlined,
  FileTextOutlined,
  MedicineBoxOutlined,
  UserOutlined,
  TeamOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  ExclamationCircleOutlined,
} from '@ant-design/icons';
import styled from 'styled-components';
import { designTokens } from '../../../styles/theme';
import type { ColumnsType } from 'antd/es/table';

const { Title, Text } = Typography;

const PageContainer = styled.div`
  .page-header {
    margin-bottom: ${designTokens.spacing.lg}px;
  }
  
  .filter-section {
    background: white;
    padding: ${designTokens.spacing.lg}px;
    border-radius: ${designTokens.borderRadius.base}px;
    margin-bottom: ${designTokens.spacing.lg}px;
    box-shadow: ${designTokens.shadows.sm};
  }
  
  .stat-cards {
    margin-bottom: ${designTokens.spacing.lg}px;
  }
`;

const StatCard = styled(Card)`
  .stat-icon {
    font-size: 24px;
    padding: 12px;
    border-radius: ${designTokens.borderRadius.base}px;
    background: ${props => props.color}20;
    color: ${props => props.color};
  }
  
  .stat-content {
    display: flex;
    align-items: center;
    justify-content: space-between;
  }
  
  .stat-info {
    flex: 1;
  }
`;

const WorkerNameCell = styled.div`
  display: flex;
  align-items: center;
  gap: ${designTokens.spacing.sm}px;
  
  .worker-info {
    .worker-name {
      font-weight: ${designTokens.typography.fontWeight.medium};
      color: ${designTokens.colors.neutral[900]};
    }
    .worker-id {
      font-size: ${designTokens.typography.fontSize.xs}px;
      color: ${designTokens.colors.neutral[500]};
    }
  }
`;

const ActionButton = styled(Button)`
  &.ant-btn-text {
    color: ${designTokens.colors.neutral[600]};
    
    &:hover {
      color: ${designTokens.colors.primary[600]};
      background: ${designTokens.colors.primary[50]};
    }
  }
`;

// 더미 데이터
const mockWorkers = [
  {
    id: 1,
    employeeId: 'EMP001',
    name: '김철수',
    department: '생산1팀',
    position: '선임기술자',
    employmentType: '정규직',
    gender: '남',
    age: 35,
    workYears: 5,
    healthStatus: 'good',
    lastExamDate: '2025-06-15',
    nextExamDate: '2025-12-15',
    educationStatus: 'completed',
    riskLevel: 'low',
  },
  {
    id: 2,
    employeeId: 'EMP002',
    name: '이영희',
    department: '품질관리팀',
    position: '주임',
    employmentType: '정규직',
    gender: '여',
    age: 28,
    workYears: 3,
    healthStatus: 'attention',
    lastExamDate: '2025-05-20',
    nextExamDate: '2025-11-20',
    educationStatus: 'pending',
    riskLevel: 'medium',
  },
];

interface Worker {
  id: number;
  employeeId: string;
  name: string;
  department: string;
  position: string;
  employmentType: string;
  gender: string;
  age: number;
  workYears: number;
  healthStatus: string;
  lastExamDate: string;
  nextExamDate: string;
  educationStatus: string;
  riskLevel: string;
}

export const WorkerList: React.FC = () => {
  const [selectedRowKeys, setSelectedRowKeys] = useState<React.Key[]>([]);
  const [viewMode, setViewMode] = useState<string>('table');

  const getHealthStatusTag = (status: string) => {
    const config = {
      good: { color: 'success', text: '양호', icon: <CheckCircleOutlined /> },
      attention: { color: 'warning', text: '주의', icon: <ExclamationCircleOutlined /> },
      bad: { color: 'error', text: '위험', icon: <CloseCircleOutlined /> },
    };
    const { color, text, icon } = config[status as keyof typeof config] || config.good;
    
    return (
      <Tag color={color} icon={icon}>
        {text}
      </Tag>
    );
  };

  const getRiskLevelBadge = (level: string) => {
    const colors = {
      low: designTokens.colors.success[500],
      medium: designTokens.colors.warning[500],
      high: designTokens.colors.error[500],
    };
    
    return (
      <Badge 
        color={colors[level as keyof typeof colors]} 
        text={
          level === 'low' ? '낮음' : 
          level === 'medium' ? '보통' : '높음'
        }
      />
    );
  };

  const columns: ColumnsType<Worker> = [
    {
      title: '근로자',
      dataIndex: 'name',
      key: 'name',
      fixed: 'left',
      width: 200,
      render: (text, record) => (
        <WorkerNameCell>
          <Avatar icon={<UserOutlined />} />
          <div className="worker-info">
            <div className="worker-name">{text}</div>
            <div className="worker-id">{record.employeeId}</div>
          </div>
        </WorkerNameCell>
      ),
    },
    {
      title: '소속',
      dataIndex: 'department',
      key: 'department',
      width: 120,
    },
    {
      title: '직위',
      dataIndex: 'position',
      key: 'position',
      width: 100,
    },
    {
      title: '고용형태',
      dataIndex: 'employmentType',
      key: 'employmentType',
      width: 100,
      render: (text) => (
        <Tag color={text === '정규직' ? 'blue' : 'orange'}>
          {text}
        </Tag>
      ),
    },
    {
      title: '건강상태',
      dataIndex: 'healthStatus',
      key: 'healthStatus',
      width: 100,
      render: (status) => getHealthStatusTag(status),
    },
    {
      title: '차기검진',
      dataIndex: 'nextExamDate',
      key: 'nextExamDate',
      width: 120,
      render: (date) => {
        const daysUntil = Math.floor((new Date(date).getTime() - new Date().getTime()) / (1000 * 60 * 60 * 24));
        return (
          <Tooltip title={`D-${daysUntil}`}>
            <Text type={daysUntil < 30 ? 'danger' : undefined}>
              {date}
            </Text>
          </Tooltip>
        );
      },
    },
    {
      title: '교육상태',
      dataIndex: 'educationStatus',
      key: 'educationStatus',
      width: 100,
      render: (status) => (
        <Tag color={status === 'completed' ? 'success' : 'warning'}>
          {status === 'completed' ? '이수' : '미이수'}
        </Tag>
      ),
    },
    {
      title: '위험도',
      dataIndex: 'riskLevel',
      key: 'riskLevel',
      width: 100,
      render: (level) => getRiskLevelBadge(level),
    },
    {
      title: '작업',
      key: 'action',
      fixed: 'right',
      width: 80,
      render: () => (
        <Dropdown
          menu={{
            items: [
              {
                key: 'view',
                label: '상세보기',
                icon: <FileTextOutlined />,
              },
              {
                key: 'edit',
                label: '수정',
                icon: <EditOutlined />,
              },
              {
                key: 'health',
                label: '건강기록',
                icon: <MedicineBoxOutlined />,
              },
              {
                type: 'divider',
              },
              {
                key: 'delete',
                label: '삭제',
                icon: <DeleteOutlined />,
                danger: true,
              },
            ],
          }}
          trigger={['click']}
        >
          <ActionButton type="text" icon={<MoreOutlined />} />
        </Dropdown>
      ),
    },
  ];

  const rowSelection = {
    selectedRowKeys,
    onChange: (keys: React.Key[]) => setSelectedRowKeys(keys),
  };

  return (
    <PageContainer>
      <div className="page-header">
        <Row justify="space-between" align="middle">
          <Col>
            <Title level={2} style={{ margin: 0 }}>근로자 관리</Title>
          </Col>
          <Col>
            <Space>
              <Button icon={<DownloadOutlined />}>엑셀 다운로드</Button>
              <Button type="primary" icon={<PlusOutlined />}>
                근로자 등록
              </Button>
            </Space>
          </Col>
        </Row>
      </div>

      <Row gutter={[16, 16]} className="stat-cards">
        <Col xs={24} sm={12} md={6}>
          <StatCard size="small" color={designTokens.colors.primary[500]}>
            <div className="stat-content">
              <div className="stat-info">
                <Text type="secondary">전체 근로자</Text>
                <Title level={3} style={{ margin: '4px 0' }}>245명</Title>
              </div>
              <div className="stat-icon">
                <TeamOutlined />
              </div>
            </div>
          </StatCard>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <StatCard size="small" color={designTokens.colors.success[500]}>
            <div className="stat-content">
              <div className="stat-info">
                <Text type="secondary">건강 양호</Text>
                <Title level={3} style={{ margin: '4px 0' }}>198명</Title>
              </div>
              <div className="stat-icon">
                <CheckCircleOutlined />
              </div>
            </div>
          </StatCard>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <StatCard size="small" color={designTokens.colors.warning[500]}>
            <div className="stat-content">
              <div className="stat-info">
                <Text type="secondary">검진 예정</Text>
                <Title level={3} style={{ margin: '4px 0' }}>32명</Title>
              </div>
              <div className="stat-icon">
                <MedicineBoxOutlined />
              </div>
            </div>
          </StatCard>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <StatCard size="small" color={designTokens.colors.error[500]}>
            <div className="stat-content">
              <div className="stat-info">
                <Text type="secondary">교육 미이수</Text>
                <Title level={3} style={{ margin: '4px 0' }}>15명</Title>
              </div>
              <div className="stat-icon">
                <ExclamationCircleOutlined />
              </div>
            </div>
          </StatCard>
        </Col>
      </Row>

      <div className="filter-section">
        <Row gutter={[16, 16]} align="middle">
          <Col flex="auto">
            <Space size="middle" wrap>
              <Input
                placeholder="이름, 사번으로 검색"
                prefix={<SearchOutlined />}
                style={{ width: 240 }}
              />
              <Select
                placeholder="부서 선택"
                style={{ width: 160 }}
                options={[
                  { value: 'all', label: '전체 부서' },
                  { value: 'prod1', label: '생산1팀' },
                  { value: 'prod2', label: '생산2팀' },
                  { value: 'qa', label: '품질관리팀' },
                ]}
              />
              <Select
                placeholder="건강상태"
                style={{ width: 120 }}
                options={[
                  { value: 'all', label: '전체' },
                  { value: 'good', label: '양호' },
                  { value: 'attention', label: '주의' },
                  { value: 'bad', label: '위험' },
                ]}
              />
              <Button icon={<FilterOutlined />}>
                고급 필터
              </Button>
            </Space>
          </Col>
          <Col>
            <Segmented
              value={viewMode}
              onChange={setViewMode}
              options={[
                { label: '테이블', value: 'table' },
                { label: '카드', value: 'card' },
              ]}
            />
          </Col>
        </Row>
      </div>

      <Card>
        <Table
          rowSelection={rowSelection}
          columns={columns}
          dataSource={mockWorkers}
          rowKey="id"
          scroll={{ x: 1200 }}
          pagination={{
            total: 245,
            pageSize: 10,
            showSizeChanger: true,
            showTotal: (total) => `총 ${total}명`,
          }}
        />
      </Card>
    </PageContainer>
  );
};