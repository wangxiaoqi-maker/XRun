"""
认证 API
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..services.auth_service import AuthService, create_access_token, decode_token
from ..models.user import UserRole

router = APIRouter(prefix="/auth", tags=["认证"])
security = HTTPBearer(auto_error=False)


# ==================== 请求/响应模型 ====================

class LoginRequest(BaseModel):
    """登录请求"""
    username: str = Field(..., min_length=2, max_length=50, description="用户名")
    password: str = Field(..., min_length=6, description="密码")


class RegisterRequest(BaseModel):
    """注册请求"""
    username: str = Field(..., min_length=2, max_length=50, description="用户名")
    password: str = Field(..., min_length=6, description="密码")
    email: Optional[EmailStr] = Field(None, description="邮箱")
    nickname: Optional[str] = Field(None, max_length=50, description="昵称")


class TokenResponse(BaseModel):
    """Token 响应"""
    access_token: str
    token_type: str = "bearer"
    user: dict


class UserResponse(BaseModel):
    """用户响应"""
    id: str
    username: str
    email: Optional[str]
    nickname: str
    avatar: Optional[str]
    role: str
    is_active: bool
    last_login: Optional[str]
    created_at: str


class ChangePasswordRequest(BaseModel):
    """修改密码请求"""
    old_password: str = Field(..., description="旧密码")
    new_password: str = Field(..., min_length=6, description="新密码")


class UpdateProfileRequest(BaseModel):
    """更新个人信息请求"""
    nickname: Optional[str] = Field(None, max_length=50, description="昵称")
    email: Optional[EmailStr] = Field(None, description="邮箱")
    avatar: Optional[str] = Field(None, description="头像 URL")


# ==================== 依赖注入 ====================

async def get_auth_service(db: AsyncSession = Depends(get_db)) -> AuthService:
    """获取认证服务"""
    return AuthService(db)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    auth_service: AuthService = Depends(get_auth_service)
):
    """获取当前用户"""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未登录",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    payload = decode_token(credentials.credentials)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的令牌",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的令牌",
        )
    
    user = await auth_service.get_user_by_id(user_id)
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在或已禁用",
        )
    
    return user


async def get_current_admin(current_user = Depends(get_current_user)):
    """获取当前管理员用户"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限",
        )
    return current_user


async def get_optional_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    auth_service: AuthService = Depends(get_auth_service)
):
    """获取当前用户（可选，未登录返回 None）"""
    if not credentials:
        return None
    
    payload = decode_token(credentials.credentials)
    if not payload:
        return None
    
    user_id = payload.get("sub")
    if not user_id:
        return None
    
    return await auth_service.get_user_by_id(user_id)


# ==================== API 端点 ====================

@router.post("/login", response_model=TokenResponse, summary="用户登录")
async def login(
    request: LoginRequest,
    auth_service: AuthService = Depends(get_auth_service)
):
    """用户登录，返回访问令牌"""
    user = await auth_service.authenticate_user(request.username, request.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
        )
    
    # 更新最后登录时间
    await auth_service.update_last_login(user)
    
    # 创建令牌
    access_token = create_access_token(data={"sub": user.id, "role": user.role.value})
    
    return TokenResponse(
        access_token=access_token,
        user=user.to_dict()
    )


@router.post("/register", response_model=TokenResponse, summary="用户注册")
async def register(
    request: RegisterRequest,
    auth_service: AuthService = Depends(get_auth_service)
):
    """用户注册"""
    # 检查用户名是否已存在
    if await auth_service.get_user_by_username(request.username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名已存在",
        )
    
    # 检查邮箱是否已存在
    if request.email and await auth_service.get_user_by_email(request.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="邮箱已被注册",
        )
    
    # 创建用户
    user = await auth_service.create_user(
        username=request.username,
        password=request.password,
        email=request.email,
        nickname=request.nickname
    )
    
    # 创建令牌
    access_token = create_access_token(data={"sub": user.id, "role": user.role.value})
    
    return TokenResponse(
        access_token=access_token,
        user=user.to_dict()
    )


@router.get("/me", response_model=UserResponse, summary="获取当前用户信息")
async def get_me(current_user = Depends(get_current_user)):
    """获取当前登录用户信息"""
    return UserResponse(**current_user.to_dict())


@router.put("/me", response_model=UserResponse, summary="更新个人信息")
async def update_me(
    request: UpdateProfileRequest,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """更新当前用户个人信息"""
    if request.nickname is not None:
        current_user.nickname = request.nickname
    if request.email is not None:
        current_user.email = request.email
    if request.avatar is not None:
        current_user.avatar = request.avatar
    
    await db.commit()
    await db.refresh(current_user)
    
    return UserResponse(**current_user.to_dict())


@router.post("/change-password", summary="修改密码")
async def change_password(
    request: ChangePasswordRequest,
    current_user = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service)
):
    """修改密码"""
    from ..services.auth_service import verify_password
    
    # 验证旧密码
    if not verify_password(request.old_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="旧密码错误",
        )
    
    # 修改密码
    await auth_service.change_password(current_user, request.new_password)
    
    return {"message": "密码修改成功"}


# ==================== 管理员 API ====================

@router.get("/users", summary="获取用户列表（管理员）")
async def list_users(
    offset: int = 0,
    limit: int = 50,
    current_admin = Depends(get_current_admin),
    auth_service: AuthService = Depends(get_auth_service)
):
    """获取所有用户列表（仅管理员）"""
    users = await auth_service.get_all_users(offset, limit)
    return [user.to_dict() for user in users]


@router.delete("/users/{user_id}", summary="删除用户（管理员）")
async def delete_user(
    user_id: str,
    current_admin = Depends(get_current_admin),
    auth_service: AuthService = Depends(get_auth_service)
):
    """删除用户（仅管理员）"""
    if user_id == current_admin.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不能删除自己",
        )
    
    success = await auth_service.delete_user(user_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在",
        )
    
    return {"message": "用户已删除"}
