import { ThemeConfig } from 'antd';

export const safeworkTheme: ThemeConfig = {
  token: {
    colorPrimary: '#1890ff',
    colorSuccess: '#52c41a',
    colorWarning: '#faad14',
    colorError: '#f5222d',
    fontFamily: "'Pretendard', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
    fontSize: 14,
    borderRadius: 6,
    controlHeight: 40,
  },
  components: {
    Button: {
      controlHeight: 40,
      fontSize: 16,
    },
    Table: {
      headerBg: '#fafafa',
      rowHoverBg: '#f5f5f5',
    },
    Card: {
      borderRadiusLG: 8,
      boxShadow: '0 2px 8px rgba(0,0,0,0.09)',
    },
  },
};
