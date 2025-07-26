import { Table, TableProps } from 'antd';
import { useMediaQuery } from '@/hooks/useMediaQuery';
import styled from 'styled-components';

const ResponsiveTableWrapper = styled.div`
  .ant-table-wrapper {
    .ant-table {
      font-size: 14px;
    }
    
    @media (max-width: 768px) {
      .ant-table-thead > tr > th {
        padding: 8px 8px;
        font-size: 12px;
      }
      
      .ant-table-tbody > tr > td {
        padding: 8px 8px;
        font-size: 12px;
      }
    }
  }
`;

export interface DataTableProps<T> extends TableProps<T> {
  mobileColumns?: TableProps<T>['columns'];
}

export function DataTable<T extends object>({ 
  columns, 
  mobileColumns, 
  ...props 
}: DataTableProps<T>) {
  const isMobile = useMediaQuery('(max-width: 768px)');
  
  return (
    <ResponsiveTableWrapper>
      <Table<T>
        {...props}
        columns={isMobile && mobileColumns ? mobileColumns : columns}
        scroll={{ x: isMobile ? 'max-content' : undefined }}
        pagination={{
          ...props.pagination,
          size: isMobile ? 'small' : 'default',
          showSizeChanger: !isMobile,
        }}
      />
    </ResponsiveTableWrapper>
  );
}