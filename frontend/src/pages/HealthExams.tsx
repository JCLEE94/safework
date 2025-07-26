import React, { useState } from 'react';
import { Card, Table, Button, Space, Tag, Typography, Row, Col, DatePicker, Select, Progress } from 'antd';
import { 
  PlusOutlined, 
  CalendarOutlined, 
  FileTextOutlined,
  TeamOutlined,
  MedicineBoxOutlined
} from '@ant-design/icons';
import { useQuery } from '@tanstack/react-query';
import { healthExamsApi, HealthExam } from '@/services/api/healthExams';
import { formatDate, formatExamTypeLabel } from '@/utils/formatters';
import { PAGINATION } from '@/config/constants';
import dayjs from 'dayjs';

const { Title } = Typography;
const { RangePicker } = DatePicker;
const { Option } = Select;

const HealthExams: React.FC = () => {
  const [filter, setFilter] = useState({});
  const [selectedExamType, setSelectedExamType] = useState<string>('all');

  // 건강검진 목록 조회
  const { data: examData, isLoading } = useQuery({
    queryKey: ['health-exams', filter, selectedExamType],
    queryFn: () => healthExamsApi.getList({
      ...filter,
      exam_type: selectedExamType === 'all' ? undefined : selectedExamType as any,
    }),
  });

  // 건강검진 통계 조회
  const { data: stats } = useQuery({
    queryKey: ['health-exam-stats'],
    queryFn: () => healthExamsApi.getStats(),
  });

  const columns = [
    {
      title: '검진일자',
      dataIndex: 'exam_date',
      key: 'exam_date',
      width: 120,
      render: (date: string) => formatDate(date),
      sorter: true,
    },
    {
      title: '수검자',
      key: 'worker_info',
      width: 200,
      render: (record: HealthExam) => (
        <Space direction="vertical" size={0}>
          <span>{record.worker_name || `Worker ${record.worker_id}`}</span>
          <span style={{ fontSize: 12, color: '#999' }}>
            ID: {record.worker_id}
          </span>
        </Space>
      ),
    },
    {
      title: '검진종류',
      dataIndex: 'exam_type',
      key: 'exam_type',
      width: 120,
      render: (type: string) => {
        const color = {
          general: 'blue',
          special: 'orange',
          placement: 'green',
          return_to_work: 'purple',
        }[type] || 'default';
        return <Tag color={color}>{formatExamTypeLabel(type)}</Tag>;
      },
    },
    {
      title: '검진기관',
      dataIndex: 'exam_agency',
      key: 'exam_agency',
      width: 150,
      ellipsis: true,
    },
    {
      title: '검진결과',
      dataIndex: 'result_status',
      key: 'result_status',
      width: 100,
      render: (result: string) => {
        const resultMap = {
          normal: { color: 'success', text: '정상' },
          observation: { color: 'warning', text: '관찰필요' },
          disease_suspect: { color: 'orange', text: '질병의심' },
          disease: { color: 'error', text: '유질병' },
        };
        const config = resultMap[result as keyof typeof resultMap] || { color: 'default', text: result };
        return <Tag color={config.color}>{config.text}</Tag>;
      },
    },
    {
      title: '다음 검진일',
      dataIndex: 'next_exam_date',
      key: 'next_exam_date',
      width: 120,
      render: (date: string) => date ? formatDate(date) : '-',
    },
    {
      title: '작업',
      key: 'action',
      width: 120,
      fixed: 'right' as const,
      render: (_: any, record: HealthExam) => (
        <Space size="small">
          <Button
            type="link"
            size="small"
            icon={<FileTextOutlined />}
            onClick={() => handleViewDetail(record)}
          >
            상세
          </Button>
          <Button
            type="link"
            size="small"
            onClick={() => handlePrintReport(record)}
          >
            결과지
          </Button>
        </Space>
      ),
    },
  ];

  const handleViewDetail = (exam: HealthExam) => {
    // TODO: 건강검진 상세 페이지로 이동
    console.log('View exam detail:', exam);
  };

  const handlePrintReport = (exam: HealthExam) => {
    // TODO: 검진 결과지 출력
    console.log('Print exam report:', exam);
  };

  const handleDateRangeChange = (dates: [dayjs.Dayjs | null, dayjs.Dayjs | null] | null) => {
    if (dates && dates[0] && dates[1]) {
      setFilter({
        ...filter,
        start_date: dates[0].format('YYYY-MM-DD'),
        end_date: dates[1].format('YYYY-MM-DD'),
      });
    } else {
      const { start_date, end_date, ...rest } = filter as any;
      setFilter(rest);
    }
  };

  return (
    <div>
      <Title level={2}>건강검진 관리</Title>

      {/* 통계 카드 */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Space direction="vertical" style={{ width: '100%' }}>
              <Space>
                <CalendarOutlined style={{ fontSize: 20, color: '#1890ff' }} />
                <span style={{ color: '#999' }}>월간 검진</span>
              </Space>
              <div style={{ fontSize: 24, fontWeight: 'bold' }}>
                {stats?.monthly_completed || 0}/{stats?.monthly_scheduled || 0}명
              </div>
              <Progress 
                percent={Math.round(((stats?.monthly_completed || 0) / (stats?.monthly_scheduled || 1)) * 100)}
                size="small"
                showInfo={false}
              />
            </Space>
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Space direction="vertical" style={{ width: '100%' }}>
              <Space>
                <TeamOutlined style={{ fontSize: 20, color: '#52c41a' }} />
                <span style={{ color: '#999' }}>특수검진 대상</span>
              </Space>
              <div style={{ fontSize: 24, fontWeight: 'bold' }}>
                {stats?.special_exam_targets || 0}명
              </div>
              <Tag color="orange">주의 필요</Tag>
            </Space>
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Space direction="vertical" style={{ width: '100%' }}>
              <Space>
                <MedicineBoxOutlined style={{ fontSize: 20, color: '#fa8c16' }} />
                <span style={{ color: '#999' }}>미수검자</span>
              </Space>
              <div style={{ fontSize: 24, fontWeight: 'bold' }}>
                {stats?.overdue_count || 0}명
              </div>
              <Tag color="error">즉시 조치</Tag>
            </Space>
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Space direction="vertical" style={{ width: '100%' }}>
              <span style={{ color: '#999' }}>사후관리 필요</span>
              <div style={{ fontSize: 24, fontWeight: 'bold' }}>
                {stats?.follow_up_required || 0}명
              </div>
              <Progress 
                percent={Math.round(((stats?.follow_up_completed || 0) / (stats?.follow_up_required || 1)) * 100)}
                size="small"
                format={() => `${stats?.follow_up_completed || 0}명 완료`}
              />
            </Space>
          </Card>
        </Col>
      </Row>

      {/* 검진 목록 */}
      <Card
        title="건강검진 목록"
        extra={
          <Space>
            <Select 
              value={selectedExamType} 
              onChange={setSelectedExamType}
              style={{ width: 150 }}
            >
              <Option value="all">전체 검진</Option>
              <Option value="general">일반건강진단</Option>
              <Option value="special">특수건강진단</Option>
              <Option value="placement">배치전건강진단</Option>
              <Option value="return_to_work">복직건강진단</Option>
            </Select>
            <RangePicker
              onChange={handleDateRangeChange}
              placeholder={['시작일', '종료일']}
            />
            <Button>
              검진 보고서
            </Button>
            <Button type="primary" icon={<PlusOutlined />}>
              검진 등록
            </Button>
          </Space>
        }
      >
        <Table
          columns={columns}
          dataSource={examData?.items || []}
          loading={isLoading}
          rowKey="id"
          scroll={{ x: 1300 }}
          pagination={{
            total: examData?.total || 0,
            pageSize: examData?.pageSize || PAGINATION.DEFAULT_PAGE_SIZE,
            current: examData?.page || 1,
            showSizeChanger: true,
            pageSizeOptions: PAGINATION.PAGE_SIZE_OPTIONS.map(String),
            showTotal: (total) => `총 ${total}건`,
          }}
          rowClassName={(record) => {
            if (record.result_status === 'disease' || record.result_status === 'disease_suspect') return 'table-row-warning';
            return '';
          }}
        />
      </Card>

      <style>{`
        :global(.table-row-overdue) {
          background-color: #fff1f0;
        }
        :global(.table-row-warning) {
          background-color: #fffbe6;
        }
      `}</style>
    </div>
  );
};

export default HealthExams;