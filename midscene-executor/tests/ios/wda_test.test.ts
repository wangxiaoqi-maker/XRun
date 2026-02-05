// WDA 连接测试
import { describe, it, beforeAll, afterAll, expect } from 'vitest';
import { agentFromWebDriverAgent, IOSAgent } from '@midscene/ios';

describe('WDA 连接测试', () => {
  let agent: IOSAgent;
  const wdaHost = process.env.WDA_HOST || 'localhost';
  const wdaPort = Number(process.env.WDA_PORT) || 58001;
  
  console.log(`[测试] WDA_HOST=${wdaHost}, WDA_PORT=${wdaPort}`);
  
  beforeAll(async () => {
    console.log(`[测试] 正在连接 WDA: ${wdaHost}:${wdaPort}`);
    agent = await agentFromWebDriverAgent({
      wdaHost,
      wdaPort,
    });
    console.log('[测试] Agent 创建成功');
  }, 30000);

  afterAll(async () => {
    if (agent) {
      await agent.destroy();
      console.log('[测试] Agent 已销毁');
    }
  });

  it('应该能截图', async () => {
    console.log('[测试] 开始截图...');
    const screenshot = await agent.aiQuery('屏幕上有什么内容？');
    console.log('[测试] 截图成功，内容:', screenshot);
    expect(screenshot).toBeDefined();
  }, 60000);
});
