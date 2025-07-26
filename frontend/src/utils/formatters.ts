import dayjs from 'dayjs';
import { DATE_FORMATS } from '@/config/constants';

/**
 * 날짜 포맷팅
 */
export const formatDate = (date: string | Date | null | undefined, format: string = DATE_FORMATS.DATE): string => {
  if (!date) return '-';
  return dayjs(date).format(format);
};

/**
 * 날짜/시간 포맷팅
 */
export const formatDateTime = (date: string | Date | null | undefined): string => {
  return formatDate(date, DATE_FORMATS.DATETIME);
};

/**
 * 상대 시간 포맷팅 (예: 3일 전, 2시간 전)
 */
export const formatRelativeTime = (date: string | Date | null | undefined): string => {
  if (!date) return '-';
  
  const now = dayjs();
  const target = dayjs(date);
  const diffInSeconds = now.diff(target, 'second');
  
  if (diffInSeconds < 60) return '방금 전';
  if (diffInSeconds < 3600) return `${Math.floor(diffInSeconds / 60)}분 전`;
  if (diffInSeconds < 86400) return `${Math.floor(diffInSeconds / 3600)}시간 전`;
  if (diffInSeconds < 2592000) return `${Math.floor(diffInSeconds / 86400)}일 전`;
  if (diffInSeconds < 31536000) return `${Math.floor(diffInSeconds / 2592000)}개월 전`;
  
  return `${Math.floor(diffInSeconds / 31536000)}년 전`;
};

/**
 * 숫자 포맷팅 (천 단위 콤마)
 */
export const formatNumber = (num: number | null | undefined): string => {
  if (num === null || num === undefined) return '0';
  return num.toLocaleString('ko-KR');
};

/**
 * 퍼센트 포맷팅
 */
export const formatPercent = (value: number | null | undefined, decimals = 1): string => {
  if (value === null || value === undefined) return '0%';
  return `${value.toFixed(decimals)}%`;
};

/**
 * 파일 크기 포맷팅
 */
export const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 Bytes';
  
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(2))} ${sizes[i]}`;
};

/**
 * 전화번호 포맷팅
 */
export const formatPhoneNumber = (phone: string | null | undefined): string => {
  if (!phone) return '-';
  
  const cleaned = phone.replace(/\D/g, '');
  
  if (cleaned.length === 11) {
    return cleaned.replace(/(\d{3})(\d{4})(\d{4})/, '$1-$2-$3');
  } else if (cleaned.length === 10) {
    return cleaned.replace(/(\d{3})(\d{3})(\d{4})/, '$1-$2-$3');
  }
  
  return phone;
};

/**
 * 사업자등록번호 포맷팅
 */
export const formatBusinessNumber = (num: string | null | undefined): string => {
  if (!num) return '-';
  
  const cleaned = num.replace(/\D/g, '');
  
  if (cleaned.length === 10) {
    return cleaned.replace(/(\d{3})(\d{2})(\d{5})/, '$1-$2-$3');
  }
  
  return num;
};

/**
 * 이름 마스킹 (개인정보보호)
 */
export const maskName = (name: string | null | undefined): string => {
  if (!name || name.length < 2) return '*';
  
  const firstChar = name.charAt(0);
  const masked = '*'.repeat(name.length - 1);
  
  return firstChar + masked;
};

/**
 * 이메일 마스킹
 */
export const maskEmail = (email: string | null | undefined): string => {
  if (!email) return '-';
  
  const [localPart, domain] = email.split('@');
  if (!localPart || !domain) return email;
  
  const maskedLocal = localPart.length > 3 
    ? localPart.substring(0, 3) + '***'
    : localPart.charAt(0) + '***';
    
  return `${maskedLocal}@${domain}`;
};

/**
 * 상태 라벨 한글화
 */
export const formatStatusLabel = (status: string, type: 'exam' | 'accident' | 'education'): string => {
  const labels: Record<string, Record<string, string>> = {
    exam: {
      draft: '초안',
      pending_approval: '승인 대기',
      approved: '승인됨',
      in_progress: '진행 중',
      completed: '완료',
      cancelled: '취소됨',
      scheduled: '예정',
      overdue: '기한 초과',
    },
    accident: {
      reported: '신고됨',
      investigating: '조사 중',
      resolved: '해결됨',
      closed: '종료',
    },
    education: {
      planned: '계획됨',
      in_progress: '진행 중',
      completed: '완료',
      cancelled: '취소됨',
    },
  };
  
  return labels[type]?.[status] || status;
};

/**
 * 검진 종류 라벨 한글화
 */
export const formatExamTypeLabel = (type: string): string => {
  const labels: Record<string, string> = {
    general: '일반건강진단',
    special: '특수건강진단',
    placement: '배치전건강진단',
    return_to_work: '복직건강진단',
  };
  
  return labels[type] || type;
};

/**
 * D-Day 계산 및 포맷팅
 */
export const formatDDay = (targetDate: string | Date | null | undefined): string => {
  if (!targetDate) return '-';
  
  const now = dayjs().startOf('day');
  const target = dayjs(targetDate).startOf('day');
  const diff = target.diff(now, 'day');
  
  if (diff === 0) return 'D-Day';
  if (diff > 0) return `D-${diff}`;
  return `D+${Math.abs(diff)}`;
};