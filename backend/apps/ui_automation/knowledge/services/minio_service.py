"""
MinIO 对象存储服务

用于存储页面截图等静态资源
"""
import base64
import hashlib
import logging
from io import BytesIO
from typing import Optional
from datetime import timedelta

from minio import Minio
from minio.error import S3Error

from ..config import get_minio_config, MinIOConfig

logger = logging.getLogger(__name__)


class MinIOService:
    """MinIO 对象存储服务"""
    
    def __init__(self, config: Optional[MinIOConfig] = None):
        self.config = config or get_minio_config()
        self._client: Optional[Minio] = None
        self._initialized = False
    
    def _get_client(self) -> Minio:
        """获取 MinIO 客户端"""
        if self._client is None:
            self._client = Minio(
                endpoint=self.config.MINIO_ENDPOINT,
                access_key=self.config.MINIO_ACCESS_KEY,
                secret_key=self.config.MINIO_SECRET_KEY,
                secure=self.config.MINIO_SECURE
            )
        return self._client
    
    def initialize(self) -> bool:
        """
        初始化服务，确保存储桶存在
        
        Returns:
            是否初始化成功
        """
        if self._initialized:
            return True
        
        try:
            client = self._get_client()
            bucket = self.config.MINIO_BUCKET
            
            # 检查并创建存储桶
            if not client.bucket_exists(bucket):
                client.make_bucket(bucket)
                logger.info(f"创建 MinIO 存储桶: {bucket}")
                
                # 设置桶策略为公开读取
                policy = f'''{{
                    "Version": "2012-10-17",
                    "Statement": [{{
                        "Effect": "Allow",
                        "Principal": {{"AWS": ["*"]}},
                        "Action": ["s3:GetObject"],
                        "Resource": ["arn:aws:s3:::{bucket}/*"]
                    }}]
                }}'''
                client.set_bucket_policy(bucket, policy)
                logger.info(f"设置存储桶 {bucket} 为公开读取")
            
            self._initialized = True
            logger.info("MinIO 服务初始化成功")
            return True
            
        except S3Error as e:
            logger.error(f"MinIO 初始化失败: {e}")
            return False
        except Exception as e:
            logger.error(f"MinIO 连接失败: {e}")
            return False
    
    def upload_screenshot(
        self,
        image_data: str,
        page_id: str,
        content_type: str = "image/png"
    ) -> Optional[str]:
        """
        上传页面截图
        
        Args:
            image_data: Base64 编码的图片数据
            page_id: 页面 ID（用于生成文件名）
            content_type: 图片类型
            
        Returns:
            图片的访问 URL，失败返回 None
        """
        if not self.initialize():
            logger.error("MinIO 未初始化，无法上传")
            return None
        
        try:
            # 解码 Base64 数据
            # 处理可能的 data URL 格式
            if ',' in image_data:
                image_data = image_data.split(',', 1)[1]
            
            image_bytes = base64.b64decode(image_data)
            
            # 生成文件名
            ext = "png" if "png" in content_type else "jpg"
            object_name = f"{page_id}.{ext}"
            
            # 上传到 MinIO
            client = self._get_client()
            client.put_object(
                bucket_name=self.config.MINIO_BUCKET,
                object_name=object_name,
                data=BytesIO(image_bytes),
                length=len(image_bytes),
                content_type=content_type
            )
            
            # 返回访问 URL
            url = f"{self.config.MINIO_PUBLIC_URL}/{self.config.MINIO_BUCKET}/{object_name}"
            logger.info(f"截图上传成功: {url}")
            return url
            
        except Exception as e:
            logger.error(f"上传截图失败: {e}")
            return None
    
    def upload_element_crop(
        self,
        image_bytes: bytes,
        element_id: str,
        content_type: str = "image/png"
    ) -> Optional[str]:
        """
        上传元素切图
        
        Args:
            image_bytes: 图片字节数据
            element_id: 元素 ID（用于生成文件名）
            content_type: 图片类型
            
        Returns:
            图片的访问 URL，失败返回 None
        """
        if not self.initialize():
            logger.error("MinIO 未初始化，无法上传")
            return None
        
        try:
            # 生成文件名（放在 elements 子目录）
            ext = "png" if "png" in content_type else "jpg"
            object_name = f"elements/{element_id}.{ext}"
            
            # 上传到 MinIO
            client = self._get_client()
            client.put_object(
                bucket_name=self.config.MINIO_BUCKET,
                object_name=object_name,
                data=BytesIO(image_bytes),
                length=len(image_bytes),
                content_type=content_type
            )
            
            # 返回访问 URL
            url = f"{self.config.MINIO_PUBLIC_URL}/{self.config.MINIO_BUCKET}/{object_name}"
            logger.info(f"元素切图上传成功: {url}")
            return url
            
        except Exception as e:
            logger.error(f"上传元素切图失败: {e}")
            return None
    
    def delete_screenshot(self, page_id: str) -> bool:
        """
        删除页面截图
        
        Args:
            page_id: 页面 ID
            
        Returns:
            是否删除成功
        """
        if not self.initialize():
            return False
        
        try:
            client = self._get_client()
            
            # 尝试删除 png 和 jpg
            for ext in ["png", "jpg"]:
                object_name = f"{page_id}.{ext}"
                try:
                    client.remove_object(self.config.MINIO_BUCKET, object_name)
                    logger.info(f"删除截图: {object_name}")
                except S3Error:
                    pass
            
            return True
        except Exception as e:
            logger.error(f"删除截图失败: {e}")
            return False
    
    def get_screenshot_url(self, page_id: str) -> Optional[str]:
        """
        获取截图 URL
        
        Args:
            page_id: 页面 ID
            
        Returns:
            图片 URL，不存在返回 None
        """
        if not self.initialize():
            return None
        
        try:
            client = self._get_client()
            
            # 检查 png 和 jpg
            for ext in ["png", "jpg"]:
                object_name = f"{page_id}.{ext}"
                try:
                    client.stat_object(self.config.MINIO_BUCKET, object_name)
                    return f"{self.config.MINIO_PUBLIC_URL}/{self.config.MINIO_BUCKET}/{object_name}"
                except S3Error:
                    continue
            
            return None
        except Exception as e:
            logger.error(f"获取截图 URL 失败: {e}")
            return None
    
    def upload_report(
        self,
        file_path: str,
        filename: str,
    ) -> Optional[str]:
        """
        上传执行报告到 MinIO
        
        Args:
            file_path: 本地文件路径
            filename: 存储的文件名
            
        Returns:
            报告的访问 URL，失败返回 None
        """
        if not self.initialize():
            logger.error("MinIO 未初始化，无法上传报告")
            return None
        
        try:
            # 上传到 reports 子目录
            object_name = f"reports/{filename}"
            
            client = self._get_client()
            client.fput_object(
                bucket_name=self.config.MINIO_BUCKET,
                object_name=object_name,
                file_path=file_path,
                content_type="text/html"  # HTML 报告可直接在浏览器查看
            )
            
            # 返回公开访问 URL
            url = f"{self.config.MINIO_PUBLIC_URL}/{self.config.MINIO_BUCKET}/{object_name}"
            logger.info(f"报告上传成功: {url}")
            return url
            
        except Exception as e:
            logger.error(f"上传报告失败: {e}")
            return None
    
    def get_report_url(self, filename: str) -> Optional[str]:
        """
        获取报告的公开 URL
        
        Args:
            filename: 报告文件名
            
        Returns:
            报告 URL
        """
        object_name = f"reports/{filename}"
        return f"{self.config.MINIO_PUBLIC_URL}/{self.config.MINIO_BUCKET}/{object_name}"


# 全局单例
_minio_service: Optional[MinIOService] = None


def get_minio_service() -> MinIOService:
    """获取 MinIO 服务单例"""
    global _minio_service
    if _minio_service is None:
        _minio_service = MinIOService()
    return _minio_service
