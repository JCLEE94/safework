"""
근로자 피드백 모델
Worker feedback model with photo attachment support
"""

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from ..config.database import Base


class WorkerFeedback(Base):
    """근로자 피드백"""

    __tablename__ = "worker_feedbacks"

    id = Column(Integer, primary_key=True, index=True)
    
    # 근로자 참조
    worker_id = Column(Integer, ForeignKey("workers.id"), nullable=False, index=True)
    
    # 피드백 내용
    content = Column(Text, nullable=False, comment="피드백 내용")
    photo_url = Column(Text, comment="첨부 사진 URL")
    
    # 작성자 정보
    created_by = Column(String(50), comment="작성자")
    
    # 시스템 정보
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    
    # 관계설정
    worker = relationship("Worker", back_populates="feedbacks")