"""
LLM 客户端使用示例
演示如何使用重构后的 base_llm 模块
"""
from core.llms.base_llm import (
    create_model_client,
    get_model_client,
    register_model,
    list_available_models,
)


def example_basic_usage():
    """示例1: 基础使用"""
    print("=" * 60)
    print("示例1: 基础使用")
    print("=" * 60)
    
    # 使用默认配置创建客户端
    deepseek_client = create_model_client("deepseek")
    print(f"✅ 创建 DeepSeek 客户端: {deepseek_client}")
    
    # 使用 QwenVL（带视觉能力）
    qwenvl_client = create_model_client("qwenvl")
    print(f"✅ 创建 QwenVL 客户端: {qwenvl_client}")
    
    # 使用 OpenAI
    openai_client = create_model_client("openai")
    print(f"✅ 创建 OpenAI 客户端: {openai_client}")
    print()


def example_custom_model():
    """示例2: 自定义模型名称"""
    print("=" * 60)
    print("示例2: 自定义模型名称")
    print("=" * 60)
    
    # 使用 OpenAI 的不同模型
    gpt4_turbo = create_model_client("openai", model_name="gpt-4-turbo")
    print(f"✅ 使用自定义模型: {gpt4_turbo}")
    
    gpt35 = create_model_client("openai", model_name="gpt-3.5-turbo")
    print(f"✅ 使用自定义模型: {gpt35}")
    print()


def example_direct_credentials():
    """示例3: 直接传入凭证"""
    print("=" * 60)
    print("示例3: 直接传入凭证（不依赖环境变量）")
    print("=" * 60)
    
    # 直接传入 API Key 和 Base URL
    client = create_model_client(
        "deepseek",
        api_key="sk-your-api-key-here",
        base_url="https://custom-endpoint.com/v1"
    )
    print(f"✅ 使用自定义凭证创建客户端: {client}")
    print()


def example_register_new_model():
    """示例4: 注册新的模型"""
    print("=" * 60)
    print("示例4: 注册自定义模型")
    print("=" * 60)
    
    # 注册一个新的模型（例如：Claude）
    register_model(
        name="claude",
        model="claude-3-opus-20240229",
        api_key_attr="CLAUDE_API_KEY",
        base_url_attr="CLAUDE_BASE_URL",
        default_base_url="https://api.anthropic.com/v1",
        vision=True,
        function_calling=True,
    )
    print("✅ 成功注册 Claude 模型配置")
    
    # 使用新注册的模型
    claude_client = create_model_client("claude")
    print(f"✅ 创建 Claude 客户端: {claude_client}")
    print()


def example_list_models():
    """示例5: 列出所有可用模型"""
    print("=" * 60)
    print("示例5: 列出所有可用的模型类型")
    print("=" * 60)
    
    models = list_available_models()
    print(f"可用的模型类型 ({len(models)} 个):")
    for model in models:
        print(f"  • {model}")
    print()


def example_backward_compatible():
    """示例6: 向后兼容的用法"""
    print("=" * 60)
    print("示例6: 向后兼容（旧代码仍然可以工作）")
    print("=" * 60)
    
    # 使用旧的便捷方法
    client = get_model_client("deepseek")
    print(f"✅ 使用 get_model_client: {client}")
    
    # 也可以使用旧的专用方法
    from core.llms.base_llm import get_deepseek_model_client, get_qwenvl_model_client
    
    deepseek = get_deepseek_model_client()
    print(f"✅ 使用 get_deepseek_model_client: {deepseek}")
    
    qwenvl = get_qwenvl_model_client()
    print(f"✅ 使用 get_qwenvl_model_client: {qwenvl}")
    print()


def example_plugin_usage():
    """示例7: 在插件中使用"""
    print("=" * 60)
    print("示例7: 在插件中使用不同的模型")
    print("=" * 60)
    
    # UI 自动化插件：使用 QwenVL（需要视觉能力）
    ui_model = create_model_client("qwenvl")
    print(f"🎨 UI 自动化插件使用: QwenVL (vision=True)")
    
    # 接口自动化插件：使用 DeepSeek（不需要视觉）
    api_model = create_model_client("deepseek")
    print(f"🔌 接口自动化插件使用: DeepSeek (vision=False)")
    
    # 用例生成插件：使用 OpenAI GPT-4
    testcase_model = create_model_client("openai", model_name="gpt-4")
    print(f"📝 用例生成插件使用: GPT-4")
    print()


def example_error_handling():
    """示例8: 错误处理"""
    print("=" * 60)
    print("示例8: 错误处理")
    print("=" * 60)
    
    # 尝试使用不存在的模型
    try:
        client = create_model_client("non_existent_model")
    except ValueError as e:
        print(f"❌ 预期的错误: {e}")
    
    # 尝试在未配置 API Key 的情况下创建客户端
    try:
        # 假设环境变量中没有 FAKE_API_KEY
        register_model(
            name="fake_model",
            model="fake-model-v1",
            api_key_attr="FAKE_API_KEY",
            base_url_attr="FAKE_BASE_URL",
            default_base_url="https://fake.com/v1",
        )
        client = create_model_client("fake_model")
    except ValueError as e:
        print(f"❌ 预期的错误: {e}")
    print()


def main():
    """运行所有示例"""
    print("\n🚀 LLM 客户端使用示例\n")
    
    try:
        example_basic_usage()
        example_custom_model()
        example_direct_credentials()
        example_register_new_model()
        example_list_models()
        example_backward_compatible()
        example_plugin_usage()
        example_error_handling()
        
        print("=" * 60)
        print("✅ 所有示例运行完成！")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ 示例运行出错: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

