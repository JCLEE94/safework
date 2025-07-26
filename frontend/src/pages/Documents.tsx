import React, { useState } from 'react';
import { Card, Table, Button, Space, Tag, Typography, Row, Col, Tabs, Upload, message } from 'antd';
import { 
  UploadOutlined, 
  DownloadOutlined, 
  FileTextOutlined, 
  FilePdfOutlined,
  FileExcelOutlined,
  FileWordOutlined,
  FolderOpenOutlined 
} from '@ant-design/icons';
import { useQuery } from '@tanstack/react-query';
import { documentsApi, Document } from '@/services/api/documents';
import { formatDate, formatFileSize } from '@/utils/formatters';
import { PAGINATION } from '@/config/constants';

const { Title } = Typography;
const { TabPane } = Tabs;

const Documents: React.FC = () => {
  const [activeCategory, setActiveCategory] = useState<string>('all');
  const [filter] = useState({});

  // 문서 목록 조회
  const { data: documentData, isLoading } = useQuery({
    queryKey: ['documents', activeCategory, filter],
    queryFn: () => documentsApi.legacy.getList({
      ...filter,
      category: activeCategory === 'all' ? undefined : activeCategory,
    }),
  });

  // 문서 카테고리별 통계
  const { data: categoryStats } = useQuery({
    queryKey: ['document-category-stats'],
    queryFn: () => documentsApi.legacy.getCategories().then(cats => ({
      total: cats.reduce((sum, cat) => sum + cat.document_count, 0),
      manual: cats.find(c => c.id === 'manual')?.document_count || 0,
      legal_form: cats.find(c => c.id === 'legal_form')?.document_count || 0,
      regulation: cats.find(c => c.id === 'regulation')?.document_count || 0,
      report: cats.find(c => c.id === 'report')?.document_count || 0,
      training: cats.find(c => c.id === 'training')?.document_count || 0,
      template: cats.find(c => c.id === 'template')?.document_count || 0,
      etc: cats.find(c => c.id === 'etc')?.document_count || 0,
      monthly_uploads: 0,
      total_size: 0,
      monthly_downloads: 0
    })),
  });

  const getFileIcon = (fileType: string) => {
    const iconMap = {
      pdf: <FilePdfOutlined style={{ color: '#ff4d4f', fontSize: 16 }} />,
      excel: <FileExcelOutlined style={{ color: '#52c41a', fontSize: 16 }} />,
      word: <FileWordOutlined style={{ color: '#1890ff', fontSize: 16 }} />,
      default: <FileTextOutlined style={{ fontSize: 16 }} />,
    };
    return iconMap[fileType as keyof typeof iconMap] || iconMap.default;
  };

  const columns = [
    {
      title: '문서명',
      key: 'title',
      width: 300,
      render: (record: Document) => (
        <Space>
          {getFileIcon(record.file_type)}
          <div>
            <div>{record.title}</div>
            <div style={{ fontSize: 12, color: '#999' }}>{record.file_path.split('/').pop()}</div>
          </div>
        </Space>
      ),
    },
    {
      title: '카테고리',
      dataIndex: 'category',
      key: 'category',
      width: 120,
      render: (category: string) => {
        const categoryMap: Record<string, { color: string; text: string }> = {
          manual: { color: 'blue', text: '업무매뉴얼' },
          legal_form: { color: 'red', text: '법정서식' },
          regulation: { color: 'purple', text: '규정/지침' },
          report: { color: 'green', text: '보고서' },
          training: { color: 'orange', text: '교육자료' },
          template: { color: 'cyan', text: '템플릿' },
          etc: { color: 'default', text: '기타' },
        };
        const config = categoryMap[category] || { color: 'default', text: category };
        return <Tag color={config.color}>{config.text}</Tag>;
      },
    },
    {
      title: '파일크기',
      dataIndex: 'file_size',
      key: 'file_size',
      width: 100,
      render: (size: number) => formatFileSize(size),
    },
    {
      title: '버전',
      dataIndex: 'version',
      key: 'version',
      width: 80,
      render: (version: string) => `v${version}`,
    },
    {
      title: '상태',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (status: string) => {
        const statusMap = {
          active: { color: 'success', text: '활성' },
          archived: { color: 'default', text: '보관' },
          draft: { color: 'warning', text: '초안' },
        };
        const config = statusMap[status as keyof typeof statusMap] || { color: 'default', text: status };
        return <Tag color={config.color}>{config.text}</Tag>;
      },
    },
    {
      title: '최종수정일',
      dataIndex: 'updated_at',
      key: 'updated_at',
      width: 120,
      render: (date: string) => formatDate(date),
    },
    {
      title: '수정자',
      dataIndex: 'updated_by',
      key: 'updated_by',
      width: 100,
    },
    {
      title: '다운로드',
      dataIndex: 'download_count',
      key: 'download_count',
      width: 80,
      render: (count: number) => `${count}회`,
    },
    {
      title: '작업',
      key: 'action',
      width: 150,
      fixed: 'right' as const,
      render: (_: any, record: Document) => (
        <Space size="small">
          <Button
            type="link"
            size="small"
            icon={<DownloadOutlined />}
            onClick={() => handleDownload(record)}
          >
            다운로드
          </Button>
          <Button
            type="link"
            size="small"
            onClick={() => handleEdit(record)}
          >
            편집
          </Button>
        </Space>
      ),
    },
  ];

  const handleDownload = async (document: Document) => {
    try {
      await documentsApi.legacy.download(document.id);
      message.success('다운로드가 시작되었습니다.');
    } catch (error) {
      message.error('다운로드 중 오류가 발생했습니다.');
    }
  };

  const handleEdit = (document: Document) => {
    // TODO: 문서 편집 페이지로 이동
    console.log('Edit document:', document);
  };

  const handleUpload = (info: any) => {
    if (info.file.status === 'done') {
      message.success(`${info.file.name} 파일이 업로드되었습니다.`);
    } else if (info.file.status === 'error') {
      message.error(`${info.file.name} 파일 업로드가 실패했습니다.`);
    }
  };

  const categoryTabs = [
    { key: 'all', label: '전체', count: categoryStats?.total || 0 },
    { key: 'manual', label: '업무매뉴얼', count: categoryStats?.manual || 0 },
    { key: 'legal_form', label: '법정서식', count: categoryStats?.legal_form || 0 },
    { key: 'regulation', label: '규정/지침', count: categoryStats?.regulation || 0 },
    { key: 'report', label: '보고서', count: categoryStats?.report || 0 },
    { key: 'training', label: '교육자료', count: categoryStats?.training || 0 },
    { key: 'template', label: '템플릿', count: categoryStats?.template || 0 },
    { key: 'etc', label: '기타', count: categoryStats?.etc || 0 },
  ];

  return (
    <div>
      <Title level={2}>문서 관리</Title>

      {/* 문서 통계 */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Space direction="vertical" style={{ width: '100%' }}>
              <span style={{ color: '#999' }}>전체 문서</span>
              <span style={{ fontSize: 24, fontWeight: 'bold' }}>
                {categoryStats?.total || 0}개
              </span>
            </Space>
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Space direction="vertical" style={{ width: '100%' }}>
              <span style={{ color: '#999' }}>이번 달 업로드</span>
              <span style={{ fontSize: 24, fontWeight: 'bold' }}>
                {categoryStats?.monthly_uploads || 0}개
              </span>
            </Space>
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Space direction="vertical" style={{ width: '100%' }}>
              <span style={{ color: '#999' }}>총 용량</span>
              <span style={{ fontSize: 24, fontWeight: 'bold' }}>
                {formatFileSize(categoryStats?.total_size || 0)}
              </span>
            </Space>
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Space direction="vertical" style={{ width: '100%' }}>
              <span style={{ color: '#999' }}>이번 달 다운로드</span>
              <span style={{ fontSize: 24, fontWeight: 'bold' }}>
                {categoryStats?.monthly_downloads || 0}회
              </span>
            </Space>
          </Card>
        </Col>
      </Row>

      {/* 문서 목록 */}
      <Card
        extra={
          <Space>
            <Upload
              onChange={handleUpload}
              showUploadList={false}
              customRequest={({ file, onSuccess }) => {
                // TODO: 실제 업로드 구현
                setTimeout(() => {
                  onSuccess?.({}, file);
                }, 1000);
              }}
            >
              <Button icon={<UploadOutlined />}>문서 업로드</Button>
            </Upload>
            <Button icon={<FolderOpenOutlined />}>
              폴더 관리
            </Button>
          </Space>
        }
      >
        <Tabs activeKey={activeCategory} onChange={setActiveCategory}>
          {categoryTabs.map(tab => (
            <TabPane 
              tab={
                <span>
                  {tab.label} <Tag>{tab.count}</Tag>
                </span>
              } 
              key={tab.key} 
            />
          ))}
        </Tabs>

        <Table
          columns={columns}
          dataSource={documentData || []}
          loading={isLoading}
          rowKey="id"
          scroll={{ x: 1400 }}
          pagination={{
            total: documentData?.length || 0,
            pageSize: PAGINATION.DEFAULT_PAGE_SIZE,
            current: 1,
            showSizeChanger: true,
            pageSizeOptions: PAGINATION.PAGE_SIZE_OPTIONS.map(String),
            showTotal: (total) => `총 ${total}개`,
          }}
        />
      </Card>
    </div>
  );
};

export default Documents;