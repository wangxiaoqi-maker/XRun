import { defineConfig } from 'vitest/config';

export default defineConfig({
  test: {
    // 测试环境
    environment: 'node',
    
    // 全局超时配置
    testTimeout: 240000,  // 4 分钟
    hookTimeout: 240000,  // 4 分钟
    
    // 报告配置
    reporters: ['verbose', 'json'],
    outputFile: {
      json: './reports/results.json',
    },
    
    // 测试文件匹配
    include: ['tests/**/*.test.ts'],
    
    // 并行配置（移动端测试通常串行执行）
    maxWorkers: 1,
    minWorkers: 1,
    
    // 失败重试
    retry: 0,
    
    // 测试结果概览
    passWithNoTests: true,
    
    // 全局变量
    globals: true,
    
    // 排除
    exclude: ['**/node_modules/**', '**/dist/**'],
  },
});
