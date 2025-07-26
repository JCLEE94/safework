import { ThemeConfig } from 'antd';

// 디자인 토큰 정의
export const designTokens = {
  // 브랜드 컬러
  colors: {
    primary: {
      50: '#E6F4FF',
      100: '#BAE0FF',
      200: '#91CAFF',
      300: '#69B1FF',
      400: '#4096FF',
      500: '#1677FF', // 주 브랜드 색상
      600: '#0958D9',
      700: '#003EB3',
      800: '#002C8C',
      900: '#001D66',
    },
    success: {
      50: '#F6FFED',
      100: '#D9F7BE',
      200: '#B7EB8F',
      300: '#95DE64',
      400: '#73D13D',
      500: '#52C41A', // 성공 색상
      600: '#389E0D',
      700: '#237804',
      800: '#135200',
      900: '#092B00',
    },
    warning: {
      50: '#FFFBE6',
      100: '#FFF1B8',
      200: '#FFE58F',
      300: '#FFD666',
      400: '#FFC53D',
      500: '#FAAD14', // 경고 색상
      600: '#D48806',
      700: '#AD6800',
      800: '#874D00',
      900: '#613400',
    },
    error: {
      50: '#FFF1F0',
      100: '#FFCCC7',
      200: '#FFA39E',
      300: '#FF7875',
      400: '#FF4D4F',
      500: '#F5222D', // 오류 색상
      600: '#CF1322',
      700: '#A8071A',
      800: '#820014',
      900: '#5C0011',
    },
    neutral: {
      50: '#FAFAFA',
      100: '#F5F5F5',
      200: '#E8E8E8',
      300: '#D9D9D9',
      400: '#BFBFBF',
      500: '#8C8C8C',
      600: '#595959',
      700: '#434343',
      800: '#262626',
      900: '#1F1F1F',
    },
  },
  // 타이포그래피
  typography: {
    fontFamily: "'Pretendard', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
    fontSize: {
      xs: 12,
      sm: 14,
      base: 16,
      lg: 18,
      xl: 20,
      '2xl': 24,
      '3xl': 30,
      '4xl': 38,
      '5xl': 46,
    },
    fontWeight: {
      regular: 400,
      medium: 500,
      semibold: 600,
      bold: 700,
    },
    lineHeight: {
      tight: 1.2,
      normal: 1.5,
      relaxed: 1.75,
    },
  },
  // 간격
  spacing: {
    xs: 4,
    sm: 8,
    md: 16,
    lg: 24,
    xl: 32,
    '2xl': 48,
    '3xl': 64,
  },
  // 테두리
  borderRadius: {
    sm: 4,
    base: 8,
    md: 12,
    lg: 16,
    xl: 24,
    full: 9999,
  },
  // 그림자
  shadows: {
    sm: '0 1px 2px 0 rgba(0, 0, 0, 0.05)',
    base: '0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06)',
    md: '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
    lg: '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)',
    xl: '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)',
  },
  // 애니메이션
  transitions: {
    fast: '150ms',
    base: '250ms',
    slow: '350ms',
    slower: '500ms',
  },
  // 브레이크포인트
  breakpoints: {
    xs: 480,
    sm: 576,
    md: 768,
    lg: 992,
    xl: 1200,
    xxl: 1600,
  },
};

// Ant Design 테마 설정
export const safeworkTheme: ThemeConfig = {
  token: {
    // 색상
    colorPrimary: designTokens.colors.primary[500],
    colorSuccess: designTokens.colors.success[500],
    colorWarning: designTokens.colors.warning[500],
    colorError: designTokens.colors.error[500],
    colorInfo: designTokens.colors.primary[500],
    colorTextBase: designTokens.colors.neutral[900],
    colorBgBase: '#ffffff',
    
    // 타이포그래피
    fontFamily: designTokens.typography.fontFamily,
    fontSize: designTokens.typography.fontSize.sm,
    fontSizeHeading1: designTokens.typography.fontSize['4xl'],
    fontSizeHeading2: designTokens.typography.fontSize['3xl'],
    fontSizeHeading3: designTokens.typography.fontSize['2xl'],
    fontSizeHeading4: designTokens.typography.fontSize.xl,
    fontSizeHeading5: designTokens.typography.fontSize.lg,
    
    // 레이아웃
    lineHeight: designTokens.typography.lineHeight.normal,
    borderRadius: designTokens.borderRadius.base,
    controlHeight: 40,
    controlHeightLG: 48,
    controlHeightSM: 32,
    
    // 간격
    marginXS: designTokens.spacing.xs,
    marginSM: designTokens.spacing.sm,
    margin: designTokens.spacing.md,
    marginMD: designTokens.spacing.md,
    marginLG: designTokens.spacing.lg,
    marginXL: designTokens.spacing.xl,
    
    // 그림자
    boxShadow: designTokens.shadows.base,
    boxShadowSecondary: designTokens.shadows.md,
  },
  components: {
    Button: {
      controlHeight: 40,
      controlHeightLG: 48,
      controlHeightSM: 32,
      fontSize: designTokens.typography.fontSize.base,
      fontSizeLG: designTokens.typography.fontSize.lg,
      fontSizeSM: designTokens.typography.fontSize.sm,
      fontWeight: designTokens.typography.fontWeight.medium,
      borderRadius: designTokens.borderRadius.base,
      boxShadow: 'none',
      primaryShadow: 'none',
      dangerShadow: 'none',
      defaultShadow: 'none',
    },
    Input: {
      controlHeight: 40,
      controlHeightLG: 48,
      controlHeightSM: 32,
      fontSize: designTokens.typography.fontSize.base,
      borderRadius: designTokens.borderRadius.base,
    },
    Select: {
      controlHeight: 40,
      controlHeightLG: 48,
      controlHeightSM: 32,
      fontSize: designTokens.typography.fontSize.base,
      borderRadius: designTokens.borderRadius.base,
    },
    Table: {
      headerBg: designTokens.colors.neutral[50],
      headerColor: designTokens.colors.neutral[900],
      headerBorderRadius: designTokens.borderRadius.base,
      rowHoverBg: designTokens.colors.primary[50],
      fontSize: designTokens.typography.fontSize.sm,
      cellPaddingBlock: 12,
      cellPaddingInline: 16,
    },
    Card: {
      borderRadiusLG: designTokens.borderRadius.md,
      boxShadow: designTokens.shadows.sm,
      paddingLG: designTokens.spacing.lg,
      padding: designTokens.spacing.md,
    },
    Modal: {
      borderRadiusLG: designTokens.borderRadius.md,
      boxShadow: designTokens.shadows.xl,
      paddingContentHorizontalLG: designTokens.spacing.lg,
    },
    Drawer: {
      paddingLG: designTokens.spacing.lg,
    },
    Menu: {
      itemBg: 'transparent',
      itemSelectedBg: designTokens.colors.primary[50],
      itemSelectedColor: designTokens.colors.primary[600],
      itemActiveBg: designTokens.colors.primary[50],
      itemHoverBg: designTokens.colors.neutral[50],
      fontSize: designTokens.typography.fontSize.base,
      itemHeight: 48,
      itemMarginInline: 8,
      borderRadius: designTokens.borderRadius.base,
    },
    Layout: {
      headerBg: '#ffffff',
      headerColor: designTokens.colors.neutral[900],
      headerHeight: 64,
      siderBg: '#ffffff',
      bodyBg: designTokens.colors.neutral[50],
      footerBg: '#ffffff',
    },
    Form: {
      labelColor: designTokens.colors.neutral[700],
      labelFontSize: designTokens.typography.fontSize.sm,
      itemMarginBottom: designTokens.spacing.lg,
    },
    Alert: {
      borderRadiusLG: designTokens.borderRadius.base,
      paddingContentVerticalLG: designTokens.spacing.md,
      paddingContentHorizontalLG: designTokens.spacing.lg,
    },
    Tag: {
      borderRadiusSM: designTokens.borderRadius.sm,
      defaultBg: designTokens.colors.neutral[100],
      defaultColor: designTokens.colors.neutral[700],
    },
    Badge: {
      textFontSize: designTokens.typography.fontSize.xs,
      textFontWeight: designTokens.typography.fontWeight.semibold,
    },
    Tooltip: {
      borderRadius: designTokens.borderRadius.base,
      boxShadowSecondary: designTokens.shadows.lg,
    },
    Divider: {
      colorSplit: designTokens.colors.neutral[200],
      marginLG: designTokens.spacing.lg,
    },
  },
};

// 다크 모드 테마 (향후 구현용)
export const darkTheme: ThemeConfig = {
  ...safeworkTheme,
  token: {
    ...safeworkTheme.token,
    colorBgBase: designTokens.colors.neutral[900],
    colorTextBase: designTokens.colors.neutral[50],
  },
  algorithm: undefined, // 다크 모드 알고리즘 적용 시 설정
};
