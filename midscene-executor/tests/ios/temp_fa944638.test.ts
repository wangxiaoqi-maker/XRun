// 自动生成 - 请勿手动修改
// 用例: 转账
// 平台: iOS
// 生成时间: 2026-02-05T17:15:15.316281

import { sleep } from '@midscene/core/utils';
import { beforeAll, afterAll, describe, it, vi, expect } from 'vitest';
import {
  IOSAgent,
  IOSDevice,
  agentFromWebDriverAgent,
  checkIOSEnvironment,
} from '@midscene/ios';

// 配置全局超时
vi.setConfig({
  testTimeout: 240000,
  hookTimeout: 240000,
});

describe('转账', () => {
  let agent: IOSAgent | null = null;
  let device: IOSDevice | null = null;

  // ========== 参数化变量（从环境变量读取）==========

  beforeAll(async () => {
    // iOS 环境检查
    const envCheck = await checkIOSEnvironment();
    if (!envCheck.available) {
      console.warn(`iOS environment check failed: ${envCheck.error}`);
      return;
    }

    // WDA 连接配置
    const wdaHost = process.env.WDA_HOST || 'localhost';
    const wdaPort = Number(process.env.WDA_PORT) || 63612;

    // 创建设备实例
    device = new IOSDevice({
      wdaHost,
      wdaPort,
      autoDismissKeyboard: true,
    });

    // 连接设备
    await device.connect();

    // 创建 Agent
    agent = new IOSAgent(device, {
      // AI 上下文
      aiActionContext: process.env.AI_CONTEXT || '',
      
      // 报告配置
      generateReport: true,
      
      // 操作后等待
      waitAfterAction: 300,
      
      // 规划限制
      replanningCycleLimit: 20,
      
      
      // 模型配置
      modelConfig: {
        MIDSCENE_MODEL_NAME: process.env.MIDSCENE_MODEL_NAME || 'claude-opus-4-5-thinkin',
        MIDSCENE_MODEL_BASE_URL: process.env.MIDSCENE_MODEL_BASE_URL || 'http://127.0.0.1:8045/v1',
        MIDSCENE_MODEL_API_KEY: process.env.MIDSCENE_MODEL_API_KEY || '',
        MIDSCENE_MODEL_FAMILY: 'gemini',
      },
    });

  }, 240000);

  afterAll(async () => {
    // 清理资源
    if (device) {
      await device.destroy();
    }
  });

  // ========== 测试执行 ==========
  it('转账', async () => {
    if (!agent) {
      console.warn('Agent not initialized, skipping test');
      return;
    }

    // Step 1: 启动 (id: step_step_step_step_step_step_1770278333135)
    console.log("[Step 1] 启动");
    await agent.launch('com.esurfingpay.bestpay');
    await sleep(2000);

    // Step 2: 点击 (id: step_1770282885065)
    console.log("[Step 2] 点击");
    await agent.aiTap('我的');

    // Step 3: 点击 (id: step_1770282888862)
    console.log("[Step 3] 点击");
    await agent.aiTap('余额');

    // Step 4: 点击 (id: step_1770282894093)
    console.log("[Step 4] 点击");
    await agent.aiTap('继续');
  }, 720000);
});