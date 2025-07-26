import React, { useState } from 'react';
import { Card, Table, Button, Space, Tag, Typography, Row, Col, Statistic, Progress, DatePicker } from 'antd';
import { PlusOutlined, CalendarOutlined, TeamOutlined, FilePdfOutlined } from '@ant-design/icons';
import { useQuery } from '@tanstack/react-query';
import { educationsApi, Education } from '@/services/api/educations';
import { formatDate, formatStatusLabel } from '@/utils/formatters';
import { PAGINATION, EDUCATION_CATEGORIES } from '@/config/constants';
import dayjs from 'dayjs';

const { Title } = Typography;
const { RangePicker } = DatePicker;

const Educations: React.FC = () => {
  const [filter, setFilter] = useState({});
  const [dateRange, setDateRange] = useState<[dayjs.Dayjs, dayjs.Dayjs] | null>(null);

  // 교육 목록 조회
  const { data: educationData, isLoading } = useQuery({
    queryKey: ['educations', filter],
    queryFn: () => educationsApi.getList(filter),
  });

  // 교육 통계 조회
  const { data: stats } = useQuery({
    queryKey: ['education-stats'],
    queryFn: () => educationsApi.getStats(),
  });

  const columns = [
    {
      title: '교육일정',
      key: 'schedule',
      width: 200,
      render: (record: Education) => (
        <Space direction="vertical" size={0}>
          <span>{formatDate(record.education_date)}</span>
          <span style={{ fontSize: 12, color: '#999' }}>
            {record.start_time} - {record.end_time} ({record.duration_hours}시간)
          </span>
        </Space>
      ),
    },
    {
      title: '교육명',
      dataIndex: 'title',
      key: 'title',
      width: 250,
      ellipsis: true,
    },
    {
      title: '분류',
      dataIndex: 'category',
      key: 'category',
      width: 120,
      render: (category: keyof typeof EDUCATION_CATEGORIES) => {
        const categoryMap = {
          safety: { color: 'blue', text: '안전교육' },
          health: { color: 'green', text: '보건교육' },
          emergency: { color: 'red', text: '응급대응' },
          special: { color: 'purple', text: '특별교육' },
          regular: { color: 'orange', text: '정기교육' },
        };
        const config = categoryMap[category as keyof typeof categoryMap] || { color: 'default', text: category };
        return <Tag color={config.color}>{config.text}</Tag>;
      },
    },
    {
      title: '교육방법',
      key: 'method',
      width: 100,
      render: (record: Education) => {
        const isOnline = record.location === '온라인' || record.location.toLowerCase() === 'online';
        return (
          <Space>
            {isOnline ? <FilePdfOutlined /> : <TeamOutlined />}
            <span>{isOnline ? '온라인' : '집합'}</span>
          </Space>
        );
      },
    },
    {
      title: '강사',
      dataIndex: 'instructor',
      key: 'instructor',
      width: 100,
    },
    {
      title: '장소',
      dataIndex: 'location',
      key: 'location',
      width: 150,
      ellipsis: true,
      render: (location: string) => 
        location === '온라인' ? '온라인' : location,
    },
    {
      title: '대상인원',
      key: 'participants',
      width: 120,
      render: (record: Education) => (
        <Space>
          <span>{record.current_participants}/{record.max_participants}명</span>
          <Progress
            percent={Math.round((record.current_participants / record.max_participants) * 100)}
            size="small"
            style={{ width: 50 }}
          />
        </Space>
      ),
    },
    {
      title: '상태',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (status: string) => {
        const statusMap = {
          planned: 'warning',
          in_progress: 'processing',
          completed: 'success',
          cancelled: 'error',
        };
        return (
          <Tag color={statusMap[status as keyof typeof statusMap]}>
            {formatStatusLabel(status, 'education')}
          </Tag>
        );
      },
    },
    {
      title: '작업',
      key: 'action',
      width: 100,
      fixed: 'right' as const,
      render: (_: any, record: Education) => (
        <Space size="small">
          <Button
            type="link"
            size="small"
            onClick={() => handleViewDetail(record)}
          >
            상세
          </Button>
          <Button
            type="link"
            size="small"
            onClick={() => handleManageAttendance(record)}
          >
            출석
          </Button>
        </Space>
      ),
    },
  ];

  const handleViewDetail = (education: Education) => {
    // TODO: 교육 상세 페이지로 이동
    console.log('View education detail:', education);
  };

  const handleManageAttendance = (education: Education) => {
    // TODO: 출석 관리 모달 열기
    console.log('Manage attendance:', education);
  };

  const handleDateRangeChange = (dates: [dayjs.Dayjs | null, dayjs.Dayjs | null] | null) => {
    if (dates && dates[0] && dates[1]) {
      setDateRange([dates[0], dates[1]]);
      setFilter({
        ...filter,
        start_date: dates[0].format('YYYY-MM-DD'),
        end_date: dates[1].format('YYYY-MM-DD'),
      });
    } else {
      setDateRange(null);
      const { start_date, end_date, ...rest } = filter as any;
      setFilter(rest);
    }
  };

  return (
    <div>
      <Title level={2}>교육 관리</Title>

      {/* 통계 카드 */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="월간 교육 실시"
              value={stats?.total_educations || 0}
              suffix="회"
              prefix={<CalendarOutlined />}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="총 수료 인원"
              value={stats?.total_participants || 0}
              suffix="명"
              prefix={<TeamOutlined />}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="평균 출석률"
              value={stats?.average_attendance_rate || 0}
              suffix="%"
              valueStyle={{ 
                color: stats?.average_attendance_rate && stats.average_attendance_rate >= 80 
                  ? '#3f8600' 
                  : '#cf1322' 
              }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="법정교육 이수율"
              value={stats?.average_completion_rate || 0}
              suffix="%"
              valueStyle={{ 
                color: stats?.average_completion_rate && stats.average_completion_rate >= 90 
                  ? '#3f8600' 
                  : '#cf1322' 
              }}
            />
          </Card>
        </Col>
      </Row>

      {/* 교육 목록 */}
      <Card
        title="교육 목록"
        extra={
          <Space>
            <RangePicker
              value={dateRange}
              onChange={handleDateRangeChange}
              placeholder={['시작일', '종료일']}
            />
            <Button>
              교육 보고서
            </Button>
            <Button type="primary" icon={<PlusOutlined />}>
              교육 등록
            </Button>
          </Space>
        }
      >
        <Table
          columns={columns}
          dataSource={educationData?.items || []}
          loading={isLoading}
          rowKey="id"
          scroll={{ x: 1300 }}
          pagination={{
            total: educationData?.total || 0,
            pageSize: educationData?.pageSize || PAGINATION.DEFAULT_PAGE_SIZE,
            current: educationData?.page || 1,
            showSizeChanger: true,
            pageSizeOptions: PAGINATION.PAGE_SIZE_OPTIONS.map(String),
            showTotal: (total) => `총 ${total}건`,
          }}
          rowClassName={(record) => {
            const today = dayjs();
            const educationDate = dayjs(record.education_date);
            if (educationDate.isBefore(today) && record.status === 'PLANNED') {
              return 'table-row-overdue';
            }
            return '';
          }}
        />
      </Card>

      <style>{`
        :global(.table-row-overdue) {
          background-color: #fff1f0;
        }
      `}</style>
    </div>
  );
};

export default Educations;