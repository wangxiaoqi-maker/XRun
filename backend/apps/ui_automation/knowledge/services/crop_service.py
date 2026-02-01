"""
元素切图服务

从页面截图中根据 bbox 坐标裁剪出元素图片
"""
import io
import base64
from typing import Optional, List, Tuple
from PIL import Image
from loguru import logger

from .minio_service import get_minio_service


class CropService:
    """元素切图服务"""
    
    def __init__(self):
        self.minio_service = get_minio_service()
    
    def crop_element_from_base64(
        self,
        image_data: str,
        bbox: List[float],
        element_id: str,
        padding: int = 2
    ) -> Optional[str]:
        """
        从 Base64 图片中裁剪元素并上传到 MinIO
        
        Args:
            image_data: Base64 编码的页面截图
            bbox: 元素位置坐标 [left%, top%, width%, height%]
            element_id: 元素 ID
            padding: 裁剪时的边距扩展（像素）
            
        Returns:
            裁剪后图片的 URL，失败返回 None
        """
        if not bbox or len(bbox) != 4:
            logger.warning(f"无效的 bbox: {bbox}")
            return None
        
        try:
            # 解码 Base64 图片
            if ',' in image_data:
                image_data = image_data.split(',', 1)[1]
            
            image_bytes = base64.b64decode(image_data)
            image = Image.open(io.BytesIO(image_bytes))
            
            # 裁剪元素
            crop_bytes = self._crop_image(image, bbox, padding)
            if not crop_bytes:
                return None
            
            # 上传到 MinIO
            url = self.minio_service.upload_element_crop(
                image_bytes=crop_bytes,
                element_id=element_id
            )
            
            return url
            
        except Exception as e:
            logger.error(f"裁剪元素失败: {e}")
            return None
    
    def crop_element_from_url(
        self,
        image_url: str,
        bbox: List[float],
        element_id: str,
        padding: int = 2
    ) -> Optional[str]:
        """
        从 URL 图片中裁剪元素并上传到 MinIO
        
        Args:
            image_url: 页面截图 URL
            bbox: 元素位置坐标 [left%, top%, width%, height%]
            element_id: 元素 ID
            padding: 裁剪时的边距扩展（像素）
            
        Returns:
            裁剪后图片的 URL，失败返回 None
        """
        if not bbox or len(bbox) != 4:
            logger.warning(f"无效的 bbox: {bbox}")
            return None
        
        try:
            import httpx
            
            # 下载图片
            with httpx.Client(timeout=30) as client:
                response = client.get(image_url)
                response.raise_for_status()
                image_bytes = response.content
            
            image = Image.open(io.BytesIO(image_bytes))
            
            # 裁剪元素
            crop_bytes = self._crop_image(image, bbox, padding)
            if not crop_bytes:
                return None
            
            # 上传到 MinIO
            url = self.minio_service.upload_element_crop(
                image_bytes=crop_bytes,
                element_id=element_id
            )
            
            return url
            
        except Exception as e:
            logger.error(f"从 URL 裁剪元素失败: {e}")
            return None
    
    def _crop_image(
        self,
        image: Image.Image,
        bbox: List[float],
        padding: int = 2
    ) -> Optional[bytes]:
        """
        根据百分比 bbox 裁剪图片
        
        Args:
            image: PIL Image 对象
            bbox: [left%, top%, width%, height%]
            padding: 边距扩展
            
        Returns:
            裁剪后的图片字节数据
        """
        try:
            width, height = image.size
            left_pct, top_pct, w_pct, h_pct = bbox
            
            # 百分比转像素坐标
            left = int(width * left_pct / 100) - padding
            top = int(height * top_pct / 100) - padding
            right = int(width * (left_pct + w_pct) / 100) + padding
            bottom = int(height * (top_pct + h_pct) / 100) + padding
            
            # 确保不越界
            left = max(0, left)
            top = max(0, top)
            right = min(width, right)
            bottom = min(height, bottom)
            
            # 确保裁剪区域有效
            if right <= left or bottom <= top:
                logger.warning(f"裁剪区域无效: ({left}, {top}, {right}, {bottom})")
                return None
            
            # 裁剪
            cropped = image.crop((left, top, right, bottom))
            
            # 转换为字节
            output = io.BytesIO()
            cropped.save(output, format='PNG', optimize=True)
            return output.getvalue()
            
        except Exception as e:
            logger.error(f"图片裁剪失败: {e}")
            return None
    
    def batch_crop_elements(
        self,
        image_data: str,
        elements: List[dict]
    ) -> List[Tuple[str, Optional[str]]]:
        """
        批量裁剪元素
        
        Args:
            image_data: Base64 编码的页面截图
            elements: 元素列表，每个元素需包含 id 和 bbox
            
        Returns:
            [(element_id, crop_url), ...] 列表
        """
        results = []
        
        try:
            # 解码图片一次
            if ',' in image_data:
                image_data = image_data.split(',', 1)[1]
            
            image_bytes = base64.b64decode(image_data)
            image = Image.open(io.BytesIO(image_bytes))
            
            for element in elements:
                element_id = element.get('id')
                bbox = element.get('bbox')
                
                if not element_id or not bbox:
                    results.append((element_id, None))
                    continue
                
                # 裁剪并上传
                crop_bytes = self._crop_image(image, bbox)
                if crop_bytes:
                    url = self.minio_service.upload_element_crop(
                        image_bytes=crop_bytes,
                        element_id=element_id
                    )
                    results.append((element_id, url))
                else:
                    results.append((element_id, None))
            
        except Exception as e:
            logger.error(f"批量裁剪失败: {e}")
        
        return results


# 全局单例
_crop_service: Optional[CropService] = None


def get_crop_service() -> CropService:
    """获取切图服务单例"""
    global _crop_service
    if _crop_service is None:
        _crop_service = CropService()
    return _crop_service
