/**
 * Android 设备接口
 * 实现 Midscene AbstractInterface
 */
import { execSync } from 'child_process';
import { readFileSync } from 'fs';

export class AndroidInterface {
    constructor(deviceId) {
        this.deviceId = deviceId;
        this.interfaceType = 'android';
    }

    /**
     * 获取设备分辨率
     */
    async size() {
        const deviceArg = this.deviceId ? `-s ${this.deviceId}` : '';
        const output = execSync(`adb ${deviceArg} shell wm size`).toString();
        
        const match = output.match(/(\d+)x(\d+)/);
        if (match) {
            return {
                width: parseInt(match[1]),
                height: parseInt(match[2])
            };
        }
        
        return { width: 1080, height: 1920 };
    }

    /**
     * 截取屏幕并返回 base64
     */
    async screenshotBase64() {
        const deviceArg = this.deviceId ? `-s ${this.deviceId}` : '';
        const tempFile = '/tmp/midscene_android_screenshot.png';
        
        // 截图保存到临时文件
        execSync(`adb ${deviceArg} exec-out screencap -p > ${tempFile}`);
        
        // 读取文件并转换为 base64
        const imageBuffer = readFileSync(tempFile);
        const base64String = imageBuffer.toString('base64');
        
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
        const deviceArg = this.deviceId ? `-s ${this.deviceId}` : '';
        execSync(`adb ${deviceArg} shell input tap ${x} ${y}`);
    }

    /**
     * 滑动屏幕
     */
    async swipe(startX, startY, endX, endY, duration = 300) {
        const deviceArg = this.deviceId ? `-s ${this.deviceId}` : '';
        execSync(`adb ${deviceArg} shell input swipe ${startX} ${startY} ${endX} ${endY} ${duration}`);
    }

    /**
     * 输入文本
     */
    async input(text) {
        const deviceArg = this.deviceId ? `-s ${this.deviceId}` : '';
        // 转义特殊字符
        const escaped = text.replace(/ /g, '%s').replace(/'/g, "\\'");
        execSync(`adb ${deviceArg} shell input text '${escaped}'`);
    }

    /**
     * 返回键
     */
    async back() {
        const deviceArg = this.deviceId ? `-s ${this.deviceId}` : '';
        execSync(`adb ${deviceArg} shell input keyevent KEYCODE_BACK`);
    }

    /**
     * Home 键
     */
    async home() {
        const deviceArg = this.deviceId ? `-s ${this.deviceId}` : '';
        execSync(`adb ${deviceArg} shell input keyevent KEYCODE_HOME`);
    }

    /**
     * 启动应用
     */
    async launchApp(packageName, activityName) {
        const deviceArg = this.deviceId ? `-s ${this.deviceId}` : '';
        if (activityName) {
            execSync(`adb ${deviceArg} shell am start -n ${packageName}/${activityName}`);
        } else {
            execSync(`adb ${deviceArg} shell monkey -p ${packageName} -c android.intent.category.LAUNCHER 1`);
        }
    }

    /**
     * 清除应用数据
     */
    async clearAppData(packageName) {
        const deviceArg = this.deviceId ? `-s ${this.deviceId}` : '';
        execSync(`adb ${deviceArg} shell pm clear ${packageName}`);
    }

    /**
     * 获取当前应用包名
     */
    async getCurrentPackage() {
        const deviceArg = this.deviceId ? `-s ${this.deviceId}` : '';
        const output = execSync(`adb ${deviceArg} shell dumpsys window | grep mCurrentFocus`).toString();
        
        const match = output.match(/(\w+(\.\w+)+)/);
        return match ? match[1] : null;
    }
}

