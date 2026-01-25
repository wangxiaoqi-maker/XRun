"""
执行 API
"""
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, WebSocket
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
import uuid
import asyncio
import json
import yaml
from datetime import datetime
from pathlib import Path

from apps.ui_automation.database import get_db
from apps.ui_automation.models.test_case import TestCase
from apps.ui_automation.models.execution import Execution
from apps.ui_automation.models.ai_config import AIConfig
from apps.ui_automation.schemas.execution import ExecutionRequest, ExecutionResponse, ExecutionList
from apps.ui_automation.config import settings

router = APIRouter()

# 执行状态缓存
execution_cache = {}

def model_to_response(execution: Execution) -> ExecutionResponse:
    """模型转响应"""
    return ExecutionResponse(
        id=execution.id,
        case_id=execution.case_id,
        device_id=execution.device_id,
        platform=execution.platform,
        status=execution.status,
        logs=execution.logs,
        report_path=execution.report_path,
        duration_ms=execution.duration_ms,
        error_message=execution.error_message,
        started_at=execution.started_at,
        finished_at=execution.finished_at,
        created_at=execution.created_at
    )

async def get_active_ai_config(db: AsyncSession) -> dict:
    """获取激活的 AI 配置"""
    result = await db.execute(
        select(AIConfig).where(AIConfig.is_active == True)
    )
    config = result.scalar_one_or_none()
    
    if config:
        return {
            "base_url": config.base_url,
            "api_key": config.api_key,
            "model_name": config.model_name,
            "model_family": config.model_family
        }
    return None

async def run_execution(
    execution_id: str,
    case_yaml: str,
    device_id: str,
    platform: str,
    ai_config: dict
):
    """运行用例执行"""
    from apps.ui_automation.database import AsyncSessionLocal
    
    logs = []
    start_time = datetime.now()
    
    def log(msg: str):
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {msg}"
        logs.append(log_entry)
        execution_cache[execution_id]["logs"] = logs
        print(log_entry)
    
    async with AsyncSessionLocal() as db:
        # 更新状态为运行中
        result = await db.execute(
            select(Execution).where(Execution.id == execution_id)
        )
        execution = result.scalar_one()
        execution.status = "running"
        execution.started_at = start_time
        await db.commit()
        
        execution_cache[execution_id]["status"] = "running"
        
        try:
            log(f"🚀 开始执行用例 (设备: {device_id})")
            
            # 解析 YAML
            case_data = yaml.safe_load(case_yaml)
            steps = case_data.get("steps", [])
            
            log(f"📋 共 {len(steps)} 个步骤")
            
            # 生成执行脚本并调用 Node.js 执行器
            script_content = generate_executor_script(
                steps=steps,
                device_id=device_id,
                platform=platform,
                ai_config=ai_config,
                execution_id=execution_id
            )
            
            # 保存临时脚本
            script_path = Path(settings.EXECUTOR_PATH) / f"temp_{execution_id}.js"
            script_path.parent.mkdir(parents=True, exist_ok=True)
            script_path.write_text(script_content)
            
            log("📝 执行脚本已生成")
            
            # 创建 .env 文件给执行器
            env_content = ""
            if ai_config:
                env_content = f"""
MIDSCENE_MODEL_BASE_URL={ai_config.get('base_url', '')}
MIDSCENE_MODEL_API_KEY={ai_config.get('api_key', '')}
MIDSCENE_MODEL_NAME={ai_config.get('model_name', '')}
MIDSCENE_MODEL_FAMILY={ai_config.get('model_family', '')}
"""
                env_path = Path(settings.EXECUTOR_PATH) / ".env"
                env_path.write_text(env_content)
            
            # 执行脚本
            process = await asyncio.create_subprocess_exec(
                "node", str(script_path),
                cwd=str(Path(settings.EXECUTOR_PATH)),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            # 读取输出
            while True:
                line = await process.stdout.readline()
                if not line:
                    break
                log(line.decode().strip())
            
            await process.wait()
            
            # 检查执行结果
            if process.returncode == 0:
                execution.status = "success"
                log("✅ 用例执行成功!")
            else:
                stderr = await process.stderr.read()
                execution.status = "failed"
                execution.error_message = stderr.decode()
                log(f"❌ 用例执行失败: {stderr.decode()}")
            
            # 清理临时脚本
            script_path.unlink(missing_ok=True)
            
        except Exception as e:
            execution.status = "error"
            execution.error_message = str(e)
            log(f"❌ 执行出错: {e}")
        
        # 更新最终状态
        execution.finished_at = datetime.now()
        execution.duration_ms = int((execution.finished_at - start_time).total_seconds() * 1000)
        execution.logs = "\n".join(logs)
        
        # 查找报告
        report_dir = Path(settings.EXECUTOR_PATH) / "midscene_run" / "report"
        if report_dir.exists():
            reports = sorted(report_dir.glob("*.html"), key=lambda x: x.stat().st_mtime, reverse=True)
            if reports:
                execution.report_path = str(reports[0])
        
        await db.commit()
        
        execution_cache[execution_id]["status"] = execution.status
        execution_cache[execution_id]["finished"] = True

def generate_executor_script(
    steps: list,
    device_id: str,
    platform: str,
    ai_config: dict,
    execution_id: str
) -> str:
    """生成执行脚本"""
    
    steps_code = []
    for i, step in enumerate(steps):
        step_type = step.get("type", "")
        prompt = step.get("prompt", "")
        desc = step.get("description", f"步骤 {i+1}")
        
        if step_type == "aiTap":
            code = f'''
    console.log("▶️  步骤 {i+1}: {desc}");
    await agent.aiTap("{prompt}");
    await sleep(1000);
'''
        elif step_type == "aiInput":
            text = step.get("text", "")
            code = f'''
    console.log("▶️  步骤 {i+1}: {desc}");
    await agent.aiInput("{prompt}", {{ value: "{text}" }});
    await sleep(500);
'''
        elif step_type == "aiSwipe":
            direction = step.get("direction", "up")
            code = f'''
    console.log("▶️  步骤 {i+1}: {desc}");
    await agent.aiSwipe("{prompt}", "{direction}");
    await sleep(500);
'''
        elif step_type == "aiAssert":
            code = f'''
    console.log("▶️  步骤 {i+1}: {desc}");
    await agent.aiAssert("{prompt}");
'''
        elif step_type == "aiWait":
            timeout = step.get("timeout", 10000)
            code = f'''
    console.log("▶️  步骤 {i+1}: {desc}");
    await agent.aiWaitFor("{prompt}", {{ timeout: {timeout} }});
'''
        elif step_type == "aiQuery":
            code = f'''
    console.log("▶️  步骤 {i+1}: {desc}");
    const result_{i} = await agent.aiQuery("{prompt}");
    console.log("   查询结果:", JSON.stringify(result_{i}));
'''
        elif step_type == "tap":
            x = step.get("x", 0)
            y = step.get("y", 0)
            code = f'''
    console.log("▶️  步骤 {i+1}: {desc}");
    await deviceInterface.tap({x}, {y});
    await sleep(500);
'''
        elif step_type == "swipe":
            sx = step.get("startX", 0)
            sy = step.get("startY", 0)
            ex = step.get("endX", 0)
            ey = step.get("endY", 0)
            duration = step.get("duration", 300)
            code = f'''
    console.log("▶️  步骤 {i+1}: {desc}");
    await deviceInterface.swipe({sx}, {sy}, {ex}, {ey}, {duration});
    await sleep(500);
'''
        elif step_type == "input":
            text = step.get("text", "")
            code = f'''
    console.log("▶️  步骤 {i+1}: {desc}");
    await deviceInterface.input("{text}");
    await sleep(300);
'''
        elif step_type == "back":
            code = f'''
    console.log("▶️  步骤 {i+1}: {desc}");
    await deviceInterface.back();
    await sleep(500);
'''
        elif step_type == "home":
            code = f'''
    console.log("▶️  步骤 {i+1}: {desc}");
    await deviceInterface.home();
    await sleep(500);
'''
        elif step_type == "launch":
            if platform == "ios":
                bundle_id = step.get("bundleId", "")
                code = f'''
    console.log("▶️  步骤 {i+1}: {desc}");
    await deviceInterface.launchApp("{bundle_id}");
    await sleep(2000);
'''
            else:
                package = step.get("package", "")
                activity = step.get("activity", "")
                code = f'''
    console.log("▶️  步骤 {i+1}: {desc}");
    await deviceInterface.launchApp("{package}", "{activity}");
    await sleep(2000);
'''
        elif step_type == "sleep":
            duration = step.get("duration", 1000)
            code = f'''
    console.log("▶️  步骤 {i+1}: {desc}");
    await sleep({duration});
'''
        elif step_type == "screenshot":
            code = f'''
    console.log("▶️  步骤 {i+1}: {desc}");
    await agent.recordToReport("{desc}");
'''
        elif step_type in ["scheme", "schemeUrl", "schemeRouter"]:
            # iOS Scheme 跳转 steps
            # schemeUrl: 完整 URL (myapp://page)
            # schemeRouter: 路由路径 (page/detail) -> 需要拼接或者直接作为 URL 处理（视业务定义，暂统一处理）
            url = step.get("url", "") or step.get("value", "") # Support 'value' from frontend input
            
            code = f'''
    console.log("▶️  步骤 {i+1}: {desc} (Scheme: {url})");
    try {{
        const {{ execSync }} = require('child_process');
        // Call backend API
        execSync(`curl -X POST "http://127.0.0.1:8000/api/devices/ios/native/scheme-jump?url={url}" -s`);
        console.log("   跳转指令已发送");
    }} catch (e) {{
        console.error("   跳转失败:", e.message);
    }}
    await sleep(2000);
'''
        else:
            code = f'    // 未知步骤类型: {step_type}\n'
        
        steps_code.append(code)
    
    interface_class = "AndroidInterface" if platform == "android" else "IOSInterface"
    
    script = f'''
import {{ createAgent }} from '@midscene/core';
import {{ {interface_class} }} from './src/{platform}_interface.js';
import 'dotenv/config';

const sleep = (ms) => new Promise(resolve => setTimeout(resolve, ms));

async function main() {{
    console.log("🚀 开始执行用例...");
    console.log("📱 平台: {platform}");
    console.log("🔧 设备: {device_id}\\n");
    
    const deviceInterface = new {interface_class}("{device_id}");
    const agent = createAgent(deviceInterface);
    
    try {{
        {"".join(steps_code)}
        
        console.log("\\n✅ 所有步骤执行完成!");
        process.exit(0);
        
    }} catch (error) {{
        console.error("\\n❌ 执行失败:", error.message);
        process.exit(1);
        
    }} finally {{
        await agent.destroy();
    }}
}}

main();
'''
    return script

@router.post("/run", response_model=ExecutionResponse)
async def run_case(
    request: ExecutionRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """执行用例"""
    # 获取用例
    result = await db.execute(
        select(TestCase).where(TestCase.id == request.case_id)
    )
    case = result.scalar_one_or_none()
    
    if not case:
        raise HTTPException(status_code=404, detail="用例不存在")
    
    # 获取 AI 配置
    ai_config = await get_active_ai_config(db)
    if not ai_config:
        raise HTTPException(status_code=400, detail="未配置 AI 模型，请先在设置中配置")
    
    # 创建执行记录
    execution = Execution(
        id=str(uuid.uuid4()),
        case_id=case.id,
        device_id=request.device_id,
        platform=case.platform,
        status="pending"
    )
    
    db.add(execution)
    await db.commit()
    await db.refresh(execution)
    
    # 初始化缓存
    execution_cache[execution.id] = {
        "status": "pending",
        "logs": [],
        "finished": False
    }
    
    # 后台执行
    background_tasks.add_task(
        run_execution,
        execution.id,
        case.yaml_content,
        request.device_id,
        case.platform,
        ai_config
    )
    
    return model_to_response(execution)

@router.get("/", response_model=ExecutionList)
async def list_executions(
    case_id: str = None,
    status: str = None,
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db)
):
    """获取执行列表"""
    query = select(Execution)
    
    if case_id:
        query = query.where(Execution.case_id == case_id)
    if status:
        query = query.where(Execution.status == status)
    
    query = query.order_by(Execution.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    executions = result.scalars().all()
    
    # 总数
    count_query = select(Execution)
    if case_id:
        count_query = count_query.where(Execution.case_id == case_id)
    if status:
        count_query = count_query.where(Execution.status == status)
    count_result = await db.execute(count_query)
    total = len(count_result.scalars().all())
    
    return ExecutionList(
        total=total,
        items=[model_to_response(e) for e in executions]
    )

@router.get("/{execution_id}", response_model=ExecutionResponse)
async def get_execution(execution_id: str, db: AsyncSession = Depends(get_db)):
    """获取执行详情"""
    result = await db.execute(
        select(Execution).where(Execution.id == execution_id)
    )
    execution = result.scalar_one_or_none()
    
    if not execution:
        raise HTTPException(status_code=404, detail="执行记录不存在")
    
    return model_to_response(execution)

@router.websocket("/{execution_id}/logs")
async def execution_logs_ws(websocket: WebSocket, execution_id: str):
    """实时日志 WebSocket"""
    await websocket.accept()
    
    last_log_count = 0
    
    try:
        while True:
            if execution_id in execution_cache:
                cache = execution_cache[execution_id]
                
                # 发送新日志
                current_logs = cache.get("logs", [])
                if len(current_logs) > last_log_count:
                    for log in current_logs[last_log_count:]:
                        await websocket.send_json({"type": "log", "data": log})
                    last_log_count = len(current_logs)
                
                # 发送状态
                await websocket.send_json({
                    "type": "status",
                    "data": cache.get("status", "unknown")
                })
                
                # 执行完成
                if cache.get("finished"):
                    await websocket.send_json({"type": "finished"})
                    break
            
            await asyncio.sleep(0.5)
    except:
        pass
    finally:
        await websocket.close()
