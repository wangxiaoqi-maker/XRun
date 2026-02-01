"""
认证服务
"""
import os
import bcrypt
from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.user import User, UserRole

# 北京时区 (UTC+8)
BEIJING_TZ = timezone(timedelta(hours=8))

def beijing_now() -> datetime:
    """获取当前北京时间（无时区信息）"""
    return datetime.now(BEIJING_TZ).replace(tzinfo=None)

# JWT 配置
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "xrun-secret-key-2024-please-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 24 * 7  # 7 天


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    return bcrypt.checkpw(
        plain_password.encode('utf-8'), 
        hashed_password.encode('utf-8')
    )


def get_password_hash(password: str) -> str:
    """密码加密"""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """创建访问令牌"""
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_token(token: str) -> Optional[dict]:
    """解码令牌"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None


class AuthService:
    """认证服务"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_user_by_username(self, username: str) -> Optional[User]:
        """根据用户名获取用户"""
        result = await self.session.execute(
            select(User).where(User.username == username)
        )
        return result.scalar_one_or_none()
    
    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        """根据 ID 获取用户"""
        result = await self.session.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()
    
    async def get_user_by_email(self, email: str) -> Optional[User]:
        """根据邮箱获取用户"""
        result = await self.session.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()
    
    async def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """认证用户"""
        user = await self.get_user_by_username(username)
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        if not user.is_active:
            return None
        return user
    
    async def create_user(
        self,
        username: str,
        password: str,
        email: Optional[str] = None,
        nickname: Optional[str] = None,
        role: UserRole = UserRole.USER
    ) -> User:
        """创建用户"""
        user = User(
            username=username,
            email=email,
            hashed_password=get_password_hash(password),
            nickname=nickname or username,
            role=role
        )
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user
    
    async def update_last_login(self, user: User):
        """更新最后登录时间（北京时间）"""
        user.last_login = beijing_now()
        await self.session.commit()
    
    async def change_password(self, user: User, new_password: str):
        """修改密码"""
        user.hashed_password = get_password_hash(new_password)
        await self.session.commit()
    
    async def get_all_users(self, offset: int = 0, limit: int = 50):
        """获取所有用户"""
        result = await self.session.execute(
            select(User).offset(offset).limit(limit).order_by(User.created_at.desc())
        )
        return list(result.scalars().all())
    
    async def delete_user(self, user_id: str) -> bool:
        """删除用户"""
        user = await self.get_user_by_id(user_id)
        if not user:
            return False
        await self.session.delete(user)
        await self.session.commit()
        return True
    
    async def init_admin_user(self):
        """初始化管理员账号（如果不存在）"""
        admin = await self.get_user_by_username("admin")
        if not admin:
            await self.create_user(
                username="admin",
                password="admin123",
                email="admin@xrun.com",
                nickname="管理员",
                role=UserRole.ADMIN
            )
            print("✅ 已创建默认管理员账号: admin / admin123")
