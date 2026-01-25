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
import jakarta.websocket.Session;
import org.cloud.sonic.agent.bridge.android.AndroidDeviceBridgeTool;
import org.cloud.sonic.agent.common.maps.ScreenMap;
import org.cloud.sonic.agent.tests.android.AndroidTestTaskBootThread;
import org.cloud.sonic.agent.tools.BytesTool;
import org.cloud.sonic.agent.tools.PortTool;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.IOException;
import java.io.InputStream;
import java.net.InetSocketAddress;
import java.net.Socket;
import java.util.concurrent.BlockingQueue;

/**
 * scrcpy socket线程
 * 通过端口转发，将设备视频流转发到此Socket
 */
public class ScrcpyInputSocketThread extends Thread {

    private final Logger log = LoggerFactory.getLogger(ScrcpyInputSocketThread.class);

    public final static String ANDROID_INPUT_SOCKET_PRE = "android-scrcpy-input-socket-task-%s-%s-%s";

    private IDevice iDevice;

    private BlockingQueue<byte[]> dataQueue;

    private ScrcpyLocalThread scrcpyLocalThread;

    private AndroidTestTaskBootThread androidTestTaskBootThread;

    private Session session;

    public ScrcpyInputSocketThread(IDevice iDevice, BlockingQueue<byte[]> dataQueue, ScrcpyLocalThread scrcpyLocalThread, Session session) {
        this.iDevice = iDevice;
        this.dataQueue = dataQueue;
        this.scrcpyLocalThread = scrcpyLocalThread;
        this.session = session;
        this.androidTestTaskBootThread = scrcpyLocalThread.getAndroidTestTaskBootThread();
        this.setDaemon(false);
        this.setName(androidTestTaskBootThread.formatThreadName(ANDROID_INPUT_SOCKET_PRE));
    }

    public IDevice getiDevice() {
        return iDevice;
    }

    public BlockingQueue<byte[]> getDataQueue() {
        return dataQueue;
    }

    public ScrcpyLocalThread getScrcpyLocalThread() {
        return scrcpyLocalThread;
    }

    public AndroidTestTaskBootThread getAndroidTestTaskBootThread() {
        return androidTestTaskBootThread;
    }

    public Session getSession() {
        return session;
    }

    private static final int BUFFER_SIZE = 1024 * 1024 * 10;
    private static final int READ_BUFFER_SIZE = 1024 * 64;
    
    // scrcpy 3.1 协议常量
    private static final int CODEC_ID_H264 = 0x68323634; // "h264" in big-endian
    private static final int CODEC_META_SIZE = 12; // codec_id(4) + width(4) + height(4)
    private static final int FRAME_HEADER_SIZE = 12; // pts(8) + size(4)

    @Override
    public void run() {
        int scrcpyPort = PortTool.getPort();
        AndroidDeviceBridgeTool.forward(iDevice, scrcpyPort, "scrcpy");
        Socket videoSocket = new Socket();
        InputStream inputStream = null;
        try {
            videoSocket.connect(new InetSocketAddress("localhost", scrcpyPort));
            inputStream = videoSocket.getInputStream();
            
            if (!videoSocket.isConnected()) {
                log.error("Failed to connect to scrcpy socket");
                return;
            }
            
            // ==== scrcpy 3.1 协议处理 ====
            
            // 1. 读取 dummy byte（tunnel_forward 模式下）
            byte[] dummyByte = new byte[1];
            int read = inputStream.read(dummyByte);
            if (read != 1) {
                log.error("Failed to read dummy byte from scrcpy");
                return;
            }
            log.info("scrcpy dummy byte received: {}", dummyByte[0] & 0xFF);
            
            // 2. 读取 device metadata（设备名称，固定 64 字节）
            // scrcpy 3.1 发送固定 64 字节，null-terminated UTF-8
            byte[] deviceNameBytes = new byte[64];
            int totalRead = 0;
            while (totalRead < 64) {
                read = inputStream.read(deviceNameBytes, totalRead, 64 - totalRead);
                if (read <= 0) {
                    log.error("Failed to read device name");
                    return;
                }
                totalRead += read;
            }
            // 找到 null 终止符
            int nameLen = 0;
            for (int i = 0; i < 64; i++) {
                if (deviceNameBytes[i] == 0) {
                    nameLen = i;
                    break;
                }
            }
            if (nameLen == 0) nameLen = 64;
            String deviceName = new String(deviceNameBytes, 0, nameLen, "UTF-8");
            log.info("scrcpy device name: {}", deviceName);

            
            // 3. 读取 codec metadata (12 bytes)
            byte[] codecMeta = new byte[CODEC_META_SIZE];
            totalRead = 0;
            while (totalRead < CODEC_META_SIZE) {
                read = inputStream.read(codecMeta, totalRead, CODEC_META_SIZE - totalRead);
                if (read <= 0) {
                    log.error("Failed to read codec metadata");
                    return;
                }
                totalRead += read;
            }
            
            // 解析 codec metadata (big-endian)
            int codecId = ((codecMeta[0] & 0xFF) << 24) | ((codecMeta[1] & 0xFF) << 16) | 
                         ((codecMeta[2] & 0xFF) << 8) | (codecMeta[3] & 0xFF);
            int videoWidth = ((codecMeta[4] & 0xFF) << 24) | ((codecMeta[5] & 0xFF) << 16) | 
                            ((codecMeta[6] & 0xFF) << 8) | (codecMeta[7] & 0xFF);
            int videoHeight = ((codecMeta[8] & 0xFF) << 24) | ((codecMeta[9] & 0xFF) << 16) | 
                             ((codecMeta[10] & 0xFF) << 8) | (codecMeta[11] & 0xFF);
            
            log.info("scrcpy codec: 0x{}, size: {}x{}", Integer.toHexString(codecId), videoWidth, videoHeight);
            
            // 发送尺寸信息到前端
            JSONObject size = new JSONObject();
            size.put("msg", "size");
            size.put("width", String.valueOf(videoWidth));
            size.put("height", String.valueOf(videoHeight));
            BytesTool.sendText(session, size.toJSONString());
            
            // 4. 读取视频帧（每帧有 12-byte header）
            byte[] frameHeader = new byte[FRAME_HEADER_SIZE];
            
            while (scrcpyLocalThread.isAlive()) {
                // 读取 frame header
                totalRead = 0;
                while (totalRead < FRAME_HEADER_SIZE) {
                    read = inputStream.read(frameHeader, totalRead, FRAME_HEADER_SIZE - totalRead);
                    if (read <= 0) {
                        log.info("scrcpy stream ended");
                        return;
                    }
                    totalRead += read;
                }
                
                // 解析 frame header
                // pts (8 bytes, big-endian) - 最高 2 bits 是 flags
                // packet_size (4 bytes, big-endian)
                long ptsAndFlags = 0;
                for (int i = 0; i < 8; i++) {
                    ptsAndFlags = (ptsAndFlags << 8) | (frameHeader[i] & 0xFF);
                }
                boolean isConfig = (ptsAndFlags & 0x8000000000000000L) != 0;
                boolean isKeyFrame = (ptsAndFlags & 0x4000000000000000L) != 0;
                
                int packetSize = ((frameHeader[8] & 0xFF) << 24) | ((frameHeader[9] & 0xFF) << 16) | 
                                ((frameHeader[10] & 0xFF) << 8) | (frameHeader[11] & 0xFF);
                
                if (packetSize <= 0 || packetSize > BUFFER_SIZE) {
                    log.warn("Invalid packet size: {}", packetSize);
                    continue;
                }
                
                // 读取视频数据
                byte[] packetData = new byte[packetSize];
                totalRead = 0;
                while (totalRead < packetSize) {
                    read = inputStream.read(packetData, totalRead, packetSize - totalRead);
                    if (read <= 0) {
                        log.warn("Failed to read packet data, expected {} bytes, got {}", packetSize, totalRead);
                        break;
                    }
                    totalRead += read;
                }
                
                if (totalRead == packetSize) {
                    // 发送数据到队列
                    dataQueue.add(packetData);
                    // 调试日志：打印前 10 帧的信息
                    if (dataQueue.size() <= 10) {
                        log.info("scrcpy frame received: size={}, isConfig={}, isKeyFrame={}, queueSize={}", 
                            packetSize, isConfig, isKeyFrame, dataQueue.size());
                    }
                }
            }
        } catch (IOException e) {
            log.error("scrcpy socket error: {}", e.getMessage());
        } finally {
            if (scrcpyLocalThread.isAlive()) {
                scrcpyLocalThread.interrupt();
                log.info("scrcpy thread closed.");
            }
            if (videoSocket.isConnected()) {
                try {
                    videoSocket.close();
                    log.info("scrcpy video socket closed.");
                } catch (IOException e) {
                    e.printStackTrace();
                }
            }
            if (inputStream != null) {
                try {
                    inputStream.close();
                    log.info("scrcpy input stream closed.");
                } catch (IOException e) {
                    e.printStackTrace();
                }
            }
        }
        AndroidDeviceBridgeTool.removeForward(iDevice, scrcpyPort, "scrcpy");
        if (session != null) {
            ScreenMap.getMap().remove(session);
        }
    }
}

