import React, { useState } from 'react';
import { Card, Table, Button, Space, Tag, Typography, Row, Col, Statistic } from 'antd';
import { PlusOutlined, FileTextOutlined } from '@ant-design/icons';
import { useQuery } from '@tanstack/react-query';
import { accidentsApi, Accident } from '@/services/api/accidents';
import { formatDate, formatStatusLabel } from '@/utils/formatters';
import { PAGINATION } from '@/config/constants';

const { Title } = Typography;

const Accidents: React.FC = () => {
  const [filter] = useState({});

  // 사고 목록 조회
  const { data: accidentData, isLoading } = useQuery({
    queryKey: ['accidents', filter],
    queryFn: () => accidentsApi.getList(filter),
  });

  // 사고 통계 조회
  const { data: stats } = useQuery({
    queryKey: ['accident-stats'],
    queryFn: () => accidentsApi.getStats(),
  });

  const columns = [
    {
      title: '사고일시',
      key: 'accident_datetime',
      width: 150,
      render: (record: Accident) => (
        <Space direction="vertical" size={0}>
          <span>{formatDate(record.accident_date)}</span>
          <span style={{ fontSize: 12, color: '#999' }}>{record.accident_time}</span>
        </Space>
      ),
    },
    {
      title: '유형',
      dataIndex: 'accident_type',
      key: 'accident_type',
      width: 100,
      render: (type: string) => {
        const typeMap: Record<string, { color: string; text: string }> = {
          injury: { color: 'red', text: '부상' },
          near_miss: { color: 'orange', text: '아차사고' },
          property_damage: { color: 'blue', text: '재산피해' },
          environmental: { color: 'green', text: '환경사고' },
        };
        const config = typeMap[type] || { color: 'default', text: type };
        return <Tag color={config.color}>{config.text}</Tag>;
      },
    },
    {
      title: '심각도',
      dataIndex: 'severity',
      key: 'severity',
      width: 100,
      render: (severity: string) => {
        const severityMap = {
          minor: { color: 'green', text: '경미' },
          moderate: { color: 'orange', text: '보통' },
          major: { color: 'red', text: '중대' },
          fatal: { color: 'purple', text: '치명' },
        };
        const config = severityMap[severity as keyof typeof severityMap];
        return <Tag color={config.color}>{config.text}</Tag>;
      },
    },
    {
      title: '장소',
      dataIndex: 'location',
      key: 'location',
      width: 150,
      ellipsis: true,
    },
    {
      title: '피해자',
      dataIndex: 'injured_worker_name',
      key: 'injured_worker_name',
      width: 100,
      render: (name: string) => name || '-',
    },
    {
      title: '부서',
      dataIndex: 'department',
      key: 'department',
      width: 120,
    },
    {
      title: '상태',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (status: string) => {
        const statusMap = {
          reported: 'warning',
          investigating: 'processing',
          resolved: 'success',
          closed: 'default',
        };
        return (
          <Tag color={statusMap[status as keyof typeof statusMap]}>
            {formatStatusLabel(status, 'accident')}
          </Tag>
        );
      },
    },
    {
      title: '작업',
      key: 'action',
      width: 100,
      fixed: 'right' as const,
      render: (_: any, record: Accident) => (
        <Space size="small">
          <Button
            type="link"
            size="small"
            icon={<FileTextOutlined />}
            onClick={() => handleViewDetail(record)}
          >
            상세
          </Button>
        </Space>
      ),
    },
  ];

  const handleViewDetail = (accident: Accident) => {
    // TODO: 사고 상세 페이지로 이동
    console.log('View accident detail:', accident);
  };

  const handleGenerateReport = async () => {
    const now = new Date();
    await accidentsApi.generateMonthlyReport(now.getFullYear(), now.getMonth() + 1);
  };

  return (
    <div>
      <Title level={2}>사고 관리</Title>

      {/* 통계 카드 */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="총 사고건수"
              value={stats?.total_accidents || 0}
              suffix="건"
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="LTIFR"
              value={stats?.ltifr || 0}
              precision={2}
              valueStyle={{ color: stats?.ltifr && stats.ltifr > 1 ? '#cf1322' : '#3f8600' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="손실일수"
              value={stats?.total_lost_days || 0}
              suffix="일"
              valueStyle={{ color: '#faad14' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="의료비용"
              value={stats?.total_medical_costs || 0}
              prefix="₩"
              precision={0}
            />
          </Card>
        </Col>
      </Row>

      {/* 사고 목록 */}
      <Card
        title="사고 목록"
        extra={
          <Space>
            <Button onClick={handleGenerateReport}>
              월간 보고서
            </Button>
            <Button type="primary" icon={<PlusOutlined />}>
              사고 보고
            </Button>
          </Space>
        }
      >
        <Table
          columns={columns}
          dataSource={accidentData?.items || []}
          loading={isLoading}
          rowKey="id"
          scroll={{ x: 1000 }}
          pagination={{
            total: accidentData?.total || 0,
            pageSize: accidentData?.pageSize || PAGINATION.DEFAULT_PAGE_SIZE,
            current: accidentData?.page || 1,
            showSizeChanger: true,
            pageSizeOptions: PAGINATION.PAGE_SIZE_OPTIONS.map(String),
            showTotal: (total) => `총 ${total}건`,
          }}
          rowClassName={(record) => {
            if (record.severity === 'fatal') return 'table-row-fatal';
            if (record.severity === 'major') return 'table-row-major';
            return '';
          }}
        />
      </Card>

      <style>{`
        :global(.table-row-fatal) {
          background-color: #fff1f0;
        }
        :global(.table-row-major) {
          background-color: #fff7e6;
        }
      `}</style>
    </div>
  );
};

export default Accidents;