import React from 'react';
import { Tag, Space } from 'antd';
import { ColumnsType } from 'antd/es/table';
import { DataTable } from '@/components/organisms/DataTable';
import { WorkerExamStatus } from '../types';
import dayjs from 'dayjs';

interface WorkerExamStatusTableProps {
  data: WorkerExamStatus[];
  loading?: boolean;
}

const getStatusTag = (status: WorkerExamStatus['exam_status']) => {
  const config = {
    completed: { color: 'success', text: '완료' },
    scheduled: { color: 'processing', text: '예정' },
    overdue: { color: 'error', text: '기한 초과' },
  };
  
  const { color, text } = config[status];
  return <Tag color={color}>{text}</Tag>;
};

export const WorkerExamStatusTable: React.FC<WorkerExamStatusTableProps> = ({ data, loading }) => {
  const columns: ColumnsType<WorkerExamStatus> = [
    {
      title: '근로자명',
      dataIndex: 'worker_name',
      key: 'worker_name',
      width: 120,
    },
    {
      title: '부서',
      dataIndex: 'department',
      key: 'department',
      width: 150,
    },
    {
      title: '최근 검진일',
      dataIndex: 'last_exam_date',
      key: 'last_exam_date',
      width: 120,
      render: (date) => date ? dayjs(date).format('YYYY-MM-DD') : '-',
    },
    {
      title: '다음 검진 예정일',
      dataIndex: 'next_exam_due',
      key: 'next_exam_due',
      width: 140,
      render: (date) => dayjs(date).format('YYYY-MM-DD'),
    },
    {
      title: '상태',
      dataIndex: 'exam_status',
      key: 'exam_status',
      width: 100,
      render: getStatusTag,
    },
    {
      title: '작업',
      key: 'action',
      width: 100,
      render: (_, record) => (
        <Space size="middle">
          <a>상세보기</a>
          {record.exam_status === 'overdue' && <a>알림발송</a>}
        </Space>
      ),
    },
  ];

  const mobileColumns: ColumnsType<WorkerExamStatus> = [
    {
      title: '근로자',
      dataIndex: 'worker_name',
      key: 'worker_name',
      render: (name, record) => (
        <Space direction="vertical" size={0}>
          <span style={{ fontWeight: 500 }}>{name}</span>
          <span style={{ fontSize: 12, color: '#999' }}>{record.department}</span>
        </Space>
      ),
    },
    {
      title: '다음 검진',
      dataIndex: 'next_exam_due',
      key: 'next_exam_due',
      render: (date, record) => (
        <Space direction="vertical" size={0}>
          <span>{dayjs(date).format('YY-MM-DD')}</span>
          {getStatusTag(record.exam_status)}
        </Space>
      ),
    },
  ];

  return (
    <DataTable<WorkerExamStatus>
      columns={columns}
      mobileColumns={mobileColumns}
      dataSource={data}
      loading={loading}
      rowKey="worker_id"
      pagination={{
        pageSize: 10,
        showTotal: (total) => `총 ${total}명`,
      }}
    />
  );
};