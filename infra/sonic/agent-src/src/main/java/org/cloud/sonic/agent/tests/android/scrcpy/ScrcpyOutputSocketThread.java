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

import jakarta.websocket.Session;
import org.bytedeco.ffmpeg.avcodec.AVCodec;
import org.bytedeco.ffmpeg.avcodec.AVCodecContext;
import org.bytedeco.ffmpeg.avcodec.AVPacket;
import org.bytedeco.ffmpeg.avutil.AVFrame;
import org.bytedeco.ffmpeg.swscale.SwsContext;
import org.bytedeco.javacpp.BytePointer;
import org.cloud.sonic.agent.tests.android.AndroidTestTaskBootThread;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import javax.imageio.ImageIO;
import java.awt.image.BufferedImage;
import java.io.ByteArrayOutputStream;
import java.nio.ByteBuffer;
import java.util.concurrent.BlockingQueue;

import static org.bytedeco.ffmpeg.global.avcodec.*;
import static org.bytedeco.ffmpeg.global.avutil.*;
import static org.bytedeco.ffmpeg.global.swscale.*;
import static org.cloud.sonic.agent.tools.BytesTool.sendByte;

/**
 * 视频流输出线程 - 支持 H.264 解码
 * 将 scrcpy 的 H.264 流解码为 JPEG 帧发送给前端
 */
public class ScrcpyOutputSocketThread extends Thread {

    private final Logger log = LoggerFactory.getLogger(ScrcpyOutputSocketThread.class);

    public final static String ANDROID_OUTPUT_SOCKET_PRE = "android-scrcpy-output-socket-task-%s-%s-%s";

    private ScrcpyInputSocketThread scrcpyInputSocketThread;

    private Session session;

    private String udId;

    private AndroidTestTaskBootThread androidTestTaskBootThread;

    // FFmpeg 解码器相关
    private AVCodecContext codecContext;
    private AVPacket packet;
    private AVFrame frame;
    private AVFrame rgbFrame;
    private SwsContext swsContext;
    private boolean decoderInitialized = false;
    private int width = 0;
    private int height = 0;

    public ScrcpyOutputSocketThread(
            ScrcpyInputSocketThread scrcpyInputSocketThread,
            Session session
    ) {
        this.scrcpyInputSocketThread = scrcpyInputSocketThread;
        this.session = session;
        this.androidTestTaskBootThread = scrcpyInputSocketThread.getAndroidTestTaskBootThread();
        this.setDaemon(true);
        this.setName(androidTestTaskBootThread.formatThreadName(ANDROID_OUTPUT_SOCKET_PRE));
    }

    /**
     * 初始化 H.264 解码器
     */
    private boolean initDecoder() {
        try {
            AVCodec codec = avcodec_find_decoder(AV_CODEC_ID_H264);
            if (codec == null) {
                log.error("H.264 decoder not found");
                return false;
            }

            codecContext = avcodec_alloc_context3(codec);
            if (codecContext == null) {
                log.error("Could not allocate codec context");
                return false;
            }

            // 设置解码参数
            codecContext.flags(codecContext.flags() | AV_CODEC_FLAG_LOW_DELAY);
            codecContext.flags2(codecContext.flags2() | AV_CODEC_FLAG2_FAST);

            if (avcodec_open2(codecContext, codec, (org.bytedeco.ffmpeg.avutil.AVDictionary) null) < 0) {
                log.error("Could not open codec");
                return false;
            }

            packet = av_packet_alloc();
            frame = av_frame_alloc();
            rgbFrame = av_frame_alloc();

            if (packet == null || frame == null || rgbFrame == null) {
                log.error("Could not allocate frame or packet");
                return false;
            }

            decoderInitialized = true;
            log.info("H.264 decoder initialized successfully");
            return true;
        } catch (Exception e) {
            log.error("Failed to initialize H.264 decoder", e);
            return false;
        }
    }

    /**
     * 解码 H.264 NAL 单元并转换为 JPEG
     */
    private byte[] decodeToJpeg(byte[] nalUnit) {
        if (!decoderInitialized) {
            return null;
        }

        try {
            // 设置 packet 数据
            BytePointer data = new BytePointer(nalUnit);
            packet.data(data);
            packet.size(nalUnit.length);

            // 发送 packet 到解码器
            int ret = avcodec_send_packet(codecContext, packet);
            if (ret < 0) {
                data.close();
                return null;
            }

            // 接收解码后的帧
            ret = avcodec_receive_frame(codecContext, frame);
            data.close();
            
            if (ret < 0) {
                return null; // 需要更多数据或出错
            }

            // 更新尺寸
            if (width != frame.width() || height != frame.height()) {
                width = frame.width();
                height = frame.height();
                
                // 重新创建 SwsContext
                if (swsContext != null) {
                    sws_freeContext(swsContext);
                }
                swsContext = sws_getContext(
                        width, height, frame.format(),
                        width, height, AV_PIX_FMT_BGR24,
                        SWS_BILINEAR, null, null, (double[]) null
                );
                
                // 分配 RGB 帧缓冲区
                int size = av_image_get_buffer_size(AV_PIX_FMT_BGR24, width, height, 1);
                BytePointer buffer = new BytePointer(av_malloc(size));
                av_image_fill_arrays(rgbFrame.data(), rgbFrame.linesize(), buffer, AV_PIX_FMT_BGR24, width, height, 1);
                
                log.info("Video size: {}x{}", width, height);
            }

            if (swsContext == null) {
                return null;
            }

            // 转换为 RGB
            sws_scale(swsContext, frame.data(), frame.linesize(), 0, height, rgbFrame.data(), rgbFrame.linesize());

            // 转换为 BufferedImage
            BufferedImage image = new BufferedImage(width, height, BufferedImage.TYPE_3BYTE_BGR);
            byte[] imageData = ((java.awt.image.DataBufferByte) image.getRaster().getDataBuffer()).getData();
            
            BytePointer rgbData = rgbFrame.data(0);
            int linesize = rgbFrame.linesize(0);
            
            for (int y = 0; y < height; y++) {
                rgbData.position(y * linesize);
                rgbData.get(imageData, y * width * 3, width * 3);
            }
            rgbData.position(0);

            // 转换为 JPEG
            ByteArrayOutputStream baos = new ByteArrayOutputStream();
            ImageIO.write(image, "JPEG", baos);
            return baos.toByteArray();

        } catch (Exception e) {
            log.debug("Decode error: {}", e.getMessage());
            return null;
        }
    }

    /**
     * 释放解码器资源
     */
    private void releaseDecoder() {
        try {
            if (swsContext != null) {
                sws_freeContext(swsContext);
                swsContext = null;
            }
            if (rgbFrame != null) {
                av_frame_free(rgbFrame);
                rgbFrame = null;
            }
            if (frame != null) {
                av_frame_free(frame);
                frame = null;
            }
            if (packet != null) {
                av_packet_free(packet);
                packet = null;
            }
            if (codecContext != null) {
                avcodec_free_context(codecContext);
                codecContext = null;
            }
            decoderInitialized = false;
            log.info("H.264 decoder released");
        } catch (Exception e) {
            log.error("Error releasing decoder", e);
        }
    }

    @Override
    public void run() {
        log.info("ScrcpyOutputSocketThread started");
        
        // 初始化解码器
        boolean decoderOk = false;
        try {
            decoderOk = initDecoder();
        } catch (Throwable e) {
            log.error("Failed to initialize decoder: {}", e.getMessage(), e);
        }
        
        if (!decoderOk) {
            log.error("FFmpeg decoder initialization failed! Video streaming will not work.");
        }

        int frameCount = 0;
        try {
            while (scrcpyInputSocketThread.isAlive()) {
                BlockingQueue<byte[]> dataQueue = scrcpyInputSocketThread.getDataQueue();
                byte[] buffer = new byte[0];
                try {
                    buffer = dataQueue.take();
                } catch (InterruptedException e) {
                    log.debug("scrcpy was interrupted：", e);
                    break;
                }

                frameCount++;
                if (frameCount <= 5) {
                    log.info("ScrcpyOutputSocketThread processing frame {}, size={}, decoderInitialized={}", 
                        frameCount, buffer.length, decoderInitialized);
                }

                if (decoderInitialized) {
                    // 解码 H.264 为 JPEG
                    byte[] jpeg = decodeToJpeg(buffer);
                    if (jpeg != null) {
                        sendByte(session, jpeg);
                        if (frameCount <= 5) {
                            log.info("Sent JPEG frame {}, size={}", frameCount, jpeg.length);
                        }
                    } else {
                        if (frameCount <= 5) {
                            log.warn("Failed to decode frame {}", frameCount);
                        }
                    }
                } else {
                    // 回退：直接发送原始数据（前端无法显示）
                    sendByte(session, buffer);
                }
            }
        } finally {
            log.info("ScrcpyOutputSocketThread exiting, processed {} frames", frameCount);
            releaseDecoder();
        }
    }
    
    /**
     * 使用 screencap 命令截屏作为回退方案
     * 帧率较低 (~5 FPS) 但比无画面好
     */
    private void runScreencapFallback() {
        log.info("Starting screencap fallback mode for device");
        
        com.android.ddmlib.IDevice iDevice = scrcpyInputSocketThread.getiDevice();
        if (iDevice == null) {
            log.error("Device not available for screencap fallback");
            return;
        }
        
        int frameCount = 0;
        long lastFrameTime = 0;
        final long FRAME_INTERVAL_MS = 200; // ~5 FPS
        
        try {
            while (scrcpyInputSocketThread.isAlive()) {
                long now = System.currentTimeMillis();
                
                // 限制帧率
                if (now - lastFrameTime < FRAME_INTERVAL_MS) {
                    Thread.sleep(FRAME_INTERVAL_MS - (now - lastFrameTime));
                }
                lastFrameTime = System.currentTimeMillis();
                
                // 使用 screencap 获取截图
                byte[] pngData = captureScreen(iDevice);
                if (pngData != null && pngData.length > 0) {
                    sendByte(session, pngData);
                    frameCount++;
                    if (frameCount <= 3) {
                        log.info("Sent screencap frame {}, size={}", frameCount, pngData.length);
                    }
                }
            }
        } catch (InterruptedException e) {
            log.debug("Screencap fallback interrupted");
        } catch (Exception e) {
            log.error("Screencap fallback error: {}", e.getMessage());
        } finally {
            log.info("Screencap fallback exiting, captured {} frames", frameCount);
        }
    }
    
    /**
     * 使用 ADB 截取设备屏幕
     */
    private byte[] captureScreen(com.android.ddmlib.IDevice device) {
        try {
            com.android.ddmlib.RawImage rawImage = device.getScreenshot();
            if (rawImage == null) {
                return null;
            }
            
            // 转换为 BufferedImage
            java.awt.image.BufferedImage image = new java.awt.image.BufferedImage(
                rawImage.width, rawImage.height, java.awt.image.BufferedImage.TYPE_INT_ARGB);
            
            int index = 0;
            int bytesPerPixel = rawImage.bpp >> 3;
            for (int y = 0; y < rawImage.height; y++) {
                for (int x = 0; x < rawImage.width; x++) {
                    int value = rawImage.getARGB(index);
                    index += bytesPerPixel;
                    image.setRGB(x, y, value);
                }
            }
            
            // 压缩为 JPEG
            java.io.ByteArrayOutputStream baos = new java.io.ByteArrayOutputStream();
            javax.imageio.ImageIO.write(image, "JPEG", baos);
            return baos.toByteArray();
        } catch (Exception e) {
            log.debug("Screenshot capture failed: {}", e.getMessage());
            return null;
        }
    }
}
