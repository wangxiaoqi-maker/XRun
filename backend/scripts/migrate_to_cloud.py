#!/usr/bin/env python3
"""
数据迁移脚本 - 初始化云端数据库

功能：
1. 创建 MySQL 表结构
2. 创建 Milvus Collection
3. (可选) 从本地 SQLite 迁移数据
"""
import asyncio
import os
import sys

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv("../.Env")

from loguru import logger


async def test_mysql_connection():
    """测试 MySQL 连接"""
    from apps.ui_automation.config import settings
    from sqlalchemy.ext.asyncio import create_async_engine
    from sqlalchemy import text
    
    logger.info(f"📦 测试 MySQL 连接...")
    logger.info(f"   URL: {settings.DATABASE_URL[:50]}...")
    
    try:
        engine = create_async_engine(settings.DATABASE_URL, echo=False)
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT 1"))
            row = result.fetchone()
            if row and row[0] == 1:
                logger.success("✅ MySQL 连接成功!")
                return True
    except Exception as e:
        logger.error(f"❌ MySQL 连接失败: {e}")
        return False


async def create_mysql_tables():
    """创建 MySQL 表结构"""
    from apps.ui_automation.config import settings
    from sqlalchemy.ext.asyncio import create_async_engine
    from apps.ui_automation.database import Base
    from apps.ui_automation.knowledge.models import KnowledgeBase
    from apps.ui_automation.models.llm_config import LLMProvider, LLMModel, LLMUsageLog
    
    logger.info("📦 创建 MySQL 表结构...")
    
    try:
        engine = create_async_engine(settings.DATABASE_URL, echo=False)
        
        # 创建主应用表
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.success("✅ 主应用表创建完成")
        
        # 创建知识库表
        async with engine.begin() as conn:
            await conn.run_sync(KnowledgeBase.metadata.create_all)
        logger.success("✅ 知识库表创建完成")
        
        return True
    except Exception as e:
        logger.error(f"❌ 创建表失败: {e}")
        return False


async def test_milvus_connection():
    """测试 Milvus 连接"""
    from apps.ui_automation.knowledge.config import get_milvus_config
    
    config = get_milvus_config()
    logger.info(f"📦 测试 Milvus 连接...")
    logger.info(f"   URI: {config.MILVUS_URI}")
    logger.info(f"   Database: {config.MILVUS_DATABASE}")
    logger.info(f"   Collection: {config.MILVUS_COLLECTION}")
    
    try:
        from pymilvus import MilvusClient
        
        client = MilvusClient(
            uri=config.MILVUS_URI,
            token=config.MILVUS_TOKEN,
            timeout=config.MILVUS_TIMEOUT
        )
        
        # 测试连接
        collections = client.list_collections()
        logger.success(f"✅ Milvus 连接成功! 现有 collections: {collections}")
        return client
    except Exception as e:
        logger.error(f"❌ Milvus 连接失败: {e}")
        return None


async def create_milvus_collection():
    """创建 Milvus Collection"""
    from apps.ui_automation.knowledge.config import get_milvus_config, get_embedding_config
    from pymilvus import MilvusClient, DataType
    
    milvus_config = get_milvus_config()
    embedding_config = get_embedding_config()
    
    logger.info(f"📦 创建 Milvus Collection: {milvus_config.MILVUS_COLLECTION}")
    logger.info(f"   向量维度: {embedding_config.EMBEDDING_DIMENSION}")
    
    try:
        client = MilvusClient(
            uri=milvus_config.MILVUS_URI,
            token=milvus_config.MILVUS_TOKEN,
            timeout=milvus_config.MILVUS_TIMEOUT
        )
        
        collection_name = milvus_config.MILVUS_COLLECTION
        
        # 检查 collection 是否存在
        if client.has_collection(collection_name):
            logger.warning(f"⚠️ Collection '{collection_name}' 已存在")
            
            # 获取 collection 信息
            info = client.describe_collection(collection_name)
            logger.info(f"   现有 Collection 信息: {info}")
            
            # 询问是否重建
            response = input("是否删除并重建 Collection? (y/N): ")
            if response.lower() != 'y':
                logger.info("跳过 Collection 创建")
                return True
            
            # 删除现有 collection
            client.drop_collection(collection_name)
            logger.info(f"   已删除旧 Collection")
        
        # 创建新 collection - 使用 schema 方式
        from pymilvus import CollectionSchema, FieldSchema, DataType
        
        # 定义 schema
        fields = [
            FieldSchema(name="id", dtype=DataType.VARCHAR, is_primary=True, max_length=36),
            FieldSchema(name="vector", dtype=DataType.FLOAT_VECTOR, dim=embedding_config.EMBEDDING_DIMENSION),
            FieldSchema(name="description", dtype=DataType.VARCHAR, max_length=2000),
            FieldSchema(name="app_name", dtype=DataType.VARCHAR, max_length=200),
            FieldSchema(name="page_id", dtype=DataType.VARCHAR, max_length=36),
            FieldSchema(name="page_name", dtype=DataType.VARCHAR, max_length=200),
            FieldSchema(name="element_name", dtype=DataType.VARCHAR, max_length=200),
            FieldSchema(name="element_type", dtype=DataType.VARCHAR, max_length=50),
            FieldSchema(name="platform", dtype=DataType.VARCHAR, max_length=20),
        ]
        
        schema = CollectionSchema(fields=fields, description="Page elements for semantic search")
        
        # 使用底层 API 创建
        from pymilvus import connections, Collection, utility
        
        # 连接
        connections.connect(
            alias="default",
            uri=milvus_config.MILVUS_URI,
            token=milvus_config.MILVUS_TOKEN
        )
        
        # 创建 collection
        collection = Collection(name=collection_name, schema=schema)
        
        # 创建索引
        index_params = {
            "metric_type": "COSINE",
            "index_type": "AUTOINDEX",
            "params": {}
        }
        collection.create_index(field_name="vector", index_params=index_params)
        
        # 加载到内存
        collection.load()
        
        logger.success(f"✅ Collection '{collection_name}' 创建成功!")
        logger.info(f"   维度: {embedding_config.EMBEDDING_DIMENSION}")
        logger.info(f"   度量类型: COSINE")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 创建 Collection 失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_embedding_service():
    """测试 Embedding 服务"""
    from apps.ui_automation.knowledge.config import get_embedding_config
    from apps.ui_automation.knowledge.services.embedding_service import EmbeddingService
    
    config = get_embedding_config()
    logger.info(f"📦 测试 Embedding 服务...")
    logger.info(f"   Provider: {config.EMBEDDING_PROVIDER}")
    logger.info(f"   Model: {config.EMBEDDING_MODEL}")
    logger.info(f"   Dimension: {config.EMBEDDING_DIMENSION}")
    logger.info(f"   Base URL: {config.EMBEDDING_BASE_URL}")
    
    try:
        service = EmbeddingService(config)
        await service.initialize()
        
        # 测试生成向量
        test_text = "这是一个测试文本，用于验证 Embedding 服务是否正常工作。"
        embedding = await service.embed(test_text)
        
        if embedding and len(embedding) == config.EMBEDDING_DIMENSION:
            logger.success(f"✅ Embedding 服务正常! 向量维度: {len(embedding)}")
            return True
        else:
            logger.error(f"❌ Embedding 维度不匹配: 期望 {config.EMBEDDING_DIMENSION}, 实际 {len(embedding) if embedding else 0}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Embedding 服务测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """主函数"""
    logger.info("=" * 60)
    logger.info("🚀 XRun 云端数据库迁移工具")
    logger.info("=" * 60)
    
    results = {}
    
    # 1. 测试 MySQL 连接
    results["mysql_connection"] = await test_mysql_connection()
    
    # 2. 创建 MySQL 表
    if results["mysql_connection"]:
        results["mysql_tables"] = await create_mysql_tables()
    
    # 3. 测试 Milvus 连接
    results["milvus_connection"] = await test_milvus_connection() is not None
    
    # 4. 创建 Milvus Collection
    if results["milvus_connection"]:
        results["milvus_collection"] = await create_milvus_collection()
    
    # 5. 测试 Embedding 服务
    results["embedding_service"] = await test_embedding_service()
    
    # 输出结果
    logger.info("")
    logger.info("=" * 60)
    logger.info("📊 迁移结果汇总")
    logger.info("=" * 60)
    
    all_success = True
    for name, success in results.items():
        status = "✅" if success else "❌"
        logger.info(f"   {status} {name}: {'成功' if success else '失败'}")
        if not success:
            all_success = False
    
    if all_success:
        logger.success("")
        logger.success("🎉 所有迁移任务完成!")
        logger.success("   现在可以重启后端服务使用云端数据库了。")
    else:
        logger.error("")
        logger.error("⚠️ 部分任务失败，请检查配置后重试。")
    
    return all_success


if __name__ == "__main__":
    asyncio.run(main())
