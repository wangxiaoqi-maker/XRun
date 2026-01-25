/**
 * Midscene 执行器入口
 */
import { createAgent } from '@midscene/core';
import { AndroidInterface } from './android_interface.js';
import { IOSInterface } from './ios_interface.js';
import 'dotenv/config';

const sleep = (ms) => new Promise(resolve => setTimeout(resolve, ms));

/**
 * 获取设备接口
 */
function getDeviceInterface(platform, deviceId) {
    if (platform === 'ios') {
        return new IOSInterface(deviceId);
    }
    return new AndroidInterface(deviceId);
}

/**
 * 执行测试用例
 */
async function executeTestCase(platform, deviceId, steps) {
    console.log('🚀 开始执行用例');
    console.log(`📱 平台: ${platform}`);
    console.log(`🔧 设备: ${deviceId}`);
    console.log(`📋 步骤数: ${steps.length}\n`);
    
    const deviceInterface = getDeviceInterface(platform, deviceId);
    const agent = createAgent(deviceInterface);
    
    let success = true;
    let errorMessage = null;
    
    try {
        for (let i = 0; i < steps.length; i++) {
            const step = steps[i];
            const stepNum = i + 1;
            const desc = step.description || step.type;
            
            console.log(`▶️  步骤 ${stepNum}/${steps.length}: ${desc}`);
            
            await executeStep(agent, deviceInterface, step);
            await sleep(300);
        }
        
        console.log('\n✅ 用例执行成功!');
        
    } catch (error) {
        success = false;
        errorMessage = error.message;
        console.error(`\n❌ 执行失败: ${error.message}`);
        
    } finally {
        await agent.destroy();
    }
    
    return { success, errorMessage };
}

/**
 * 执行单个步骤
 */
async function executeStep(agent, deviceInterface, step) {
    const type = step.type;
    const prompt = step.prompt || '';
    
    switch (type) {
        // AI 操作
        case 'aiTap':
            await agent.aiTap(prompt);
            break;
            
        case 'aiInput':
            await agent.aiInput(prompt, { value: step.text || '' });
            break;
            
        case 'aiSwipe':
            await agent.aiSwipe(prompt, step.direction || 'up');
            break;
            
        case 'aiAssert':
            await agent.aiAssert(prompt);
            break;
            
        case 'aiWait':
            await agent.aiWaitFor(prompt, { timeout: step.timeout || 10000 });
            break;
            
        case 'aiQuery':
            const result = await agent.aiQuery(prompt);
            console.log('   查询结果:', JSON.stringify(result));
            break;
        
        // 基础操作
        case 'tap':
            await deviceInterface.tap(step.x, step.y);
            break;
            
        case 'swipe':
            await deviceInterface.swipe(
                step.startX, step.startY,
                step.endX, step.endY,
                step.duration || 300
            );
            break;
            
        case 'input':
            await deviceInterface.input(step.text || '');
            break;
            
        case 'back':
            await deviceInterface.back();
            break;
            
        case 'home':
            await deviceInterface.home();
            break;
            
        case 'launch':
            if (step.bundleId) {
                // iOS
                await deviceInterface.launchApp(step.bundleId);
            } else {
                // Android
                await deviceInterface.launchApp(step.package, step.activity);
            }
            break;
            
        case 'sleep':
            await sleep(step.duration || 1000);
            break;
            
        case 'screenshot':
            await agent.recordToReport(step.description || '截图');
            break;
            
        default:
            console.warn(`   ⚠️ 未知步骤类型: ${type}`);
    }
}

// 导出
export {
    executeTestCase,
    getDeviceInterface,
    AndroidInterface,
    IOSInterface
};

