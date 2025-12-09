# 贡献指南

感谢您对 XRun 的关注！我们欢迎任何形式的贡献。

## 🌟 如何贡献

### 报告问题

如果您发现了bug或有功能建议：

1. 在 [Issues](https://github.com/wangxiaoqi-maker/XRun/issues) 中搜索是否已有相关问题
2. 如果没有，创建一个新的 Issue
3. 清楚地描述问题或建议，包括：
   - 问题的详细描述
   - 复现步骤（如果是bug）
   - 期望的行为
   - 实际的行为
   - 环境信息（操作系统、Python版本等）

### 提交代码

1. **Fork 项目**
   ```bash
   # Fork 后克隆到本地
   git clone https://github.com/YOUR_USERNAME/XRun.git
   cd XRun
   ```

2. **创建分支**
   ```bash
   git checkout -b feature/your-feature-name
   # 或
   git checkout -b bugfix/your-bugfix-name
   ```

3. **开发**
   - 编写代码
   - 添加测试
   - 确保代码风格一致
   - 更新文档

4. **提交**
   ```bash
   git add .
   git commit -m "feat: add your feature description"
   ```
   
   提交信息格式：
   - `feat:` 新功能
   - `fix:` 修复bug
   - `docs:` 文档更新
   - `style:` 代码格式调整
   - `refactor:` 重构
   - `test:` 测试相关
   - `chore:` 构建/工具相关

5. **推送并创建 Pull Request**
   ```bash
   git push origin feature/your-feature-name
   ```
   然后在 GitHub 上创建 Pull Request

## 📝 代码规范

### Python 代码

- 遵循 PEP 8 规范
- 使用 4 空格缩进
- 最大行长度 120 字符
- 使用类型注解

```python
def process_test_case(case_id: int, options: dict) -> dict:
    """处理测试用例
    
    Args:
        case_id: 测试用例ID
        options: 执行选项
        
    Returns:
        测试结果字典
    """
    pass
```

### JavaScript/TypeScript

- 使用 ESLint 和 Prettier
- 使用 2 空格缩进
- 优先使用函数式编程

## 🧪 测试

在提交 PR 前，请确保：

```bash
# 运行后端测试
python manage.py test

# 运行前端测试
cd frontend
npm test

# 代码格式检查
flake8 .
```

## 📚 文档

如果您的贡献涉及：
- 新功能：请更新相关文档
- API 变更：请更新 API 文档
- 配置变更：请更新配置说明

## 💬 交流

- 通过 Issue 讨论问题和建议
- 加入我们的讨论组（待建立）

## 🎯 开发优先级

当前重点开发方向：

1. **高优先级**
   - AI 核心引擎优化
   - UI 自动化功能完善
   - 性能优化

2. **中优先级**
   - 更多 AI 模型支持
   - 测试报告增强
   - 国际化支持

3. **低优先级**
   - 插件系统
   - 主题定制

## ⚠️ 注意事项

- 不要提交包含敏感信息的代码（API密钥、密码等）
- 确保您的代码不会破坏现有功能
- 大的功能变更请先创建 Issue 讨论
- 保持 PR 的粒度合理，一个 PR 只做一件事

## 📜 行为准则

- 尊重所有贡献者
- 建设性的反馈
- 包容不同的观点
- 专注于对项目最有利的方向

---

再次感谢您的贡献！每一个 Star ⭐️ 和 PR 都是对我们最大的支持！
