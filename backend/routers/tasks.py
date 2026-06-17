"""
AiMaster 任务路由
"""
import json
import asyncio
from datetime import datetime
from typing import Optional, List
import uuid
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Task, User, TaskStatus
from ..routers.auth import get_current_user
from ..ai_service import ai_service

router = APIRouter(prefix="/api/tasks", tags=["任务"])


# ==================== Pydantic 模型 ====================
class ArticleSubmit(BaseModel):
    """提交文章请求"""
    platform: str
    article: dict


class ArticleSubmitResponse(BaseModel):
    """提交文章响应"""
    success: bool
    task_id: str
    message: str


class TaskListItem(BaseModel):
    """任务列表项"""
    id: str
    original_title: str
    original_platform: str
    status: str
    progress: int
    created_at: Optional[str] = None


class TaskDetail(BaseModel):
    """任务详情"""
    id: str
    original_title: str
    original_url: Optional[str] = None
    original_author: Optional[str] = None
    original_platform: Optional[str] = None
    original_content: Optional[str] = None
    original_images: List[dict] = []
    original_publish_time: Optional[str] = None
    rewritten_title: Optional[str] = None
    rewritten_content: Optional[str] = None
    rewritten_images: List[dict] = []
    status: str
    progress: int
    ai_model: Optional[str] = None
    ai_tokens_used: int = 0
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    completed_at: Optional[str] = None


# ==================== 任务接口 ====================
@router.post("", response_model=ArticleSubmitResponse)
async def submit_article(
    article_data: ArticleSubmit,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """提交文章进行 AI 改写"""
    article = article_data.article
    platform = article_data.platform

    # 创建任务
    task_id = str(uuid.uuid4())

    # 处理图片
    images = article.get("images", []) or []
    if article.get("imageList"):
        images = article.get("imageList")
    images_json = json.dumps(images, ensure_ascii=False)

    # 处理时间
    publish_time = None
    if article.get("publishTime"):
        try:
            publish_time = datetime.fromisoformat(article["publishTime"].replace("Z", "+00:00"))
        except:
            pass

    task = Task(
        id=task_id,
        user_id=current_user.id,
        original_title=article.get("title", "无标题"),
        original_url=article.get("url", ""),
        original_author=article.get("author", ""),
        original_content=article.get("content", "") or article.get("contentList", ""),
        original_platform=platform,
        original_images=images_json,
        original_publish_time=publish_time,
        status=TaskStatus.PENDING_REWRITE,
        progress=0
    )

    db.add(task)
    db.commit()

    # 异步处理 AI 改写
    asyncio.create_task(ai_service.rewrite_article(task_id, db))

    return ArticleSubmitResponse(
        success=True,
        task_id=task_id,
        message="任务已创建"
    )


@router.get("", response_model=List[TaskListItem])
async def get_tasks(
    size: int = Query(default=10, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    status_filter: Optional[str] = Query(default=None, alias="status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取当前用户的任务列表"""
    query = db.query(Task).filter(Task.user_id == current_user.id)

    if status_filter:
        try:
            status_enum = TaskStatus(status_filter)
            query = query.filter(Task.status == status_enum)
        except ValueError:
            pass

    # 按创建时间倒序
    query = query.order_by(Task.created_at.desc())

    # 分页
    tasks = query.offset(offset).limit(size).all()

    return [
        TaskListItem(
            id=task.id,
            original_title=task.original_title,
            original_platform=task.original_platform,
            status=task.status.value,
            progress=task.progress,
            created_at=task.created_at.isoformat() if task.created_at else None
        )
        for task in tasks
    ]


@router.get("/{task_id}", response_model=TaskDetail)
async def get_task(
    task_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取任务详情"""
    task = db.query(Task).filter(Task.id == task_id).first()

    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    if task.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="无权访问此任务")

    # 解析图片
    original_images = []
    rewritten_images = []
    try:
        original_images = json.loads(task.original_images) if task.original_images else []
        rewritten_images = json.loads(task.rewritten_images) if task.rewritten_images else []
    except:
        pass

    return TaskDetail(
        id=task.id,
        original_title=task.original_title,
        original_url=task.original_url,
        original_author=task.original_author,
        original_platform=task.original_platform,
        original_content=task.original_content,
        original_images=original_images,
        original_publish_time=task.original_publish_time.isoformat() if task.original_publish_time else None,
        rewritten_title=task.rewritten_title,
        rewritten_content=task.rewritten_content,
        rewritten_images=rewritten_images,
        status=task.status.value,
        progress=task.progress,
        ai_model=task.ai_model,
        ai_tokens_used=task.ai_tokens_used,
        created_at=task.created_at.isoformat() if task.created_at else None,
        updated_at=task.updated_at.isoformat() if task.updated_at else None,
        completed_at=task.completed_at.isoformat() if task.completed_at else None
    )


@router.delete("/{task_id}")
async def delete_task(
    task_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除任务"""
    task = db.query(Task).filter(Task.id == task_id).first()

    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    if task.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="无权访问此任务")

    db.delete(task)
    db.commit()

    return {"message": "任务已删除"}


@router.post("/{task_id}/retry")
async def retry_task(
    task_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """重试失败的任务"""
    task = db.query(Task).filter(Task.id == task_id).first()

    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    if task.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="无权访问此任务")

    if task.status != TaskStatus.FAILED:
        raise HTTPException(status_code=400, detail="只能重试失败的任务")

    # 重置状态并重新处理
    task.status = TaskStatus.PENDING_REWRITE
    task.progress = 0
    db.commit()

    asyncio.create_task(ai_service.rewrite_article(task_id, db))

    return {"message": "任务已重新开始"}
