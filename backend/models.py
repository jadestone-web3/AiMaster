"""
AiMaster 数据模型
"""
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, Integer, Boolean, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from .database import Base
import enum


class TaskStatus(str, enum.Enum):
    """任务状态枚举"""
    PENDING_REWRITE = "pending_rewrite"      # 待改写
    REWRITTING = "rewriting"                  # 改写中
    REWRITTEN = "rewritten"                  # 已改写
    PENDING_PUBLISH = "pending_publish"       # 待发布
    PUBLISHED = "published"                  # 已发布
    FAILED = "failed"                        # 失败


class User(Base):
    """用户表"""
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    is_admin = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关联
    tasks = relationship("Task", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User {self.username}>"


class Task(Base):
    """任务表"""
    __tablename__ = "tasks"

    id = Column(String(36), primary_key=True, index=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)

    # 原始文章信息
    original_title = Column(String(500))
    original_url = Column(String(2000))
    original_author = Column(String(200))
    original_content = Column(Text)
    original_platform = Column(String(50))
    original_images = Column(Text)  # JSON 存储
    original_publish_time = Column(DateTime)

    # 改写后内容
    rewritten_title = Column(String(500))
    rewritten_content = Column(Text)
    rewritten_images = Column(Text)  # JSON 存储

    # 任务状态
    status = Column(SQLEnum(TaskStatus), default=TaskStatus.PENDING_REWRITE, index=True)
    progress = Column(Integer, default=0)

    # AI 相关
    ai_model = Column(String(50))
    ai_tokens_used = Column(Integer, default=0)

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime)

    # 关联
    user = relationship("User", back_populates="tasks")

    def __repr__(self):
        return f"<Task {self.id} - {self.status.value}>"

    def to_dict(self):
        """转换为字典"""
        import json
        return {
            "id": self.id,
            "original_title": self.original_title,
            "original_url": self.original_url,
            "original_author": self.original_author,
            "original_platform": self.original_platform,
            "original_images": json.loads(self.original_images) if self.original_images else [],
            "original_publish_time": self.original_publish_time.isoformat() if self.original_publish_time else None,
            "rewritten_title": self.rewritten_title,
            "rewritten_content": self.rewritten_content,
            "rewritten_images": json.loads(self.rewritten_images) if self.rewritten_images else [],
            "status": self.status.value,
            "progress": self.progress,
            "ai_model": self.ai_model,
            "ai_tokens_used": self.ai_tokens_used,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }


class RefreshToken(Base):
    """刷新令牌表"""
    __tablename__ = "refresh_tokens"

    token = Column(String(64), primary_key=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<RefreshToken for user {self.user_id}>"
