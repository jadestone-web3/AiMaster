"""
AiMaster 认证路由
"""
from datetime import datetime, timedelta
import uuid
import bcrypt
from fastapi import APIRouter, Depends, HTTPException, Header, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from pydantic import BaseModel

from ..database import get_db
from ..models import User, RefreshToken, TaskStatus
from ..config import settings

router = APIRouter(prefix="/api/auth", tags=["认证"])


# ==================== Pydantic 模型 ====================
class CaptchaResponse(BaseModel):
    captcha_id: str
    captcha_image: str


class LoginRequest(BaseModel):
    username: str
    password: str
    captcha_id: str = ""
    captcha_code: str = ""


class RegisterRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: dict


class RefreshRequest(BaseModel):
    refresh_token: str


class UserResponse(BaseModel):
    id: str
    username: str
    is_admin: bool
    is_active: bool
    created_at: datetime


# ==================== 密码工具 ====================
def hash_password(password: str) -> str:
    """密码哈希"""
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, hashed: str) -> bool:
    """验证密码"""
    return bcrypt.checkpw(password.encode(), hashed.encode())


# ==================== JWT 工具 ====================
def create_access_token(user_id: str, username: str) -> str:
    """创建访问令牌（简化版 base64）"""
    import base64
    import json

    expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    data = {
        "sub": username,
        "user_id": user_id,
        "exp": expire.timestamp()
    }
    token_data = json.dumps(data)
    return base64.b64encode(token_data.encode()).decode()


def verify_access_token(token: str) -> dict:
    """验证访问令牌"""
    import base64
    import json

    try:
        padded_token = token + "=" * (4 - len(token) % 4)
        token_data = base64.b64decode(padded_token).decode()
        data = json.loads(token_data)

        # 检查过期
        exp = data.get("exp", 0)
        if datetime.utcnow().timestamp() > exp:
            return None

        return data
    except Exception:
        return None


def create_refresh_token(db: Session, user_id: str) -> str:
    """创建刷新令牌"""
    token = str(uuid.uuid4())
    expires_at = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    db_refresh = RefreshToken(
        token=token,
        user_id=user_id,
        expires_at=expires_at
    )
    db.add(db_refresh)
    db.commit()

    return token


def verify_refresh_token(db: Session, token: str) -> User:
    """验证刷新令牌并返回用户"""
    db_refresh = db.query(RefreshToken).filter(
        RefreshToken.token == token,
        RefreshToken.expires_at > datetime.utcnow()
    ).first()

    if not db_refresh:
        return None

    return db.query(User).filter(User.id == db_refresh.user_id, User.is_active == True).first()


# ==================== 依赖项 ====================
def get_current_user(
    authorization: str = Header(None),
    db: Session = Depends(get_db)
) -> User:
    """获取当前用户"""
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )

    token = authorization.replace("Bearer ", "")
    payload = verify_access_token(token)

    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )

    user = db.query(User).filter(User.username == payload["sub"], User.is_active == True).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )

    return user


def get_admin_user(current_user: User = Depends(get_current_user)) -> User:
    """获取当前管理员用户"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    return current_user


# ==================== 验证码接口 ====================
@router.get("/captcha", response_model=CaptchaResponse)
async def get_captcha():
    """获取验证码（极简化版本）"""
    captcha_id = str(uuid.uuid4())
    # 返回一个简单的 base64 透明图片
    captcha_image = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
    return CaptchaResponse(captcha_id=captcha_id, captcha_image=captcha_image)


# ==================== 认证接口 ====================
@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest, db: Session = Depends(get_db)):
    """用户登录"""
    # 查找用户
    user = db.query(User).filter(User.username == request.username, User.is_active == True).first()

    if not user or not verify_password(request.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名或密码错误"
        )

    # 创建令牌
    access_token = create_access_token(user.id, user.username)
    refresh_token = create_refresh_token(db, user.id)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user={
            "id": user.id,
            "username": user.username,
            "is_admin": user.is_admin
        }
    )


@router.post("/register", response_model=TokenResponse)
async def register(request: RegisterRequest, db: Session = Depends(get_db)):
    """用户注册"""
    # 检查用户名是否已存在
    existing = db.query(User).filter(User.username == request.username).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名已存在"
        )

    # 创建用户
    user_id = str(uuid.uuid4())
    user = User(
        id=user_id,
        username=request.username,
        password_hash=hash_password(request.password),
        is_admin=False,  # 普通用户
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # 创建令牌
    access_token = create_access_token(user.id, user.username)
    refresh_token = create_refresh_token(db, user.id)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user={
            "id": user.id,
            "username": user.username,
            "is_admin": user.is_admin
        }
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(request: RefreshRequest, db: Session = Depends(get_db)):
    """刷新访问令牌"""
    user = verify_refresh_token(db, request.refresh_token)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )

    # 创建新访问令牌
    access_token = create_access_token(user.id, user.username)

    return TokenResponse(
        access_token=access_token,
        refresh_token=request.refresh_token,  # 保持刷新令牌不变
        user={
            "id": user.id,
            "username": user.username,
            "is_admin": user.is_admin
        }
    )


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """获取当前用户信息"""
    return UserResponse(
        id=current_user.id,
        username=current_user.username,
        is_admin=current_user.is_admin,
        is_active=current_user.is_active,
        created_at=current_user.created_at
    )


@router.post("/logout")
async def logout(request: RefreshRequest, db: Session = Depends(get_db)):
    """登出（删除刷新令牌）"""
    db.query(RefreshToken).filter(RefreshToken.token == request.refresh_token).delete()
    db.commit()
    return {"message": "Logged out successfully"}


# ==================== 管理员接口 ====================
@router.get("/admin/users", response_model=list)
async def list_users(
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    """列出所有用户（仅管理员）"""
    users = db.query(User).all()
    return [
        {
            "id": u.id,
            "username": u.username,
            "is_admin": u.is_admin,
            "is_active": u.is_active,
            "created_at": u.created_at
        }
        for u in users
    ]


@router.delete("/admin/users/{user_id}")
async def delete_user(
    user_id: str,
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    """删除用户（仅管理员）"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.is_admin:
        raise HTTPException(status_code=400, detail="Cannot delete admin user")

    db.delete(user)
    db.commit()
    return {"message": "User deleted"}
