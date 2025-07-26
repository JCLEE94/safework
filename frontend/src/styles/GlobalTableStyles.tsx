import { createGlobalStyle } from 'styled-components';
import { designTokens } from './theme';

export const GlobalTableStyles = createGlobalStyle`
  /* Ant Design 테이블 텍스트 오버플로우 처리 */
  .ant-table {
    /* 테이블 셀 기본 오버플로우 설정 */
    .ant-table-cell {
      position: relative;
      overflow: hidden;
      
      /* 긴 텍스트 처리 */
      &.ant-table-cell-ellipsis {
        overflow: hidden;
        white-space: nowrap;
        text-overflow: ellipsis;
        word-break: keep-all;
      }
    }
    
    /* 고정 컬럼 텍스트 오버플로우 */
    .ant-table-cell-fix-left,
    .ant-table-cell-fix-right {
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }
    
    /* 테이블 헤더 텍스트 오버플로우 */
    thead .ant-table-cell {
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }
    
    /* 반응형 테이블 스크롤 */
    .ant-table-content {
      overflow-x: auto;
      -webkit-overflow-scrolling: touch;
    }
  }
  
  /* 카드 컴포넌트 텍스트 오버플로우 */
  .ant-card {
    .ant-card-meta-title {
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }
    
    .ant-card-meta-description {
      overflow: hidden;
      text-overflow: ellipsis;
      display: -webkit-box;
      -webkit-line-clamp: 2;
      -webkit-box-orient: vertical;
    }
  }
  
  /* 태그 컴포넌트 오버플로우 */
  .ant-tag {
    max-width: 100%;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
  
  /* Select 드롭다운 텍스트 오버플로우 */
  .ant-select-item-option-content {
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
  
  /* Breadcrumb 텍스트 오버플로우 */
  .ant-breadcrumb-link {
    max-width: 200px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    display: inline-block;
    vertical-align: bottom;
  }
  
  /* Menu 아이템 텍스트 오버플로우 */
  .ant-menu-item,
  .ant-menu-submenu-title {
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
  
  /* 모바일 반응형 텍스트 처리 */
  @media (max-width: ${designTokens.breakpoints.md}px) {
    .ant-table-cell {
      padding: ${designTokens.spacing.xs}px ${designTokens.spacing.sm}px;
      font-size: ${designTokens.typography.fontSize.sm}px;
    }
    
    .ant-breadcrumb-link {
      max-width: 120px;
    }
  }
`;

export default GlobalTableStyles;