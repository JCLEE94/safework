"""
건강진단 예약 관리 모델
Health Exam Appointment Management Model
"""

from sqlalchemy import Column, Integer, String, DateTime, Date, Boolean, ForeignKey, Text, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from ..config.database import Base


class AppointmentStatus(str, enum.Enum):
    """예약 상태"""
    SCHEDULED = "scheduled"  # 예약됨
    CONFIRMED = "confirmed"  # 확정됨
    COMPLETED = "completed"  # 완료됨
    CANCELLED = "cancelled"  # 취소됨
    NO_SHOW = "no_show"     # 미참석
    RESCHEDULED = "rescheduled"  # 일정변경


class NotificationType(str, enum.Enum):
    """알림 유형"""
    SMS = "sms"
    EMAIL = "email"
    KAKAO = "kakao"
    APP_PUSH = "app_push"


class HealthExamAppointment(Base):
    """건강진단 예약"""
    __tablename__ = "health_exam_appointments"
    
    id = Column(Integer, primary_key=True, index=True)
    worker_id = Column(Integer, ForeignKey("workers.id", ondelete="CASCADE"), nullable=False)
    exam_type = Column(String(50), nullable=False)  # 일반건강진단, 특수건강진단, 배치전건강진단
    
    # 예약 정보
    scheduled_date = Column(Date, nullable=False, index=True)
    scheduled_time = Column(String(10))  # HH:MM 형식
    medical_institution = Column(String(200), nullable=False)  # 검진기관
    institution_address = Column(Text)
    institution_phone = Column(String(20))
    
    # 상태 관리
    status = Column(SQLEnum(AppointmentStatus), default=AppointmentStatus.SCHEDULED, nullable=False)
    confirmed_at = Column(DateTime)
    completed_at = Column(DateTime)
    cancelled_at = Column(DateTime)
    cancellation_reason = Column(Text)
    
    # 알림 설정
    reminder_days_before = Column(Integer, default=3)  # 며칠 전 알림
    reminder_sent = Column(Boolean, default=False)
    reminder_sent_at = Column(DateTime)
    notification_methods = Column(Text)  # JSON 형식으로 저장 ["sms", "email"]
    
    # 추가 정보
    special_instructions = Column(Text)  # 특별 지시사항 (금식 여부 등)
    exam_items = Column(Text)  # 검사 항목 (JSON)
    estimated_duration = Column(Integer)  # 예상 소요시간(분)
    
    # 이전 예약 연결 (재예약인 경우)
    previous_appointment_id = Column(Integer, ForeignKey("health_exam_appointments.id"))
    
    # 메타데이터
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    created_by = Column(String(100))
    updated_by = Column(String(100))
    
    # 관계 설정
    worker = relationship("Worker", back_populates="exam_appointments")
    previous_appointment = relationship("HealthExamAppointment", remote_side=[id])


class AppointmentNotification(Base):
    """예약 알림 기록"""
    __tablename__ = "appointment_notifications"
    
    id = Column(Integer, primary_key=True, index=True)
    appointment_id = Column(Integer, ForeignKey("health_exam_appointments.id", ondelete="CASCADE"), nullable=False)
    
    notification_type = Column(SQLEnum(NotificationType), nullable=False)
    sent_at = Column(DateTime, default=datetime.now)
    status = Column(String(20), default="sent")  # sent, failed, delivered
    
    # 알림 내용
    recipient = Column(String(200))  # 전화번호, 이메일 등
    message_content = Column(Text)
    
    # 응답 정보
    response_code = Column(String(50))
    response_message = Column(Text)
    delivery_confirmed_at = Column(DateTime)
    
    # 관계 설정
    appointment = relationship("HealthExamAppointment", backref="notifications")