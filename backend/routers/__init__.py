"""
AiMaster 路由模块
"""
from .auth import router as auth_router, get_current_user
from .tasks import router as tasks_router
from .articles import router as articles_router

__all__ = ["auth_router", "tasks_router", "articles_router", "get_current_user"]
