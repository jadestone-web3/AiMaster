"""
AiMaster 后端主应用
"""
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Depends
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from database import get_db, init_db, SessionLocal
from models import User, TaskStatus
from config import settings
from routers import auth_router, tasks_router
from routers.articles import router as articles_router
from routers.auth import verify_access_token
from ai_service import ai_service


def create_default_admin():
    """创建默认管理员账号"""
    db = SessionLocal()
    try:
        existing = db.query(User).filter(User.username == settings.ADMIN_USERNAME).first()
        if not existing:
            from routers.auth import hash_password
            admin = User(
                id="admin-default-id",
                username=settings.ADMIN_USERNAME,
                password_hash=hash_password(settings.ADMIN_PASSWORD),
                is_admin=True,
                is_active=True
            )
            db.add(admin)
            db.commit()
            print(f"✅ 默认管理员账号已创建: {settings.ADMIN_USERNAME}")
        else:
            print(f"ℹ️ 管理员账号已存在: {settings.ADMIN_USERNAME}")
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期"""
    # 启动时
    print("=" * 50)
    print("🚀 AiMaster Backend 启动中...")
    print("=" * 50)

    # 初始化数据库
    init_db()
    print("✅ 数据库初始化完成")

    # 创建默认管理员
    create_default_admin()

    print(f"✅ AI 服务模式: {'模拟模式' if settings.AI_MOCK_MODE else '真实 API'}")
    if settings.AI_MOCK_MODE:
        print("💡 设置 AI_MOCK_MODE=false 启用真实 MiniMax API")
    print("=" * 50)
    print()

    yield

    # 关闭时
    print("👋 AiMaster Backend 已关闭")


# 创建应用
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    lifespan=lifespan
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 全局异常处理
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    print(f"全局异常: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc) if settings.DEBUG else "Internal server error"}
    )


# 注册 API 路由
app.include_router(auth_router)
app.include_router(tasks_router)
app.include_router(articles_router)


# ==================== 页面路由 ====================
@app.get("/", response_class=HTMLResponse)
async def home():
    """首页 - 需要登录"""
    with open(os.path.join(os.path.dirname(__file__), "templates", "index.html"), "r", encoding="utf-8") as f:
        return f.read()


@app.get("/login", response_class=HTMLResponse)
async def login_page():
    """登录页"""
    with open(os.path.join(os.path.dirname(__file__), "templates", "login.html"), "r", encoding="utf-8") as f:
        return f.read()


@app.get("/register", response_class=HTMLResponse)
async def register_page():
    """注册页"""
    with open(os.path.join(os.path.dirname(__file__), "templates", "register.html"), "r", encoding="utf-8") as f:
        return f.read()


# ==================== 健康检查 ====================
@app.get("/health")
async def health():
    """健康检查"""
    return {"status": "healthy"}




# ==================== 启动说明 ====================
if __name__ == "__main__":
    import uvicorn

    print("=" * 50)
    print("📖 API 文档: http://localhost:8000/docs")
    print("=" * 50)

    uvicorn.run(app, host="0.0.0.0", port=8000)
