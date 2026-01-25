/**
 * iOS 设备接口
 * 实现 Midscene AbstractInterface
 * 依赖：tidevice 或 WebDriverAgent
 */
import { execSync } from 'child_process';
import { readFileSync, writeFileSync, unlinkSync } from 'fs';
import { tmpdir } from 'os';
import { join } from 'path';

export class IOSInterface {
    constructor(deviceId) {
        this.deviceId = deviceId;
        this.interfaceType = 'ios';
        this.wdaPort = 8100;  // WebDriverAgent 端口
    }

    /**
     * 获取设备分辨率
     */
    async size() {
        try {
            // 通过 WebDriverAgent 获取屏幕尺寸
            const response = await fetch(`http://localhost:${this.wdaPort}/session/`);
            const data = await response.json();
            
            if (data.value?.capabilities?.deviceScreenSize) {
                const size = data.value.capabilities.deviceScreenSize;
                const [width, height] = size.split('x').map(Number);
                return { width, height };
            }
        } catch (e) {
            console.warn('通过 WDA 获取屏幕尺寸失败，使用默认值');
        }
        
        // 默认 iPhone 分辨率
        return { width: 390, height: 844 };
    }

    /**
     * 截取屏幕并返回 base64
     */
    async screenshotBase64() {
        const tempFile = join(tmpdir(), `midscene_ios_screenshot_${Date.now()}.png`);
        
        try {
            // 方式1：使用 tidevice 截图
            execSync(`tidevice -u ${this.deviceId} screenshot ${tempFile}`, { stdio: 'pipe' });
        } catch (e) {
            try {
                // 方式2：使用 WebDriverAgent 截图
                const response = await fetch(`http://localhost:${this.wdaPort}/screenshot`);
                const data = await response.json();
                
                if (data.value) {
                    const imageBuffer = Buffer.from(data.value, 'base64');
                    writeFileSync(tempFile, imageBuffer);
                } else {
                    throw new Error('WDA 截图失败');
                }
            } catch (e2) {
                // 方式3：使用 idevicescreenshot
                execSync(`idevicescreenshot -u ${this.deviceId} ${tempFile}`, { stdio: 'pipe' });
            }
        }
        
        // 读取文件并转换为 base64
        const imageBuffer = readFileSync(tempFile);
        const base64String = imageBuffer.toString('base64');
        
        // 清理临时文件
        try { unlinkSync(tempFile); } catch {}
        
        // 检查是否使用豆包模型
        const isDoubaoModel = process.env.MIDSCENE_MODEL_NAME?.includes('doubao');
        if (isDoubaoModel) {
            return `data:image/png;base64,${base64String}`;
        }
        
        return base64String;
    }

    /**
     * 点击屏幕
     */
    async tap(x, y) {
        try {
            // 使用 WebDriverAgent
            await this._wdaRequest('POST', '/wda/tap/0', {
                x: x,
                y: y
            });
        } catch (e) {
            // 降级到 tidevice
            execSync(`tidevice -u ${this.deviceId} tap ${x} ${y}`, { stdio: 'pipe' });
        }
    }

    /**
     * 滑动屏幕
     */
    async swipe(startX, startY, endX, endY, duration = 0.3) {
        try {
            // 使用 WebDriverAgent
            await this._wdaRequest('POST', '/wda/dragFromToForDuration', {
                fromX: startX,
                fromY: startY,
                toX: endX,
                toY: endY,
                duration: duration
            });
        } catch (e) {
            // 降级到 tidevice
            execSync(`tidevice -u ${this.deviceId} swipe ${startX} ${startY} ${endX} ${endY} ${duration}`, { stdio: 'pipe' });
        }
    }

    /**
     * 输入文本
     */
    async input(text) {
        try {
            // 使用 WebDriverAgent
            await this._wdaRequest('POST', '/wda/keys', {
                value: text.split('')
            });
        } catch (e) {
            // 降级：通过剪贴板粘贴
            console.warn('直接输入失败，请确保键盘已打开');
        }
    }

    /**
     * 返回（模拟左滑返回）
     */
    async back() {
        const size = await this.size();
        await this.swipe(10, size.height / 2, size.width * 0.8, size.height / 2, 0.3);
    }

    /**
     * Home 键
     */
    async home() {
        try {
            await this._wdaRequest('POST', '/wda/homescreen');
        } catch (e) {
            execSync(`tidevice -u ${this.deviceId} home`, { stdio: 'pipe' });
        }
    }

    /**
     * 启动应用
     */
    async launchApp(bundleId) {
        try {
            // 使用 tidevice 启动
            execSync(`tidevice -u ${this.deviceId} launch ${bundleId}`, { stdio: 'pipe' });
        } catch (e) {
            // 使用 WebDriverAgent
            await this._wdaRequest('POST', '/wda/apps/launch', {
                bundleId: bundleId
            });
        }
    }

    /**
     * 终止应用
     */
    async terminateApp(bundleId) {
        try {
            execSync(`tidevice -u ${this.deviceId} kill ${bundleId}`, { stdio: 'pipe' });
        } catch (e) {
            await this._wdaRequest('POST', '/wda/apps/terminate', {
                bundleId: bundleId
            });
        }
    }

    /**
     * 锁屏
     */
    async lock() {
        await this._wdaRequest('POST', '/wda/lock');
    }

    /**
     * 解锁
     */
    async unlock() {
        await this._wdaRequest('POST', '/wda/unlock');
    }

    /**
     * 发送 WDA 请求
     */
    async _wdaRequest(method, path, body = null) {
        const url = `http://localhost:${this.wdaPort}${path}`;
        const options = {
            method: method,
            headers: {
                'Content-Type': 'application/json'
            }
        };
        
        if (body) {
            options.body = JSON.stringify(body);
        }
        
        const response = await fetch(url, options);
        const data = await response.json();
        
        if (data.status !== 0 && response.status !== 200) {
            throw new Error(`WDA 请求失败: ${JSON.stringify(data)}`);
        }
        
        return data;
    }
}

