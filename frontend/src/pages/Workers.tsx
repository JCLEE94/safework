import React, { useState } from 'react';
import { Card, Table, Button, Space, Tag, Modal, message } from 'antd';
import { PlusOutlined, EditOutlined, DeleteOutlined, DownloadOutlined, UploadOutlined } from '@ant-design/icons';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { workersApi, Worker } from '@/services/api/workers';
import { formatDate, formatPhoneNumber } from '@/utils/formatters';
import { PAGINATION } from '@/config/constants';

const Workers: React.FC = () => {
  const queryClient = useQueryClient();
  const [selectedWorker, setSelectedWorker] = useState<Worker | null>(null);
  const [deleteModalVisible, setDeleteModalVisible] = useState(false);

  // 작업자 목록 조회
  const { data, isLoading } = useQuery({
    queryKey: ['workers'],
    queryFn: () => workersApi.getList(),
  });

  // 작업자 삭제
  const deleteMutation = useMutation({
    mutationFn: (id: number) => workersApi.delete(id),
    onSuccess: () => {
      message.success('작업자가 삭제되었습니다.');
      queryClient.invalidateQueries({ queryKey: ['workers'] });
      setDeleteModalVisible(false);
      setSelectedWorker(null);
    },
    onError: () => {
      message.error('삭제 중 오류가 발생했습니다.');
    },
  });

  const columns = [
    {
      title: '사원번호',
      dataIndex: 'employee_id',
      key: 'employee_id',
      width: 120,
    },
    {
      title: '이름',
      dataIndex: 'name',
      key: 'name',
      width: 100,
    },
    {
      title: '부서',
      dataIndex: 'department',
      key: 'department',
      width: 150,
    },
    {
      title: '직위',
      dataIndex: 'position',
      key: 'position',
      width: 100,
    },
    {
      title: '연락처',
      dataIndex: 'phone',
      key: 'phone',
      width: 140,
      render: (phone: string) => formatPhoneNumber(phone),
    },
    {
      title: '고용형태',
      dataIndex: 'employment_type',
      key: 'employment_type',
      width: 100,
      render: (type: string) => {
        const typeMap: Record<string, { color: string; text: string }> = {
          permanent: { color: 'green', text: '정규직' },
          contract: { color: 'blue', text: '계약직' },
          temporary: { color: 'orange', text: '임시직' },
        };
        const config = typeMap[type] || { color: 'default', text: type };
        return <Tag color={config.color}>{config.text}</Tag>;
      },
    },
    {
      title: '입사일',
      dataIndex: 'employment_date',
      key: 'employment_date',
      width: 120,
      render: (date: string) => formatDate(date),
    },
    {
      title: '상태',
      dataIndex: 'is_active',
      key: 'is_active',
      width: 80,
      render: (isActive: boolean) => (
        <Tag color={isActive ? 'success' : 'error'}>
          {isActive ? '재직' : '퇴직'}
        </Tag>
      ),
    },
    {
      title: '작업',
      key: 'action',
      width: 120,
      fixed: 'right' as const,
      render: (_: any, record: Worker) => (
        <Space size="small">
          <Button
            type="text"
            icon={<EditOutlined />}
            onClick={() => handleEdit(record)}
          />
          <Button
            type="text"
            danger
            icon={<DeleteOutlined />}
            onClick={() => handleDelete(record)}
          />
        </Space>
      ),
    },
  ];

  const handleEdit = (worker: Worker) => {
    // TODO: 편집 모달 열기
    console.log('Edit worker:', worker);
  };

  const handleDelete = (worker: Worker) => {
    setSelectedWorker(worker);
    setDeleteModalVisible(true);
  };

  const handleExport = async () => {
    try {
      await workersApi.exportToExcel();
      message.success('엑셀 파일이 다운로드되었습니다.');
    } catch (error) {
      message.error('다운로드 중 오류가 발생했습니다.');
    }
  };

  return (
    <div>
      <Card
        title="작업자 관리"
        extra={
          <Space>
            <Button icon={<UploadOutlined />}>
              엑셀 가져오기
            </Button>
            <Button icon={<DownloadOutlined />} onClick={handleExport}>
              엑셀 내보내기
            </Button>
            <Button type="primary" icon={<PlusOutlined />}>
              작업자 추가
            </Button>
          </Space>
        }
      >
        <Table
          columns={columns}
          dataSource={data?.items || []}
          loading={isLoading}
          rowKey="id"
          scroll={{ x: 1200 }}
          pagination={{
            defaultPageSize: PAGINATION.DEFAULT_PAGE_SIZE,
            showSizeChanger: true,
            pageSizeOptions: PAGINATION.PAGE_SIZE_OPTIONS.map(String),
            showTotal: (total) => `총 ${total}명`,
          }}
        />
      </Card>

      <Modal
        title="작업자 삭제"
        open={deleteModalVisible}
        onOk={() => selectedWorker && deleteMutation.mutate(selectedWorker.id)}
        onCancel={() => setDeleteModalVisible(false)}
        confirmLoading={deleteMutation.isPending}
      >
        <p>
          <strong>{selectedWorker?.name}</strong> ({selectedWorker?.employee_id})님을 
          삭제하시겠습니까?
        </p>
        <p>이 작업은 되돌릴 수 없습니다.</p>
      </Modal>
    </div>
  );
};

export default Workers;