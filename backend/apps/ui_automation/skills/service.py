"""Skill 业务逻辑 - 搜索、抓取、安装、prompt 注入"""
import re
import logging
from typing import List, Optional, Dict, Any, Tuple

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from .models import Skill
from .repository import SkillRepository

logger = logging.getLogger(__name__)

SKILLS_SH_SEARCH_URL = "https://skills.sh/api/search"
SKILL_MD_PATHS = [
    "skills/{name}/SKILL.md",
    ".claude/skills/{name}/SKILL.md",
    ".agents/skills/{name}/SKILL.md",
    "{name}/SKILL.md",
]

DEFAULT_BRANCH = "main"

SCRIPT_EXT_MAP = {
    ".sh": "shell", ".bash": "shell",
    ".py": "python",
    ".js": "javascript", ".mjs": "javascript",
    ".ts": "typescript",
    ".yml": "yaml", ".yaml": "yaml",
    ".json": "json",
}


class SkillService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = SkillRepository(db)

    # ---------- 搜索 ----------

    async def search_skills_sh(self, q: str, limit: int = 10) -> Dict[str, Any]:
        """代理 skills.sh 搜索 API"""
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.get(
                    SKILLS_SH_SEARCH_URL,
                    params={"q": q, "limit": limit},
                )
                resp.raise_for_status()
                return resp.json()
        except Exception as e:
            logger.error(f"skills.sh search failed: {e}")
            return {"skills": [], "count": 0, "error": str(e)}

    # ---------- 抓取 SKILL.md + 伴随脚本 ----------

    async def _locate_skill_md(
        self, owner: str, repo: str, skill_name: str, branch: str = DEFAULT_BRANCH,
    ) -> Tuple[str, str]:
        """定位 SKILL.md，返回 (content, dir_path)"""
        async with httpx.AsyncClient(timeout=15.0) as client:
            for path_tpl in SKILL_MD_PATHS:
                path = path_tpl.format(name=skill_name)
                url = f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{path}"
                try:
                    resp = await client.get(url)
                    if resp.status_code == 200:
                        dir_path = "/".join(path.split("/")[:-1])
                        return resp.text, dir_path
                except Exception as e:
                    logger.debug(f"Failed to fetch {url}: {e}")
        raise ValueError(f"SKILL.md not found in {owner}/{repo} for skill {skill_name}")

    async def fetch_skill_md_from_github(
        self, owner: str, repo: str, skill_name: str, branch: str = DEFAULT_BRANCH,
    ) -> str:
        content, _ = await self._locate_skill_md(owner, repo, skill_name, branch)
        return content

    async def _fetch_companion_files(
        self, owner: str, repo: str, branch: str, dir_path: str,
    ) -> List[Dict[str, str]]:
        """从 SKILL.md 同级目录抓取脚本文件"""
        api_url = f"https://api.github.com/repos/{owner}/{repo}/contents/{dir_path}?ref={branch}"
        files: List[Dict[str, str]] = []
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.get(api_url)
                if resp.status_code != 200:
                    return files
                for item in resp.json():
                    if item.get("type") != "file":
                        continue
                    name = item["name"]
                    if name.upper() == "SKILL.MD":
                        continue
                    ext = self._file_extension(name)
                    lang = SCRIPT_EXT_MAP.get(ext)
                    if not lang:
                        continue
                    dl_url = item.get("download_url")
                    if not dl_url:
                        continue
                    content_resp = await client.get(dl_url)
                    if content_resp.status_code == 200:
                        files.append({
                            "filename": name,
                            "language": lang,
                            "content": content_resp.text,
                        })
        except Exception as e:
            logger.debug(f"Failed to fetch companion files from {dir_path}: {e}")
        return files

    async def _fetch_skill_bundle(
        self, owner: str, repo: str, skill_name: str, branch: str = DEFAULT_BRANCH,
    ) -> Tuple[str, List[Dict[str, str]]]:
        """抓取 SKILL.md + 同目录脚本，返回 (content, files)"""
        content, dir_path = await self._locate_skill_md(owner, repo, skill_name, branch)
        files = await self._fetch_companion_files(owner, repo, branch, dir_path)
        return content, files

    async def fetch_from_raw_url(self, url: str) -> str:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            return resp.text

    @staticmethod
    def _file_extension(filename: str) -> str:
        return ("." + filename.rsplit(".", 1)[-1].lower()) if "." in filename else ""

    # ---------- 解析元信息 ----------

    def _parse_metadata(self, content: str) -> Dict[str, str]:
        """从 SKILL.md 内容解析 name、description"""
        name = ""
        description = ""
        lines = content.split("\n")
        for i, line in enumerate(lines):
            if line.startswith("# "):
                name = line[2:].strip()
                break
        for i, line in enumerate(lines):
            if re.match(r"^##\s+(1\.\s+)?目标", line):
                desc_lines = []
                for j in range(i + 1, min(i + 10, len(lines))):
                    if lines[j].strip().startswith("#"):
                        break
                    desc_lines.append(lines[j].strip())
                description = "\n".join(desc_lines).strip()[:500]
                break
        if not description and name:
            description = name
        return {"name": name or "未命名", "description": description or ""}

    def _slug_to_key(self, slug: str) -> str:
        """将 skills.sh id 转为 key"""
        return slug.replace("/", "_").replace(" ", "-").lower()

    @staticmethod
    def _detect_category(content: str, name: str = "", description: str = "") -> str:
        """根据 Skill 内容自动检测分类，未匹配则返回 general"""
        text = f"{name} {description} {content[:2000]}".lower()
        case_kws = ["测试用例", "test case", "testcase", "用例生成", "用例编写", "case generat"]
        method_kws = ["测试方法", "测试点", "test method", "测试设计", "test design",
                      "等价类", "边界值", "场景法", "错误推测", "判定表", "状态迁移"]
        if any(kw in text for kw in case_kws):
            return "tcg_case"
        if any(kw in text for kw in method_kws):
            return "tcg_method"
        return "general"

    # ---------- 安装 ----------

    async def install_from_skills_sh(
        self, source: str, skill_name: str
    ) -> Skill:
        """从 skills.sh 安装（source 格式 owner/repo）"""
        parts = source.split("/")
        if len(parts) < 2:
            raise ValueError("source 格式应为 owner/repo")
        owner, repo = parts[0], parts[1]
        content, files = await self._fetch_skill_bundle(owner, repo, skill_name)
        meta = self._parse_metadata(content)
        key = self._slug_to_key(f"{source}_{skill_name}")
        if await self.repo.get_by_key(key):
            raise ValueError(f"Skill {key} 已存在，请先删除或使用更新")
        detected_cat = self._detect_category(content, meta["name"], meta["description"])
        return await self.repo.create(
            key=key,
            name=meta["name"] or skill_name,
            description=meta["description"],
            icon="⚙",
            category=detected_cat,
            source_type="skills_sh",
            source_url=f"https://skills.sh/{source}/{skill_name}",
            source_repo=source,
            raw_content=content,
            files=files,
            is_builtin=False,
            is_enabled=True,
        )

    async def install_from_url(self, url: str) -> Skill:
        """从 URL 下载并安装（支持 skills.sh、GitHub、raw URL）"""
        url = url.strip()
        if "skills.sh" in url:
            parts = url.rstrip("/").split("/")
            if len(parts) >= 3:
                skill_name = parts[-1]
                source = "/".join(parts[-3:-1])
                return await self.install_from_skills_sh(source, skill_name)
        if "raw.githubusercontent.com" in url:
            content = await self.fetch_from_raw_url(url)
            meta = self._parse_metadata(content)
            key = self._slug_to_key(meta["name"] or "imported")
            if await self.repo.get_by_key(key):
                key = f"{key}_{hash(url) % 10000}"
            detected_cat = self._detect_category(content, meta["name"], meta["description"])
            return await self.repo.create(
                key=key,
                name=meta["name"] or "导入的 Skill",
                description=meta["description"],
                icon="⚙",
                category=detected_cat,
                source_type="github",
                source_url=url,
                source_repo="",
                raw_content=content,
                is_builtin=False,
                is_enabled=True,
            )
        if "github.com" in url:
            m = re.match(r"https?://github\.com/([^/]+)/([^/]+)", url)
            if m:
                owner, repo = m.group(1), m.group(2).replace(".git", "")
                skill_name = "skill"
                if "/tree/" in url or "/blob/" in url:
                    parts = url.split("/")
                    for i, p in enumerate(parts):
                        if p in ("tree", "blob") and i + 1 < len(parts):
                            skill_name = parts[i - 1] if i > 0 else "skill"
                            break
                content, files = await self._fetch_skill_bundle(owner, repo, skill_name)
                meta = self._parse_metadata(content)
                key = self._slug_to_key(f"{owner}_{repo}_{skill_name}")
                detected_cat = self._detect_category(content, meta["name"], meta["description"])
                return await self.repo.create(
                    key=key,
                    name=meta["name"] or skill_name,
                    description=meta["description"],
                    icon="⚙",
                    category=detected_cat,
                    source_type="github",
                    source_url=url,
                    source_repo=f"{owner}/{repo}",
                    raw_content=content,
                    files=files,
                    is_builtin=False,
                    is_enabled=True,
                )
        raise ValueError(f"不支持的 URL 格式: {url}")

    async def create_manual(
        self, key: str, name: str, content: str,
        description: str = "", category: str = "",
        files: list | None = None,
    ) -> Skill:
        """手动创建 Skill"""
        if await self.repo.get_by_key(key):
            raise ValueError(f"Skill key {key} 已存在")
        if not content.strip():
            raise ValueError("content 不能为空")
        meta = self._parse_metadata(content) if not name else {}
        final_desc = description or meta.get("description", "")
        final_cat = category or self._detect_category(content, name, final_desc)
        return await self.repo.create(
            key=key,
            name=name or meta.get("name", "未命名"),
            description=final_desc,
            icon="⚙",
            category=final_cat,
            source_type="manual",
            source_url="",
            source_repo="",
            raw_content=content,
            files=files or [],
            is_builtin=False,
            is_enabled=True,
        )

    async def refresh(self, skill_id: str) -> Optional[Skill]:
        """从原始 URL 重新拉取（含伴随脚本）"""
        skill = await self.repo.get_by_id(skill_id)
        if not skill or not skill.source_url:
            return None
        files: List[Dict[str, str]] = []
        if "raw.githubusercontent.com" in skill.source_url:
            content = await self.fetch_from_raw_url(skill.source_url)
        elif skill.source_repo:
            repo_parts = skill.source_repo.split("/")
            if len(repo_parts) < 2:
                return None
            owner, repo = repo_parts[0], repo_parts[1]
            url_parts = skill.source_url.rstrip("/").split("/")
            skill_name = url_parts[-1] if url_parts else ""
            content, files = await self._fetch_skill_bundle(owner, repo, skill_name)
        else:
            return None
        meta = self._parse_metadata(content)
        update_kwargs: Dict[str, Any] = {
            "raw_content": content,
            "name": meta.get("name") or skill.name,
            "description": meta.get("description") or skill.description,
        }
        if files:
            update_kwargs["files"] = files
        await self.repo.update(skill_id, **update_kwargs)
        return await self.repo.get_by_id(skill_id)

    # ---------- Prompt 注入 Helper ----------

    @staticmethod
    def build_skill_prompt_block(skills: List[Skill], max_chars: int = 8000) -> str:
        """将多个 Skill 的内容拼接为可注入 prompt 的文本块"""
        if not skills:
            return ""
        blocks = []
        for skill in skills:
            content = skill.raw_content or ""
            if len(content) > max_chars:
                content = content[:max_chars] + "\n\n[内容过长，已截断...]"
            blocks.append(f"## 参考方法论：{skill.name}\n{content}")
        return "\n\n".join(blocks)
