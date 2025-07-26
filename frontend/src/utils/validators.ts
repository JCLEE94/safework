/**
 * 이메일 유효성 검증
 */
export const isValidEmail = (email: string): boolean => {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(email);
};

/**
 * 전화번호 유효성 검증 (한국 번호)
 */
export const isValidPhoneNumber = (phone: string): boolean => {
  const phoneRegex = /^01[0-9]-?[0-9]{3,4}-?[0-9]{4}$/;
  return phoneRegex.test(phone.replace(/-/g, ''));
};

/**
 * 사업자등록번호 유효성 검증
 */
export const isValidBusinessNumber = (num: string): boolean => {
  const cleaned = num.replace(/-/g, '');
  if (cleaned.length !== 10) return false;
  
  // 사업자등록번호 검증 알고리즘
  const checkSum = [1, 3, 7, 1, 3, 7, 1, 3, 5];
  let sum = 0;
  
  for (let i = 0; i < 9; i++) {
    sum += parseInt(cleaned[i]) * checkSum[i];
  }
  
  sum += Math.floor((parseInt(cleaned[8]) * 5) / 10);
  const checkDigit = (10 - (sum % 10)) % 10;
  
  return checkDigit === parseInt(cleaned[9]);
};

/**
 * 주민등록번호 유효성 검증 (마스킹된 형태만 허용)
 */
export const isValidResidentNumber = (num: string): boolean => {
  // 앞 6자리-뒤 1자리****** 형태만 허용
  const maskedRegex = /^\d{6}-[1-4]\*{6}$/;
  return maskedRegex.test(num);
};

/**
 * 비밀번호 강도 검증
 */
export const validatePasswordStrength = (password: string): {
  isValid: boolean;
  errors: string[];
} => {
  const errors: string[] = [];
  
  if (password.length < 8) {
    errors.push('비밀번호는 8자 이상이어야 합니다');
  }
  
  if (!/[A-Z]/.test(password)) {
    errors.push('대문자를 포함해야 합니다');
  }
  
  if (!/[a-z]/.test(password)) {
    errors.push('소문자를 포함해야 합니다');
  }
  
  if (!/[0-9]/.test(password)) {
    errors.push('숫자를 포함해야 합니다');
  }
  
  if (!/[!@#$%^&*(),.?":{}|<>]/.test(password)) {
    errors.push('특수문자를 포함해야 합니다');
  }
  
  return {
    isValid: errors.length === 0,
    errors,
  };
};

/**
 * 날짜 유효성 검증
 */
export const isValidDate = (dateString: string): boolean => {
  const date = new Date(dateString);
  return date instanceof Date && !isNaN(date.getTime());
};

/**
 * 날짜 범위 유효성 검증
 */
export const isValidDateRange = (startDate: string, endDate: string): boolean => {
  if (!isValidDate(startDate) || !isValidDate(endDate)) return false;
  
  const start = new Date(startDate);
  const end = new Date(endDate);
  
  return start <= end;
};

/**
 * 파일 확장자 검증
 */
export const isValidFileExtension = (filename: string, allowedExtensions: string[]): boolean => {
  const extension = filename.split('.').pop()?.toLowerCase();
  if (!extension) return false;
  
  return allowedExtensions.includes(`.${extension}`);
};

/**
 * 파일 크기 검증
 */
export const isValidFileSize = (sizeInBytes: number, maxSizeInMB: number): boolean => {
  const maxSizeInBytes = maxSizeInMB * 1024 * 1024;
  return sizeInBytes <= maxSizeInBytes;
};

/**
 * URL 유효성 검증
 */
export const isValidUrl = (url: string): boolean => {
  try {
    new URL(url);
    return true;
  } catch {
    return false;
  }
};

/**
 * 한글 이름 유효성 검증
 */
export const isValidKoreanName = (name: string): boolean => {
  const koreanNameRegex = /^[가-힣]{2,5}$/;
  return koreanNameRegex.test(name);
};

/**
 * 영문 이름 유효성 검증
 */
export const isValidEnglishName = (name: string): boolean => {
  const englishNameRegex = /^[a-zA-Z\s]{2,50}$/;
  return englishNameRegex.test(name);
};

/**
 * 숫자만 포함 검증
 */
export const isNumericOnly = (value: string): boolean => {
  return /^\d+$/.test(value);
};

/**
 * 양수 검증
 */
export const isPositiveNumber = (value: number): boolean => {
  return value > 0;
};

/**
 * 범위 내 숫자 검증
 */
export const isNumberInRange = (value: number, min: number, max: number): boolean => {
  return value >= min && value <= max;
};

/**
 * Form 필드 검증 헬퍼
 */
export const createValidator = <T>(
  validationFn: (value: T) => boolean,
  errorMessage: string
) => {
  return (_: any, value: T) => {
    if (!value) {
      return Promise.reject(new Error('필수 입력 항목입니다'));
    }
    
    if (!validationFn(value)) {
      return Promise.reject(new Error(errorMessage));
    }
    
    return Promise.resolve();
  };
};