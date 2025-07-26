import React, { useEffect } from 'react';
import { Form, Input, Select, DatePicker, Row, Col, Space, Button } from 'antd';
import { Worker, WorkerCreate } from '@/services/api/workers';
import { isValidEmail, isValidPhoneNumber, createValidator } from '@/utils/validators';
import dayjs from 'dayjs';

const { Option } = Select;

interface WorkerFormProps {
  worker?: Worker;
  onSubmit: (values: WorkerCreate) => void;
  onCancel: () => void;
  loading?: boolean;
}

export const WorkerForm: React.FC<WorkerFormProps> = ({
  worker,
  onSubmit,
  onCancel,
  loading = false,
}) => {
  const [form] = Form.useForm();

  useEffect(() => {
    if (worker) {
      form.setFieldsValue({
        ...worker,
        birth_date: worker.birth_date ? dayjs(worker.birth_date) : undefined,
        employment_date: dayjs(worker.employment_date),
      });
    }
  }, [worker, form]);

  const handleFinish = (values: any) => {
    const formData: WorkerCreate = {
      ...values,
      birth_date: values.birth_date ? values.birth_date.format('YYYY-MM-DD') : undefined,
      employment_date: values.employment_date.format('YYYY-MM-DD'),
    };
    onSubmit(formData);
  };

  return (
    <Form
      form={form}
      layout="vertical"
      onFinish={handleFinish}
      initialValues={{
        employment_type: 'permanent',
        gender: 'male',
      }}
    >
      <Row gutter={16}>
        <Col span={12}>
          <Form.Item
            label="사원번호"
            name="employee_id"
            rules={[
              { required: true, message: '사원번호를 입력해주세요' },
              { max: 20, message: '최대 20자까지 입력 가능합니다' },
            ]}
          >
            <Input placeholder="예: EMP001" />
          </Form.Item>
        </Col>
        <Col span={12}>
          <Form.Item
            label="이름"
            name="name"
            rules={[
              { required: true, message: '이름을 입력해주세요' },
              { max: 50, message: '최대 50자까지 입력 가능합니다' },
            ]}
          >
            <Input placeholder="홍길동" />
          </Form.Item>
        </Col>
      </Row>

      <Row gutter={16}>
        <Col span={12}>
          <Form.Item
            label="부서"
            name="department"
            rules={[{ required: true, message: '부서를 선택해주세요' }]}
          >
            <Select placeholder="부서 선택">
              <Option value="관리부">관리부</Option>
              <Option value="공사부">공사부</Option>
              <Option value="안전환경부">안전환경부</Option>
              <Option value="기술부">기술부</Option>
            </Select>
          </Form.Item>
        </Col>
        <Col span={12}>
          <Form.Item
            label="직위"
            name="position"
            rules={[{ required: true, message: '직위를 선택해주세요' }]}
          >
            <Select placeholder="직위 선택">
              <Option value="사원">사원</Option>
              <Option value="대리">대리</Option>
              <Option value="과장">과장</Option>
              <Option value="차장">차장</Option>
              <Option value="부장">부장</Option>
            </Select>
          </Form.Item>
        </Col>
      </Row>

      <Row gutter={16}>
        <Col span={12}>
          <Form.Item
            label="이메일"
            name="email"
            rules={[
              { type: 'email', message: '올바른 이메일 형식이 아닙니다' },
              { validator: createValidator(isValidEmail, '올바른 이메일을 입력해주세요') },
            ]}
          >
            <Input placeholder="example@company.com" />
          </Form.Item>
        </Col>
        <Col span={12}>
          <Form.Item
            label="연락처"
            name="phone"
            rules={[
              { required: true, message: '연락처를 입력해주세요' },
              { validator: createValidator(isValidPhoneNumber, '올바른 전화번호 형식이 아닙니다') },
            ]}
          >
            <Input placeholder="010-1234-5678" />
          </Form.Item>
        </Col>
      </Row>

      <Row gutter={16}>
        <Col span={8}>
          <Form.Item label="성별" name="gender">
            <Select>
              <Option value="male">남성</Option>
              <Option value="female">여성</Option>
            </Select>
          </Form.Item>
        </Col>
        <Col span={8}>
          <Form.Item label="생년월일" name="birth_date">
            <DatePicker style={{ width: '100%' }} placeholder="생년월일 선택" />
          </Form.Item>
        </Col>
        <Col span={8}>
          <Form.Item
            label="입사일"
            name="employment_date"
            rules={[{ required: true, message: '입사일을 선택해주세요' }]}
          >
            <DatePicker style={{ width: '100%' }} placeholder="입사일 선택" />
          </Form.Item>
        </Col>
      </Row>

      <Row gutter={16}>
        <Col span={12}>
          <Form.Item
            label="고용형태"
            name="employment_type"
            rules={[{ required: true, message: '고용형태를 선택해주세요' }]}
          >
            <Select>
              <Option value="permanent">정규직</Option>
              <Option value="contract">계약직</Option>
              <Option value="temporary">임시직</Option>
            </Select>
          </Form.Item>
        </Col>
        <Col span={12}>
          <Form.Item
            label="작업유형"
            name="work_type"
            rules={[{ required: true, message: '작업유형을 입력해주세요' }]}
          >
            <Input placeholder="예: 건설현장 관리" />
          </Form.Item>
        </Col>
      </Row>

      <Form.Item label="건강상태" name="health_status">
        <Input.TextArea rows={3} placeholder="특이사항이 있을 경우 입력" />
      </Form.Item>

      <Form.Item>
        <Space style={{ float: 'right' }}>
          <Button onClick={onCancel}>취소</Button>
          <Button type="primary" htmlType="submit" loading={loading}>
            {worker ? '수정' : '등록'}
          </Button>
        </Space>
      </Form.Item>
    </Form>
  );
};