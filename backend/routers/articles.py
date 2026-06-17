"""
AiMaster 文章路由 - 兼容前端 /api/articles
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List

from ..database import get_db
from ..models import User
from ..routers.auth import get_current_user
from .tasks import (
    submit_article,
    get_tasks,
    get_task,
    delete_task,
    retry_task,
    ArticleSubmit,
    ArticleSubmitResponse,
    TaskListItem,
    TaskDetail
)

router = APIRouter(prefix="/api/articles", tags=["文章"])


@router.post("", response_model=ArticleSubmitResponse)
async def post_article(
    article_data: ArticleSubmit,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """提交文章（兼容 /api/articles）"""
    return await submit_article(article_data, db, current_user)


@router.get("", response_model=List[TaskListItem])
async def list_articles(
    size: int = Query(default=10, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    status: str = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取文章列表（兼容 /api/articles）"""
    return await get_tasks(size=size, offset=offset, status_filter=status, db=db, current_user=current_user)
