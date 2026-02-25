"""
执行 API V2

提供用例执行和实时日志推送功能
"""
import uuid
import asyncio
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, Query, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from apps.ui_automation.database import get_db, get_session
from apps.ui_automation.execution.models import (
    TestCaseV2,
    ExecutionConfig,
    ExecutionRecord,
    GlobalVariable,
    Platform,
    ExecutionStatus,
    ConfigScope,
)
from apps.ui_automation.execution.schemas.execution import (
    ExecutionRequest,
    ExecutionResponse,
    ExecutionStatusResponse,
)
from apps.ui_automation.execution.compiler import TypeScriptCompiler
from apps.ui_automation.execution.runners.vitest_runner import VitestRunner
from apps.ui_automation.execution.services.knowledge_adapter import KnowledgeAdapter
from apps.ui_automation.models.llm_config import LLMProvider, LLMModel, ModelStatus

router = APIRouter(prefix="/executions", tags=["执行管理 V2"])

# 执行日志存储（内存，用于 WebSocket 推送）
# 生产环境应使用 Redis Pub/Sub
_execution_logs: dict[str, list[str]] = {}
_execution_status: dict[str, dict[str, Any]] = {}


async def _detect_wda_port() -> int | None:
    """
    检测已运行的 WDA 端口
    
    扫描常见端口，检查是否有 WDA 服务在运行
    """
    import httpx
    
    # 常见的 WDA 端口范围
    # iproxy 转发的端口通常在 55000+ 范围
    # 默认端口 8100
    ports_to_check = [8100, 55338, 55339]
    
    # 也检查最近使用的端口（从 50000 到 60000 中的常见端口）
    for port in range(55330, 55350):
        if port not in ports_to_check:
            ports_to_check.append(port)
    
    async with httpx.AsyncClient(timeout=1.0) as client:
        for port in ports_to_check:
            try:
                resp = await client.get(f"http://localhost:{port}/status")
                if resp.status_code == 200:
                    data = resp.json()
                    # WDA 的 /status 返回包含 "value" 和 "sessionId"
                    if "value" in data:
                        return port
            except Exception:
                continue
    
    return None


async def _get_vision_model_config(session) -> dict[str, Any] | None:
    """
    从平台模型配置中获取默认视觉模型
    
    与 AI 分析页面使用相同的模型配置源：llm_providers + llm_models
    
    优先级：
    1. is_default=True 的视觉模型
    2. qwen 供应商的视觉模型（Midscene 对 qwen 支持最好）
    3. 其他启用的视觉模型
    """
    from sqlalchemy import and_
    
    # 1. 查找默认的视觉模型
    result = await session.execute(
        select(LLMModel).where(
            and_(
                LLMModel.supports_vision == True,
                LLMModel.status == ModelStatus.ENABLED,
                LLMModel.is_default == True
            )
        )
    )
    model = result.scalar_one_or_none()
    
    # 2. 如果没有默认的，优先选择 gemini 或 qwen 供应商的视觉模型
    # Midscene 对 Gemini 和 Qwen VL 的支持最好
    preferred_providers = ["google", "gemini", "qwen"]
    
    if not model:
        for provider_code in preferred_providers:
            provider_result = await session.execute(
                select(LLMProvider).where(
                    and_(
                        LLMProvider.code == provider_code,
                        LLMProvider.status == ModelStatus.ENABLED
                    )
                )
            )
            found_provider = provider_result.scalar_one_or_none()
            
            if found_provider:
                result = await session.execute(
                    select(LLMModel).where(
                        and_(
                            LLMModel.provider_id == found_provider.id,
                            LLMModel.supports_vision == True,
                            LLMModel.status == ModelStatus.ENABLED
                        )
                    ).order_by(LLMModel.created_at.desc()).limit(1)
                )
                model = result.scalar_one_or_none()
                if model:
                    break
    
    # 3. 最后取任意一个启用的视觉模型
    if not model:
        result = await session.execute(
            select(LLMModel).where(
                and_(
                    LLMModel.supports_vision == True,
                    LLMModel.status == ModelStatus.ENABLED
                )
            ).order_by(LLMModel.created_at.desc()).limit(1)
        )
        model = result.scalar_one_or_none()
    
    if not model:
        return None
    
    # 获取供应商信息
    provider_result = await session.execute(
        select(LLMProvider).where(LLMProvider.id == model.provider_id)
    )
    provider = provider_result.scalar_one_or_none()
    
    if not provider or not provider.api_key:
        return None
    
    # 尝试从 config 中提取 model_family
    model_family = None
    if model.config and isinstance(model.config, dict):
        model_family = model.config.get("model_family")
    
    # 根据供应商代码推断 model_family（如果未配置）
    # Midscene 支持的 MODEL_FAMILY 值有限（来自源码）:
    # 'doubao-vision', 'gemini', 'qwen2.5-vl', 'qwen3-vl', 'vlm-ui-tars', 
    # 'vlm-ui-tars-doubao', 'glm-v', 'auto-glm', 'gpt-5'
    # 注意：gpt-4o 不支持！只支持 gpt-5
    if not model_family:
        family_mapping = {
            "qwen": "qwen2.5-vl",
            "openai": "gpt-5",  # Midscene 只支持 gpt-5，不支持 gpt-4o
            "zhipu": "glm-v",
            "doubao": "doubao-vision",
            "google": "gemini",
            "gemini": "gemini",  # 供应商代码可能是 gemini 或 google
            # Claude 等通过 OpenAI 兼容接口的模型，使用 qwen2.5-vl 格式
            "claude": "qwen2.5-vl",
            "anthropic": "qwen2.5-vl",
        }
        model_family = family_mapping.get(provider.code)
    
    # 如果仍然没有 model_family，使用默认值
    if not model_family:
        model_family = "qwen2.5-vl"  # 默认使用 qwen2.5-vl
    
    return {
        "model_base_url": provider.base_url,
        "model_api_key": provider.api_key,
        "model_name": model.model_id,  # 使用 model_id（如 qwen-vl-max）
        "model_family": model_family
    }


@router.post("", response_model=ExecutionResponse)
async def start_execution(
    request: ExecutionRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
) -> ExecutionResponse:
    """
    启动用例执行
    
    1. 获取用例和配置
    2. 编译为 TypeScript
    3. 后台执行测试
    4. 返回执行 ID 和 WebSocket 地址
    """
    # 获取用例
    result = await db.execute(
        select(TestCaseV2).where(TestCaseV2.id == request.case_id)
    )
    case = result.scalar_one_or_none()
    
    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Test case {request.case_id} not found"
        )
    
    # 创建执行记录
    execution_id = str(uuid.uuid4())
    execution = ExecutionRecord(
        id=execution_id,
        case_id=case.id,
        device_id=request.device_id,
        platform=case.platform,
        status=ExecutionStatus.PENDING,
        variables_snapshot=request.variables,
        trigger_source="api",
    )
    
    db.add(execution)
    await db.commit()
    
    # 初始化日志存储
    _execution_logs[execution_id] = []
    _execution_status[execution_id] = {
        "status": ExecutionStatus.PENDING.value,
        "case_id": case.id,
        "device_id": request.device_id,
    }
    
    # 后台执行
    background_tasks.add_task(
        _run_execution,
        execution_id=execution_id,
        case=case.to_dict(),
        device_id=request.device_id,
        variables=request.variables,
        config_overrides=request.config_overrides,
    )
    
    return ExecutionResponse(
        execution_id=execution_id,
        status=ExecutionStatus.PENDING.value,
        websocket_url=f"/api/v2/executions/{execution_id}/logs",
        estimated_duration=case.get_step_count() * 30000,  # 预估每步骤 30 秒
    )


async def _run_execution(
    execution_id: str,
    case: dict[str, Any],
    device_id: str,
    variables: dict[str, Any] | None = None,
    config_overrides: dict[str, Any] | None = None,
) -> None:
    """后台执行任务"""
    
    def log(message: str):
        """日志回调"""
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        log_entry = f"[{timestamp}] {message}"
        _execution_logs.setdefault(execution_id, []).append(log_entry)
        print(f"[Execution {execution_id[:8]}] {message}")  # 同时打印到控制台
    
    try:
        async with get_session() as session:
            # 更新状态：编译中
            _execution_status[execution_id]["status"] = ExecutionStatus.COMPILING.value
            log("[Compiler] Starting compilation...")
            
            # 获取全局变量
            global_vars_result = await session.execute(
                select(GlobalVariable).where(
                    GlobalVariable.scope == ConfigScope.GLOBAL,
                    GlobalVariable.is_active == True,
                )
            )
            global_vars = [v.to_dict(mask_secret=False) for v in global_vars_result.scalars().all()]
            
            # 获取配置
            config_result = await session.execute(
                select(ExecutionConfig).where(
                    ExecutionConfig.scope == ConfigScope.GLOBAL,
                )
            )
            config = config_result.scalar_one_or_none()
            base_config = config.to_dict() if config else {}
            
            # 合并配置覆盖
            if config_overrides:
                base_config.update(config_overrides)
                log(f"[Config] config_overrides: {config_overrides}")
            
            # 如果配置中没有模型信息，从 llm_providers + llm_models 表获取默认视觉模型
            # 与 AI 分析页面使用相同的模型配置源
            if not base_config.get("model_name") or not base_config.get("model_base_url"):
                log("[Config] No model config found, loading from platform models...")
                model_config = await _get_vision_model_config(session)
                if model_config:
                    log(f"[Config] Using model: {model_config.get('model_name')} from {model_config.get('model_base_url')}")
                    base_config["model_name"] = model_config.get("model_name")
                    base_config["model_base_url"] = model_config.get("model_base_url")
                    base_config["model_api_key"] = model_config.get("model_api_key")
                    base_config["model_family"] = model_config.get("model_family")
                else:
                    log("[Config] WARNING: No vision model configured in platform!")
            
            # 对于 iOS 平台，确保 WDA 端口配置正确
            # 优先使用前端传递的 wda_port（投屏时已启动 WDA）
            # 如果没有传递，则尝试检测已运行的 WDA
            platform = case.get("platform", "")
            log(f"[Device] Case platform: {platform}")
            
            if platform.lower() == "ios":
                if base_config.get("wda_port"):
                    # 前端已传递 wda_port（投屏时启动的 WDA）
                    log(f"[Device] Using WDA port from config: {base_config.get('wda_port')}")
                else:
                    # 尝试检测已运行的 WDA
                    log(f"[Device] No WDA port in config, detecting...")
                    wda_port = await _detect_wda_port()
                    if wda_port:
                        log(f"[Device] WDA detected on port: {wda_port}")
                        base_config["wda_port"] = wda_port
                        base_config["wda_host"] = "localhost"
                    else:
                        log(f"[Device] WARNING: No WDA detected, test may fail!")
            
            # 计算用例内容 hash，判断是否需要重新编译
            # 包含模板版本，模板更新后缓存自动失效
            import hashlib
            import json
            TEMPLATE_VERSION = "v3"  # 修复 IOSAgent import 问题
            hash_input = json.dumps({
                "steps": case.get("steps_json", []),
                "template_version": TEMPLATE_VERSION,
            }, sort_keys=True)
            case_content_hash = hashlib.sha256(hash_input.encode()).hexdigest()[:16]
            
            # 检查用例是否有缓存的编译内容
            cached_content = case.get("compiled_content")
            cached_hash = case.get("compiled_hash")
            
            ts_content = None
            content_hash = None
            
            if cached_content and cached_hash == case_content_hash:
                # 使用缓存
                log(f"[Compiler] Using cached compilation (hash: {cached_hash})")
                ts_content = cached_content
                content_hash = cached_hash
            else:
                # 需要重新编译
                log("[Compiler] Cache miss, compiling...")
                
                # 设置知识库适配器
                knowledge_adapter = KnowledgeAdapter(session)
                
                # 编译用例
                compiler = TypeScriptCompiler()
                compiler.set_knowledge_service(knowledge_adapter)
                
                compile_result = await compiler.compile(
                    case=case,
                    config=base_config,
                    global_variables=global_vars,
                    runtime_variables=variables,
                    write_to_file=False,  # 不写入文件，存数据库
                )
                
                if not compile_result.success:
                    log(f"[Compiler] Compilation failed: {compile_result.errors}")
                    _execution_status[execution_id]["status"] = ExecutionStatus.FAILED.value
                    
                    # 更新数据库记录
                    exec_result = await session.execute(
                        select(ExecutionRecord).where(ExecutionRecord.id == execution_id)
                    )
                    execution = exec_result.scalar_one_or_none()
                    if execution:
                        execution.status = ExecutionStatus.FAILED
                        execution.error_message = f"Compilation failed: {', '.join(compile_result.errors)}"
                        execution.finished_at = datetime.now()
                        await session.commit()
                    return
                
                ts_content = compile_result.output_content
                content_hash = compile_result.content_hash
                
                # 更新用例的编译缓存
                case_result = await session.execute(
                    select(TestCaseV2).where(TestCaseV2.id == case.get("id"))
                )
                case_obj = case_result.scalar_one_or_none()
                if case_obj:
                    case_obj.compiled_content = ts_content
                    case_obj.compiled_hash = case_content_hash
                    case_obj.compiled_at = datetime.now()
                
                log(f"[Compiler] Compiled successfully (hash: {content_hash})")
            
            # 更新状态：执行中
            _execution_status[execution_id]["status"] = ExecutionStatus.RUNNING.value
            log("[Runner] Starting test execution...")
            
            # 执行测试
            runner = VitestRunner()
            
            # 准备环境变量
            compiler = TypeScriptCompiler()
            env_vars = compiler.get_env_variables(base_config, variables)
            env_vars["DEVICE_ID"] = device_id
            
            # 日志记录关键环境变量
            log(f"[Runner] WDA_PORT={env_vars.get('WDA_PORT', 'not set')}, WDA_HOST={env_vars.get('WDA_HOST', 'not set')}")
            log(f"[Runner] base_config keys: {list(base_config.keys())}")
            log(f"[Runner] MIDSCENE_MODEL_NAME={env_vars.get('MIDSCENE_MODEL_NAME', 'not set')}")
            log(f"[Runner] MIDSCENE_MODEL_FAMILY={env_vars.get('MIDSCENE_MODEL_FAMILY', 'not set')}")
            log(f"[Runner] model_family in base_config: {base_config.get('model_family', 'not set')}")
            
            # 执行（使用内容而非文件路径）
            run_result = await runner.run(
                test_content=ts_content,  # 直接传内容
                env_vars=env_vars,
                device_id=device_id,
                platform=Platform(case.get("platform", "android")),
                on_log=log,
            )
            
            # 更新状态
            _execution_status[execution_id]["status"] = run_result.status.value
            _execution_status[execution_id]["duration_ms"] = run_result.duration_ms
            _execution_status[execution_id]["report_url"] = run_result.report_url
            
            log(f"[Runner] Execution completed with status: {run_result.status.value}")
            
            # 异步上传报告到 MinIO（不阻塞）
            if run_result.report_url:
                try:
                    from apps.ui_automation.knowledge.services.minio_service import get_minio_service
                    import asyncio
                    
                    async def upload_report_async():
                        try:
                            # 从本地 URL 中提取文件名
                            report_filename = run_result.report_url.split("/")[-1].replace("/view", "")
                            base_dir = Path(__file__).parent.parent.parent.parent.parent.parent
                            report_path = base_dir / "midscene-executor" / "midscene_run" / "report" / report_filename
                            
                            if report_path.exists():
                                minio_service = get_minio_service()
                                minio_url = minio_service.upload_report(str(report_path), report_filename)
                                if minio_url:
                                    log(f"[MinIO] 报告已上传: {minio_url}")
                                    # 更新执行记录的报告 URL
                                    _execution_status[execution_id]["report_url"] = minio_url
                                    run_result.report_url = minio_url
                        except Exception as e:
                            log(f"[MinIO] 上传报告失败（不影响执行）: {e}")
                    
                    # 创建异步任务上传（不等待完成）
                    asyncio.create_task(upload_report_async())
                except Exception as e:
                    log(f"[MinIO] 初始化上传任务失败: {e}")
            
            # 更新数据库记录
            exec_result = await session.execute(
                select(ExecutionRecord).where(ExecutionRecord.id == execution_id)
            )
            execution = exec_result.scalar_one_or_none()
            if execution:
                execution.status = run_result.status
                execution.started_at = run_result.started_at
                execution.finished_at = run_result.finished_at
                execution.duration_ms = run_result.duration_ms
                execution.report_url = run_result.report_url
                execution.report_data = run_result.report_data
                execution.error_message = run_result.error_message
                execution.error_stack = run_result.error_stack
                execution.steps_result = run_result.steps_result
                execution.total_steps = run_result.total_steps
                execution.passed_steps = run_result.passed_steps
                execution.failed_steps = run_result.failed_steps
                execution.skipped_steps = run_result.skipped_steps
                execution.compiled_script_content = ts_content  # 存储编译内容
                execution.compiled_script_hash = content_hash
                await session.commit()
            
    except Exception as e:
        log(f"[Error] Execution failed: {str(e)}")
        _execution_status[execution_id]["status"] = ExecutionStatus.FAILED.value
        _execution_status[execution_id]["error"] = str(e)


# ==================== 报告管理（必须在 /{execution_id} 之前定义）====================

@router.get("/reports")
async def list_reports(
    limit: int = Query(20, ge=1, le=100, description="返回数量"),
) -> dict[str, Any]:
    """
    获取 Midscene 执行报告列表
    
    扫描报告目录，返回最新的报告文件
    自动检查 MinIO 是否已有该报告，优先返回 MinIO URL
    """
    from pathlib import Path
    from apps.ui_automation.knowledge.services.minio_service import get_minio_service
    
    # 报告目录
    base_dir = Path(__file__).parent.parent.parent.parent.parent.parent
    report_dir = base_dir / "midscene-executor" / "midscene_run" / "report"
    
    if not report_dir.exists():
        return {"reports": [], "report_dir": str(report_dir)}
    
    # 获取 MinIO 服务（用于检查文件是否已上传）
    minio_service = None
    try:
        minio_service = get_minio_service()
    except Exception:
        pass
    
    reports = []
    for f in sorted(report_dir.glob("*.html"), key=lambda x: x.stat().st_mtime, reverse=True)[:limit]:
        stat = f.stat()
        # 解析文件名获取信息: ios-2026-02-05_17-17-51-0dce4334.html
        parts = f.stem.split("-")
        platform = parts[0] if parts else "unknown"
        
        # 检查 MinIO 是否已有该文件，有则返回 MinIO URL
        url = f"/api/v2/executions/reports/{f.name}/view"  # 默认本地 URL
        minio_url = None
        
        if minio_service:
            # 直接构建 MinIO URL（不做网络请求检查，假设执行后已上传）
            minio_url = minio_service.get_report_url(f.name)
        
        reports.append({
            "filename": f.name,
            "platform": platform,
            "size": stat.st_size,
            "size_mb": round(stat.st_size / 1024 / 1024, 2),
            "created_at": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            "url": minio_url or url,  # 优先 MinIO URL
            "local_url": url,  # 备用本地 URL
        })
    
    return {
        "reports": reports,
        "report_dir": str(report_dir),
        "total": len(reports),
    }


@router.post("/reports/{filename}/sync-to-minio")
async def sync_report_to_minio(filename: str) -> dict[str, Any]:
    """
    将指定报告同步到 MinIO，返回公开 URL
    
    单独的接口，避免列表接口超时
    """
    from pathlib import Path
    from apps.ui_automation.knowledge.services.minio_service import get_minio_service
    
    base_dir = Path(__file__).parent.parent.parent.parent.parent.parent
    report_path = base_dir / "midscene-executor" / "midscene_run" / "report" / filename
    
    if not report_path.exists():
        raise HTTPException(status_code=404, detail=f"报告不存在: {filename}")
    
    minio_service = get_minio_service()
    try:
        url = minio_service.upload_report(str(report_path), filename)
        if url:
            return {"success": True, "url": url, "filename": filename}
        else:
            return {"success": False, "error": "上传失败", "url": f"/api/v2/executions/reports/{filename}/view"}
    except Exception as e:
        return {"success": False, "error": str(e), "url": f"/api/v2/executions/reports/{filename}/view"}


@router.get("/reports/{filename}/view")
async def view_report(filename: str):
    """
    在浏览器中直接查看报告（不下载）
    """
    from pathlib import Path
    from fastapi.responses import HTMLResponse
    
    base_dir = Path(__file__).parent.parent.parent.parent.parent.parent
    report_path = base_dir / "midscene-executor" / "midscene_run" / "report" / filename
    
    if not report_path.exists() or not report_path.is_file():
        raise HTTPException(status_code=404, detail="Report not found")
    
    # 读取 HTML 内容并返回
    content = report_path.read_text(encoding='utf-8')
    return HTMLResponse(content=content)


@router.get("/reports/{filename}")
async def download_report(filename: str):
    """
    下载报告文件
    """
    from pathlib import Path
    from fastapi.responses import FileResponse
    
    base_dir = Path(__file__).parent.parent.parent.parent.parent.parent
    report_path = base_dir / "midscene-executor" / "midscene_run" / "report" / filename
    
    if not report_path.exists() or not report_path.is_file():
        raise HTTPException(status_code=404, detail="Report not found")
    
    return FileResponse(
        path=str(report_path),
        media_type="text/html",
        filename=filename
    )


@router.get("/{execution_id}", response_model=ExecutionStatusResponse)
async def get_execution_status(
    execution_id: str,
    db: AsyncSession = Depends(get_db),
) -> ExecutionStatusResponse:
    """获取执行状态"""
    result = await db.execute(
        select(ExecutionRecord).where(ExecutionRecord.id == execution_id)
    )
    execution = result.scalar_one_or_none()
    
    if not execution:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Execution {execution_id} not found"
        )
    
    return ExecutionStatusResponse(
        id=execution.id,
        case_id=execution.case_id,
        device_id=execution.device_id,
        device_name=execution.device_name,
        platform=execution.platform.value if execution.platform else "",
        status=execution.status.value if execution.status else "pending",
        started_at=execution.started_at,
        finished_at=execution.finished_at,
        duration_ms=execution.duration_ms,
        report_url=execution.report_url,
        error_message=execution.error_message,
        total_steps=execution.total_steps,
        passed_steps=execution.passed_steps,
        failed_steps=execution.failed_steps,
        skipped_steps=execution.skipped_steps,
        steps_result=execution.steps_result,
    )


@router.post("/{execution_id}/cancel")
async def cancel_execution(
    execution_id: str,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """取消执行"""
    result = await db.execute(
        select(ExecutionRecord).where(ExecutionRecord.id == execution_id)
    )
    execution = result.scalar_one_or_none()
    
    if not execution:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Execution {execution_id} not found"
        )
    
    if execution.is_finished():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Execution already finished"
        )
    
    # 更新状态
    execution.status = ExecutionStatus.CANCELLED
    execution.finished_at = datetime.now()
    execution.calculate_duration()
    
    await db.commit()
    
    # 更新内存状态
    if execution_id in _execution_status:
        _execution_status[execution_id]["status"] = ExecutionStatus.CANCELLED.value
    
    return {"success": True, "message": "Execution cancelled"}


@router.websocket("/{execution_id}/logs")
async def execution_logs_ws(
    websocket: WebSocket,
    execution_id: str,
):
    """
    WebSocket 实时日志推送
    
    客户端连接后，会持续接收执行日志
    """
    await websocket.accept()
    
    try:
        # 发送已有的日志
        if execution_id in _execution_logs:
            for log in _execution_logs[execution_id]:
                await websocket.send_json({"type": "log", "message": log})
        
        # 发送当前状态
        if execution_id in _execution_status:
            await websocket.send_json({
                "type": "status",
                "data": _execution_status[execution_id],
            })
        
        # 持续推送新日志
        last_log_count = len(_execution_logs.get(execution_id, []))
        
        while True:
            await asyncio.sleep(0.5)  # 轮询间隔
            
            # 检查是否有新日志
            current_logs = _execution_logs.get(execution_id, [])
            if len(current_logs) > last_log_count:
                for log in current_logs[last_log_count:]:
                    await websocket.send_json({"type": "log", "message": log})
                last_log_count = len(current_logs)
            
            # 发送状态更新
            if execution_id in _execution_status:
                status_data = _execution_status[execution_id]
                await websocket.send_json({
                    "type": "status",
                    "data": status_data,
                })
                
                # 如果执行完成，发送结束信号并关闭
                if status_data.get("status") in [
                    ExecutionStatus.PASSED.value,
                    ExecutionStatus.FAILED.value,
                    ExecutionStatus.CANCELLED.value,
                    ExecutionStatus.TIMEOUT.value,
                ]:
                    await websocket.send_json({"type": "end"})
                    break
    
    except WebSocketDisconnect:
        pass
    except Exception as e:
        try:
            await websocket.send_json({"type": "error", "message": str(e)})
        except:
            pass
    finally:
        try:
            await websocket.close()
        except:
            pass


@router.get("", response_model=dict[str, Any])
async def list_executions(
    case_id: str | None = Query(None, description="用例 ID"),
    status: ExecutionStatus | None = Query(None, description="状态"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """获取执行记录列表"""
    from sqlalchemy import func
    
    query = select(ExecutionRecord)
    
    if case_id:
        query = query.where(ExecutionRecord.case_id == case_id)
    if status:
        query = query.where(ExecutionRecord.status == status)
    
    # 统计总数
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0
    
    # 分页
    query = query.order_by(ExecutionRecord.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)
    
    result = await db.execute(query)
    executions = result.scalars().all()
    
    return {
        "total": total,
        "items": [e.to_summary() for e in executions],
        "page": page,
        "page_size": page_size,
    }
