"""
Vitest Runner

执行编译后的 TypeScript 测试文件
"""
import asyncio
import json
import os
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

from apps.ui_automation.execution.models.enums import Platform, ExecutionStatus


class RunnerResult:
    """执行结果"""
    
    def __init__(self) -> None:
        self.success: bool = False
        self.status: ExecutionStatus = ExecutionStatus.PENDING
        self.started_at: datetime | None = None
        self.finished_at: datetime | None = None
        self.duration_ms: int = 0
        
        # 结果
        self.report_url: str | None = None
        self.report_data: dict[str, Any] | None = None
        self.error_message: str | None = None
        self.error_stack: str | None = None
        
        # 步骤结果
        self.steps_result: list[dict[str, Any]] = []
        self.total_steps: int = 0
        self.passed_steps: int = 0
        self.failed_steps: int = 0
        self.skipped_steps: int = 0
        
        # 输出
        self.stdout: str = ""
        self.stderr: str = ""


class VitestRunner:
    """
    Vitest 执行器
    
    负责执行编译后的 TypeScript 测试文件，并收集结果
    """
    
    def __init__(
        self,
        project_dir: str | None = None,
        node_path: str = "node",
        npm_path: str = "npm",
    ) -> None:
        """
        初始化执行器
        
        Args:
            project_dir: Midscene Executor 项目目录
            node_path: Node.js 可执行文件路径
            npm_path: npm 可执行文件路径
        """
        if project_dir:
            self._project_dir = Path(project_dir)
        else:
            # 默认目录
            backend_dir = Path(__file__).parent.parent.parent.parent.parent
            self._project_dir = backend_dir.parent / "midscene-executor"
        
        self._node_path = node_path
        self._npm_path = npm_path
        
        # 报告目录
        self._reports_dir = self._project_dir / "reports"
    
    async def run(
        self,
        test_file: str | None = None,
        test_content: str | None = None,  # 支持直接传入 TS 内容
        env_vars: dict[str, str] | None = None,
        device_id: str | None = None,
        platform: Platform = Platform.ANDROID,
        on_log: Callable[[str], None] | None = None,
    ) -> RunnerResult:
        """
        执行测试文件
        
        Args:
            test_file: 测试文件路径（相对于 tests 目录）
            env_vars: 环境变量
            device_id: 设备 ID
            platform: 目标平台
            on_log: 日志回调
            
        Returns:
            执行结果
        """
        result = RunnerResult()
        result.started_at = datetime.now()
        result.status = ExecutionStatus.RUNNING
        
        temp_file_created = False
        test_path = None
        
        try:
            # 构建环境变量
            env = os.environ.copy()
            if env_vars:
                env.update(env_vars)
            if device_id:
                env["DEVICE_ID"] = device_id
            
            # 确定测试文件路径
            if test_content:
                # 从内容创建临时文件
                import tempfile
                import uuid as uuid_module
                
                platform_dir = "android" if platform == Platform.ANDROID else "ios"
                temp_dir = self._project_dir / "tests" / platform_dir
                temp_dir.mkdir(parents=True, exist_ok=True)
                
                temp_filename = f"temp_{uuid_module.uuid4().hex[:8]}.test.ts"
                test_path = temp_dir / temp_filename
                test_path.write_text(test_content, encoding="utf-8")
                temp_file_created = True
                
                if on_log:
                    on_log(f"[Runner] Created temp file: {test_path}")
            elif test_file:
                test_path = self._project_dir / "tests" / test_file
                if not test_path.exists():
                    raise FileNotFoundError(f"Test file not found: {test_path}")
            else:
                raise ValueError("Either test_file or test_content must be provided")
            
            cmd = [
                self._npm_path,
                "run",
                "test",
                "--",
                str(test_path),
                "--reporter=verbose",
                "--reporter=json",
                f"--outputFile={self._reports_dir / 'results.json'}",
            ]
            
            if on_log:
                on_log(f"[Runner] Executing: {' '.join(cmd)}")
                on_log(f"[Runner] Working directory: {self._project_dir}")
            
            # 执行测试
            process = await asyncio.create_subprocess_exec(
                *cmd,
                cwd=str(self._project_dir),
                env=env,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            
            # 实时读取输出
            async def read_stream(stream, is_stderr=False):
                output = []
                while True:
                    line = await stream.readline()
                    if not line:
                        break
                    line_str = line.decode("utf-8", errors="replace")
                    output.append(line_str)
                    if on_log:
                        prefix = "[stderr]" if is_stderr else "[stdout]"
                        on_log(f"{prefix} {line_str.rstrip()}")
                return "".join(output)
            
            # 并行读取 stdout 和 stderr
            stdout_task = asyncio.create_task(read_stream(process.stdout, False))
            stderr_task = asyncio.create_task(read_stream(process.stderr, True))
            
            # 等待进程完成
            exit_code = await process.wait()
            
            result.stdout = await stdout_task
            result.stderr = await stderr_task
            
            # 解析结果
            result.finished_at = datetime.now()
            result.duration_ms = int(
                (result.finished_at - result.started_at).total_seconds() * 1000
            )
            
            if exit_code == 0:
                result.success = True
                result.status = ExecutionStatus.PASSED
            else:
                result.success = False
                result.status = ExecutionStatus.FAILED
                result.error_message = f"Test failed with exit code {exit_code}"
            
            # 读取 JSON 报告
            await self._parse_report(result)
            
            # 查找 Midscene 生成的 HTML 报告
            await self._find_html_report(result, test_file)
            
        except FileNotFoundError as e:
            result.status = ExecutionStatus.FAILED
            result.error_message = str(e)
            result.finished_at = datetime.now()
            
        except asyncio.TimeoutError:
            result.status = ExecutionStatus.TIMEOUT
            result.error_message = "Test execution timeout"
            result.finished_at = datetime.now()
            
        except Exception as e:
            result.status = ExecutionStatus.FAILED
            result.error_message = str(e)
            result.error_stack = str(e.__traceback__)
            result.finished_at = datetime.now()
        
        finally:
            # 清理临时文件
            if temp_file_created and test_path and test_path.exists():
                try:
                    test_path.unlink()
                    if on_log:
                        on_log(f"[Runner] Cleaned up temp file: {test_path}")
                except Exception as e:
                    if on_log:
                        on_log(f"[Runner] Warning: Failed to clean temp file: {e}")
        
        return result
    
    async def run_suite(
        self,
        test_files: list[str],
        env_vars: dict[str, str] | None = None,
        device_id: str | None = None,
        platform: Platform = Platform.ANDROID,
        on_log: Callable[[str], None] | None = None,
        parallel: bool = False,
    ) -> list[RunnerResult]:
        """
        执行测试套件
        
        Args:
            test_files: 测试文件列表
            env_vars: 环境变量
            device_id: 设备 ID
            platform: 目标平台
            on_log: 日志回调
            parallel: 是否并行执行
            
        Returns:
            执行结果列表
        """
        if parallel:
            # 并行执行（不推荐用于移动端测试）
            tasks = [
                self.run(f, env_vars, device_id, platform, on_log)
                for f in test_files
            ]
            return await asyncio.gather(*tasks)
        else:
            # 串行执行
            results = []
            for f in test_files:
                result = await self.run(f, env_vars, device_id, platform, on_log)
                results.append(result)
                
                # 如果失败，可以选择继续或停止
                if not result.success:
                    if on_log:
                        on_log(f"[Runner] Test {f} failed, continuing...")
            
            return results
    
    async def _parse_report(self, result: RunnerResult) -> None:
        """解析 Vitest JSON 报告"""
        report_file = self._reports_dir / "results.json"
        
        if not report_file.exists():
            return
        
        try:
            with open(report_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            result.report_data = data
            
            # 统计步骤结果
            test_results = data.get("testResults", [])
            for test_result in test_results:
                for assertion in test_result.get("assertionResults", []):
                    step = {
                        "stepId": assertion.get("ancestorTitles", [""])[0],
                        "stepName": assertion.get("title", ""),
                        "status": assertion.get("status", ""),
                        "durationMs": assertion.get("duration"),
                    }
                    
                    if assertion.get("failureMessages"):
                        step["error"] = "\n".join(assertion["failureMessages"])
                    
                    result.steps_result.append(step)
                    result.total_steps += 1
                    
                    if assertion.get("status") == "passed":
                        result.passed_steps += 1
                    elif assertion.get("status") == "failed":
                        result.failed_steps += 1
                    else:
                        result.skipped_steps += 1
                        
        except Exception as e:
            # 报告解析失败不影响整体结果
            if result.error_message:
                result.error_message += f"\nReport parsing failed: {e}"
    
    async def _find_html_report(self, result: RunnerResult, test_file: str) -> None:
        """查找 Midscene 生成的 HTML 报告"""
        # Midscene 默认将报告放在 midscene_run/report 目录
        report_dir = self._project_dir / "midscene_run" / "report"
        
        if not report_dir.exists():
            return
        
        # 查找最新的 HTML 报告
        html_files = list(report_dir.glob("*.html"))
        if html_files:
            # 按修改时间排序，取最新的
            latest = max(html_files, key=lambda f: f.stat().st_mtime)
            result.report_url = str(latest)
    
    async def check_environment(self) -> dict[str, Any]:
        """
        检查执行环境
        
        Returns:
            环境检查结果
        """
        checks = {
            "project_dir_exists": self._project_dir.exists(),
            "node_modules_exists": (self._project_dir / "node_modules").exists(),
            "package_json_exists": (self._project_dir / "package.json").exists(),
            "node_version": None,
            "npm_version": None,
        }
        
        try:
            # 检查 Node.js 版本
            node_result = subprocess.run(
                [self._node_path, "--version"],
                capture_output=True,
                text=True,
            )
            checks["node_version"] = node_result.stdout.strip()
            
            # 检查 npm 版本
            npm_result = subprocess.run(
                [self._npm_path, "--version"],
                capture_output=True,
                text=True,
            )
            checks["npm_version"] = npm_result.stdout.strip()
            
        except Exception as e:
            checks["error"] = str(e)
        
        return checks
    
    async def install_dependencies(self, on_log: Callable[[str], None] | None = None) -> bool:
        """
        安装项目依赖
        
        Returns:
            是否成功
        """
        try:
            if on_log:
                on_log("[Runner] Installing dependencies...")
            
            process = await asyncio.create_subprocess_exec(
                self._npm_path,
                "install",
                cwd=str(self._project_dir),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                if on_log:
                    on_log("[Runner] Dependencies installed successfully")
                return True
            else:
                if on_log:
                    on_log(f"[Runner] Failed to install dependencies: {stderr.decode()}")
                return False
                
        except Exception as e:
            if on_log:
                on_log(f"[Runner] Error installing dependencies: {e}")
            return False
