import { api } from './baseApi';
import { API_ENDPOINTS } from '@/config/constants';

// 문서 타입 정의
export interface Document {
  id: number;
  title: string;
  category: string;
  file_path: string;
  file_size: number;
  file_type: string;
  description?: string;
  version: string;
  is_template: boolean;
  created_at: string;
  updated_at: string;
  created_by?: string;
  updated_by?: string;
}

export interface DocumentCategory {
  id: string;
  name: string;
  description?: string;
  icon?: string;
  document_count: number;
}

export interface IntegratedDocument {
  id: number;
  title: string;
  category: 
    | '업무매뉴얼'
    | '법정서식'
    | '회사규정'
    | '교육자료'
    | '점검표'
    | '보고서양식'
    | '인증서'
    | '계약서'
    | '안내문'
    | '기타';
  file_path: string;
  file_type: 'pdf' | 'docx' | 'xlsx' | 'pptx';
  file_size: number;
  description?: string;
  tags?: string[];
  is_editable: boolean;
  last_accessed?: string;
  access_count: number;
  created_at: string;
  updated_at: string;
  created_by?: string;
}

export interface DocumentEdit {
  text_inserts?: {
    text: string;
    x: number;
    y: number;
    page?: number;
    font_size?: number;
    font_family?: string;
    color?: string;
  }[];
  image_inserts?: {
    image_data: string; // base64
    x: number;
    y: number;
    width: number;
    height: number;
    page?: number;
  }[];
  cell_data?: Record<string, any>; // For Excel
  slide_updates?: any[]; // For PowerPoint
}

export interface DocumentFilter {
  category?: string;
  search?: string;
  is_template?: boolean;
  file_type?: string;
  created_by?: string;
  start_date?: string;
  end_date?: string;
  page?: number;
  pageSize?: number;
}

// 문서 API 서비스
export const documentsApi = {
  // 기본 문서 관리
  legacy: {
    // 문서 목록 조회
    getList: async (filter?: DocumentFilter) => {
      return api.get<Document[]>(API_ENDPOINTS.DOCUMENTS, {
        params: filter,
      });
    },

    // 문서 카테고리 조회
    getCategories: async () => {
      return api.get<DocumentCategory[]>(`${API_ENDPOINTS.DOCUMENTS}/categories`);
    },

    // 문서 다운로드
    download: async (id: number) => {
      const doc = await api.get<Document>(`${API_ENDPOINTS.DOCUMENTS}/${id}`);
      return api.download(
        `${API_ENDPOINTS.DOCUMENTS}/${id}/download`,
        doc.title
      );
    },

    // PDF 양식 작성
    fillPdfForm: async (templateId: number, data: Record<string, any>) => {
      return api.post<{ file_url: string }>(
        `${API_ENDPOINTS.DOCUMENTS}/${templateId}/fill-form`,
        data
      );
    },

    // 문서 업로드
    upload: async (file: File, metadata: {
      title: string;
      category: string;
      description?: string;
      is_template?: boolean;
    }) => {
      return api.upload<Document>(
        `${API_ENDPOINTS.DOCUMENTS}/upload`,
        file,
        metadata
      );
    },

    // 문서 삭제
    delete: async (id: number) => {
      return api.delete(`${API_ENDPOINTS.DOCUMENTS}/${id}`);
    },
  },

  // 통합 문서 관리 (편집 가능)
  integrated: {
    // 문서 목록 조회
    getList: async (filter?: {
      category?: string;
      search?: string;
      file_type?: string;
      tags?: string[];
      page?: number;
      pageSize?: number;
    }) => {
      return api.get<IntegratedDocument[]>(API_ENDPOINTS.INTEGRATED_DOCUMENTS, {
        params: filter,
      });
    },

    // 문서 상세 조회
    getById: async (id: number) => {
      return api.get<IntegratedDocument>(`${API_ENDPOINTS.INTEGRATED_DOCUMENTS}/${id}`);
    },

    // 문서 미리보기
    preview: async (id: number) => {
      return api.get<{ preview_url: string; pages: number }>(
        `${API_ENDPOINTS.INTEGRATED_DOCUMENTS}/${id}/preview`
      );
    },

    // 문서 편집
    edit: async (id: number, edits: DocumentEdit) => {
      return api.post<{ success: boolean; file_url: string }>(
        `${API_ENDPOINTS.INTEGRATED_DOCUMENTS}/${id}/edit`,
        edits
      );
    },

    // 문서 복사
    duplicate: async (id: number, newTitle: string) => {
      return api.post<IntegratedDocument>(
        `${API_ENDPOINTS.INTEGRATED_DOCUMENTS}/${id}/duplicate`,
        { title: newTitle }
      );
    },

    // 문서 업로드
    upload: async (file: File, metadata: {
      title: string;
      category: IntegratedDocument['category'];
      description?: string;
      tags?: string[];
      is_editable?: boolean;
    }) => {
      return api.upload<IntegratedDocument>(
        `${API_ENDPOINTS.INTEGRATED_DOCUMENTS}/upload`,
        file,
        metadata
      );
    },

    // 문서 다운로드
    download: async (id: number) => {
      const doc = await api.get<IntegratedDocument>(`${API_ENDPOINTS.INTEGRATED_DOCUMENTS}/${id}`);
      return api.download(
        `${API_ENDPOINTS.INTEGRATED_DOCUMENTS}/${id}/download`,
        doc.title
      );
    },

    // 문서 삭제
    delete: async (id: number) => {
      return api.delete(`${API_ENDPOINTS.INTEGRATED_DOCUMENTS}/${id}`);
    },

    // 태그 관리
    getTags: async () => {
      return api.get<string[]>(`${API_ENDPOINTS.INTEGRATED_DOCUMENTS}/tags`);
    },

    addTags: async (id: number, tags: string[]) => {
      return api.post(`${API_ENDPOINTS.INTEGRATED_DOCUMENTS}/${id}/tags`, { tags });
    },

    removeTags: async (id: number, tags: string[]) => {
      return api.delete(`${API_ENDPOINTS.INTEGRATED_DOCUMENTS}/${id}/tags`, {
        data: { tags }
      });
    },

    // 버전 관리
    getVersions: async (id: number) => {
      return api.get<{
        versions: {
          version: string;
          created_at: string;
          created_by: string;
          changes: string;
        }[];
      }>(`${API_ENDPOINTS.INTEGRATED_DOCUMENTS}/${id}/versions`);
    },

    restoreVersion: async (id: number, version: string) => {
      return api.post(`${API_ENDPOINTS.INTEGRATED_DOCUMENTS}/${id}/restore`, { version });
    },

    // 템플릿 관리
    getTemplates: async (category?: string) => {
      return api.get<IntegratedDocument[]>(`${API_ENDPOINTS.INTEGRATED_DOCUMENTS}/templates`, {
        params: { category }
      });
    },

    createFromTemplate: async (templateId: number, data: {
      title: string;
      replacements?: Record<string, string>;
    }) => {
      return api.post<IntegratedDocument>(
        `${API_ENDPOINTS.INTEGRATED_DOCUMENTS}/templates/${templateId}/create`,
        data
      );
    },
  },

  // 보고서 생성
  reports: {
    // 건강검진 결과 보고서
    generateHealthExamReport: async (data: {
      year: number;
      department?: string;
      include_charts?: boolean;
    }) => {
      return api.post<{ file_url: string }>(
        `${API_ENDPOINTS.DOCUMENTS}/reports/health-exam`,
        data
      );
    },

    // 사고 통계 보고서
    generateAccidentReport: async (data: {
      start_date: string;
      end_date: string;
      department?: string;
      include_analysis?: boolean;
    }) => {
      return api.post<{ file_url: string }>(
        `${API_ENDPOINTS.DOCUMENTS}/reports/accident`,
        data
      );
    },

    // 교육 이수 보고서
    generateEducationReport: async (data: {
      year: number;
      quarter?: number;
      department?: string;
    }) => {
      return api.post<{ file_url: string }>(
        `${API_ENDPOINTS.DOCUMENTS}/reports/education`,
        data
      );
    },

    // 종합 보건관리 보고서
    generateComprehensiveReport: async (data: {
      year: number;
      type: 'monthly' | 'quarterly' | 'annual';
    }) => {
      return api.post<{ file_url: string }>(
        `${API_ENDPOINTS.DOCUMENTS}/reports/comprehensive`,
        data
      );
    },
  },
};