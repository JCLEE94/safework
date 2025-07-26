import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Button,
  Chip,
  TextField,
  MenuItem,
  Grid,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Alert,
  CircularProgress,
  IconButton,
  Tooltip,
  Card,
  CardContent,
  FormControl,
  InputLabel,
  Select
} from '@mui/material';
import {
  Visibility as VisibilityIcon,
  Download as DownloadIcon,
  Upload as UploadIcon,
  Edit as EditIcon,
  Assessment as AssessmentIcon,
  FilterList as FilterListIcon
} from '@mui/icons-material';
import { healthExamManagementApi, ExamCategory } from '../../api/healthExamManagement';
import { format } from 'date-fns';
import { ko } from 'date-fns/locale';

interface ExamResult {
  id: number;
  worker_id: number;
  worker_name: string;
  employee_id: string;
  exam_date: string;
  exam_type: ExamCategory;
  institution_name: string;
  result_grade: string;
  abnormal_findings?: string[];
  follow_up_required: boolean;
  follow_up_date?: string;
  doctor_opinion?: string;
  pdf_file_path?: string;
  created_at: string;
}

export default function ExamResultManagement() {
  const [results, setResults] = useState<ExamResult[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedResult, setSelectedResult] = useState<ExamResult | null>(null);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [uploadDialogOpen, setUploadDialogOpen] = useState(false);
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  
  // Filter states
  const [filterYear, setFilterYear] = useState<number>(new Date().getFullYear());
  const [filterExamType, setFilterExamType] = useState<string>('');
  const [filterGrade, setFilterGrade] = useState<string>('');
  const [searchTerm, setSearchTerm] = useState<string>('');

  useEffect(() => {
    fetchResults();
  }, [filterYear, filterExamType, filterGrade]);

  const fetchResults = async () => {
    try {
      setLoading(true);
      // This would need to be implemented in the API
      const response = await fetch(`/api/v1/health-exam-management/results?year=${filterYear}${filterExamType ? `&exam_type=${filterExamType}` : ''}${filterGrade ? `&grade=${filterGrade}` : ''}`);
      if (response.ok) {
        const data = await response.json();
        setResults(data);
      }
    } catch (err) {
      console.error('결과 조회 실패:', err);
      setError('검진 결과를 불러오는데 실패했습니다.');
    } finally {
      setLoading(false);
    }
  };

  const handleViewResult = (result: ExamResult) => {
    setSelectedResult(result);
    setDialogOpen(true);
  };

  const handleDownloadResult = async (result: ExamResult) => {
    if (result.pdf_file_path) {
      window.open(`/api/v1/health-exam-management/results/${result.id}/download`, '_blank');
    }
  };

  const handleEditResult = (result: ExamResult) => {
    setSelectedResult(result);
    setEditDialogOpen(true);
  };

  const getGradeColor = (grade: string) => {
    switch (grade) {
      case 'A': return 'success';
      case 'B': return 'info';
      case 'C': return 'warning';
      case 'D': case 'R': return 'error';
      default: return 'default';
    }
  };

  const filteredResults = results.filter(result => {
    if (searchTerm) {
      const searchLower = searchTerm.toLowerCase();
      return result.worker_name.toLowerCase().includes(searchLower) ||
             result.employee_id.toLowerCase().includes(searchLower);
    }
    return true;
  });

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight={400}>
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return <Alert severity="error">{error}</Alert>;
  }

  return (
    <Box>
      {/* 필터 섹션 */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Grid container spacing={2} alignItems="center">
            <Grid item xs={12} md={3}>
              <FormControl fullWidth size="small">
                <InputLabel>검진년도</InputLabel>
                <Select
                  value={filterYear}
                  label="검진년도"
                  onChange={(e) => setFilterYear(Number(e.target.value))}
                >
                  {[2024, 2025, 2026].map(year => (
                    <MenuItem key={year} value={year}>{year}년</MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} md={3}>
              <FormControl fullWidth size="small">
                <InputLabel>검진종류</InputLabel>
                <Select
                  value={filterExamType}
                  label="검진종류"
                  onChange={(e) => setFilterExamType(e.target.value)}
                >
                  <MenuItem value="">전체</MenuItem>
                  {Object.entries(ExamCategory).map(([key, value]) => (
                    <MenuItem key={key} value={value}>{value}</MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} md={3}>
              <FormControl fullWidth size="small">
                <InputLabel>결과등급</InputLabel>
                <Select
                  value={filterGrade}
                  label="결과등급"
                  onChange={(e) => setFilterGrade(e.target.value)}
                >
                  <MenuItem value="">전체</MenuItem>
                  <MenuItem value="A">A (정상)</MenuItem>
                  <MenuItem value="B">B (경미한 이상)</MenuItem>
                  <MenuItem value="C">C (질환 의심)</MenuItem>
                  <MenuItem value="D">D (유질환)</MenuItem>
                  <MenuItem value="R">R (재검 필요)</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} md={3}>
              <TextField
                fullWidth
                size="small"
                placeholder="이름 또는 사번 검색"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                InputProps={{
                  startAdornment: <FilterListIcon sx={{ mr: 1, color: 'text.secondary' }} />
                }}
              />
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {/* 액션 버튼 */}
      <Box display="flex" justifyContent="space-between" mb={2}>
        <Typography variant="h6">
          검진 결과 목록 ({filteredResults.length}건)
        </Typography>
        <Box>
          <Button
            variant="outlined"
            startIcon={<UploadIcon />}
            onClick={() => setUploadDialogOpen(true)}
            sx={{ mr: 1 }}
          >
            결과 일괄 업로드
          </Button>
          <Button
            variant="contained"
            startIcon={<AssessmentIcon />}
          >
            통계 보고서
          </Button>
        </Box>
      </Box>

      {/* 결과 테이블 */}
      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>사번</TableCell>
              <TableCell>이름</TableCell>
              <TableCell>검진일</TableCell>
              <TableCell>검진종류</TableCell>
              <TableCell>검진기관</TableCell>
              <TableCell align="center">결과등급</TableCell>
              <TableCell align="center">후속조치</TableCell>
              <TableCell align="center">작업</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {filteredResults.length > 0 ? (
              filteredResults.map((result) => (
                <TableRow key={result.id}>
                  <TableCell>{result.employee_id}</TableCell>
                  <TableCell>{result.worker_name}</TableCell>
                  <TableCell>
                    {format(new Date(result.exam_date), 'yyyy-MM-dd')}
                  </TableCell>
                  <TableCell>{result.exam_type}</TableCell>
                  <TableCell>{result.institution_name}</TableCell>
                  <TableCell align="center">
                    <Chip
                      label={result.result_grade}
                      color={getGradeColor(result.result_grade)}
                      size="small"
                    />
                  </TableCell>
                  <TableCell align="center">
                    {result.follow_up_required ? (
                      <Chip label="필요" color="warning" size="small" />
                    ) : (
                      <Chip label="불필요" color="default" size="small" />
                    )}
                  </TableCell>
                  <TableCell align="center">
                    <Tooltip title="상세보기">
                      <IconButton
                        size="small"
                        onClick={() => handleViewResult(result)}
                      >
                        <VisibilityIcon />
                      </IconButton>
                    </Tooltip>
                    {result.pdf_file_path && (
                      <Tooltip title="다운로드">
                        <IconButton
                          size="small"
                          onClick={() => handleDownloadResult(result)}
                        >
                          <DownloadIcon />
                        </IconButton>
                      </Tooltip>
                    )}
                    <Tooltip title="수정">
                      <IconButton
                        size="small"
                        onClick={() => handleEditResult(result)}
                      >
                        <EditIcon />
                      </IconButton>
                    </Tooltip>
                  </TableCell>
                </TableRow>
              ))
            ) : (
              <TableRow>
                <TableCell colSpan={8} align="center">
                  검진 결과가 없습니다
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </TableContainer>

      {/* 상세보기 다이얼로그 */}
      <Dialog open={dialogOpen} onClose={() => setDialogOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>검진 결과 상세</DialogTitle>
        <DialogContent>
          {selectedResult && (
            <Box>
              <Grid container spacing={2}>
                <Grid item xs={6}>
                  <Typography variant="subtitle2" color="text.secondary">근로자 정보</Typography>
                  <Typography>{selectedResult.worker_name} ({selectedResult.employee_id})</Typography>
                </Grid>
                <Grid item xs={6}>
                  <Typography variant="subtitle2" color="text.secondary">검진일</Typography>
                  <Typography>{format(new Date(selectedResult.exam_date), 'yyyy년 MM월 dd일', { locale: ko })}</Typography>
                </Grid>
                <Grid item xs={6}>
                  <Typography variant="subtitle2" color="text.secondary">검진종류</Typography>
                  <Typography>{selectedResult.exam_type}</Typography>
                </Grid>
                <Grid item xs={6}>
                  <Typography variant="subtitle2" color="text.secondary">검진기관</Typography>
                  <Typography>{selectedResult.institution_name}</Typography>
                </Grid>
                <Grid item xs={12}>
                  <Typography variant="subtitle2" color="text.secondary">결과등급</Typography>
                  <Chip
                    label={selectedResult.result_grade}
                    color={getGradeColor(selectedResult.result_grade)}
                  />
                </Grid>
                {selectedResult.abnormal_findings && selectedResult.abnormal_findings.length > 0 && (
                  <Grid item xs={12}>
                    <Typography variant="subtitle2" color="text.secondary">이상소견</Typography>
                    {selectedResult.abnormal_findings.map((finding, index) => (
                      <Chip key={index} label={finding} sx={{ mr: 1, mb: 1 }} />
                    ))}
                  </Grid>
                )}
                {selectedResult.doctor_opinion && (
                  <Grid item xs={12}>
                    <Typography variant="subtitle2" color="text.secondary">의사 소견</Typography>
                    <Typography>{selectedResult.doctor_opinion}</Typography>
                  </Grid>
                )}
                {selectedResult.follow_up_required && (
                  <Grid item xs={12}>
                    <Alert severity="warning">
                      후속조치가 필요합니다.
                      {selectedResult.follow_up_date && ` (예정일: ${format(new Date(selectedResult.follow_up_date), 'yyyy-MM-dd')})`}
                    </Alert>
                  </Grid>
                )}
              </Grid>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDialogOpen(false)}>닫기</Button>
        </DialogActions>
      </Dialog>

      {/* 업로드 다이얼로그 */}
      <Dialog open={uploadDialogOpen} onClose={() => setUploadDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>검진 결과 일괄 업로드</DialogTitle>
        <DialogContent>
          <Alert severity="info" sx={{ mb: 2 }}>
            엑셀 파일(.xlsx)로 검진 결과를 일괄 업로드할 수 있습니다.
          </Alert>
          <Button variant="outlined" component="label" fullWidth>
            파일 선택
            <input type="file" hidden accept=".xlsx,.xls" />
          </Button>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setUploadDialogOpen(false)}>취소</Button>
          <Button variant="contained">업로드</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}