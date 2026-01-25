/*
 *   sonic-agent  Agent of Sonic Cloud Real Machine Platform.
 *   Copyright (C) 2022 SonicCloudOrg
 *
 *   This program is free software: you can redistribute it and/or modify
 *   it under the terms of the GNU Affero General Public License as published
 *   by the Free Software Foundation, either version 3 of the License, or
 *   (at your option) any later version.
 *
 *   This program is distributed in the hope that it will be useful,
 *   but WITHOUT ANY WARRANTY; without even the implied warranty of
 *   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 *   GNU Affero General Public License for more details.
 *
 *   You should have received a copy of the GNU Affero General Public License
 *   along with this program.  If not, see <https://www.gnu.org/licenses/>.
 */
package org.cloud.sonic.agent.tests.android.scrcpy;

import com.alibaba.fastjson.JSONObject;
import com.android.ddmlib.IDevice;
import com.android.ddmlib.IShellOutputReceiver;
import jakarta.websocket.Session;
import org.cloud.sonic.agent.tests.android.AndroidTestTaskBootThread;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.File;
import java.util.concurrent.Semaphore;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicBoolean;

import static org.cloud.sonic.agent.tools.BytesTool.sendText;

/**
 * 启动scrcpy等服务的线程
 */
public class ScrcpyLocalThread extends Thread {

    private final Logger log = LoggerFactory.getLogger(ScrcpyLocalThread.class);

    public final static String ANDROID_START_MINICAP_SERVER_PRE = "android-scrcpy-start-scrcpy-server-task-%s-%s-%s";

    private IDevice iDevice;

    private int finalC;

    private Session session;

    private String udId;

    private AndroidTestTaskBootThread androidTestTaskBootThread;

    private Semaphore isFinish = new Semaphore(0);

    public ScrcpyLocalThread(IDevice iDevice, int finalC, Session session, AndroidTestTaskBootThread androidTestTaskBootThread) {
        this.iDevice = iDevice;
        this.finalC = finalC;
        this.session = session;
        this.udId = iDevice.getSerialNumber();
        this.androidTestTaskBootThread = androidTestTaskBootThread;

        this.setDaemon(true);
        this.setName(androidTestTaskBootThread.formatThreadName(ANDROID_START_MINICAP_SERVER_PRE));
    }

    public IDevice getiDevice() {
        return iDevice;
    }

    public int getFinalC() {
        return finalC;
    }

    public Session getSession() {
        return session;
    }

    public String getUdId() {
        return udId;
    }

    public AndroidTestTaskBootThread getAndroidTestTaskBootThread() {
        return androidTestTaskBootThread;
    }

    public Semaphore getIsFinish() {
        return isFinish;
    }

    @Override
    public void run() {
        File scrcpyServerFile = new File("plugins/sonic-android-scrcpy.jar");
        try {
            iDevice.pushFile(scrcpyServerFile.getAbsolutePath(), "/data/local/tmp/sonic-android-scrcpy.jar");
        } catch (Exception e) {
            e.printStackTrace();
        }
        AtomicBoolean isRetry = new AtomicBoolean(false);
        try {
            // 获取 Android SDK 版本，决定使用哪个 scrcpy 参数格式
            String sdkVersionStr = iDevice.getProperty("ro.build.version.sdk");
            int sdkVersion = 0;
            try {
                sdkVersion = Integer.parseInt(sdkVersionStr);
            } catch (Exception e) {
                log.warn("Failed to parse SDK version: {}", sdkVersionStr);
            }
            
            // scrcpy 3.1 参数格式（兼容 Android 15+，SDK >= 35）
            // 也向下兼容旧版本 Android
            String scrcpyCommand = "CLASSPATH=/data/local/tmp/sonic-android-scrcpy.jar app_process / com.genymobile.scrcpy.Server 3.1 tunnel_forward=true video=true audio=false control=false max_size=800 max_fps=60";
            
            log.info("Starting scrcpy with SDK version: {}, command: {}", sdkVersion, scrcpyCommand);
            
            iDevice.executeShellCommand(scrcpyCommand,
                    new IShellOutputReceiver() {
                        @Override
                        public void addOutput(byte[] bytes, int i, int i1) {
                            String res = new String(bytes, i, i1);
                            log.info(res);
                            if (res.contains("Device")) {
                                isFinish.release();
                                isRetry.set(true);
                            } else if (!isRetry.get() && res.contains("ERROR")) {
                                log.info("scrcpy服务启动失败！");
                                JSONObject support = new JSONObject();
                                support.put("msg", "support");
                                support.put("text", "scrcpy服务启动失败！");
                                sendText(session, support.toJSONString());
                            }
                        }

                        @Override
                        public void flush() {
                        }

                        @Override
                        public boolean isCancelled() {
                            return false;
                        }
                    }, 0, TimeUnit.MILLISECONDS);
        } catch (Exception e) {
            log.info("{} scrcpy service stopped.", iDevice.getSerialNumber());
            log.error(e.getMessage());
        }
    }

}