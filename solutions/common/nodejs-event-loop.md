# 通用面试 - Node.js事件循环机制完整实现

[← 返回Node.js基础面试题](../../questions/backend/nodejs-basics.md)

## 🎯 解决方案概述

Node.js事件循环是其非阻塞I/O模型的核心机制，基于libuv库实现。本方案深入分析事件循环的工作原理、各个阶段的执行顺序、微任务和宏任务的调度机制，以及在实际开发中的性能优化策略。

## 💡 核心问题分析

### Node.js事件循环的技术挑战

**业务背景**：Node.js采用单线程事件驱动架构，需要通过事件循环机制处理大量并发I/O操作

**技术难点**：
- 事件循环各阶段的执行顺序和优先级
- 微任务队列与宏任务队列的调度机制
- 异步操作的回调函数执行时机
- 阻塞操作对事件循环性能的影响
- 内存泄漏和性能瓶颈的识别与解决

## 📝 题目解决方案

### 解决方案思路分析

#### 1. 事件循环架构设计

**为什么选择事件驱动模型？**
- **高并发处理**：单线程处理大量I/O密集型操作
- **内存效率**：避免线程创建和切换的开销
- **简化编程**：无需考虑线程同步和竞态条件
- **异步非阻塞**：提高系统吞吐量和响应性

#### 2. 事件循环六个阶段

**完整执行流程**：
1. **Timer阶段**：执行setTimeout()和setInterval()回调
2. **Pending callbacks阶段**：执行延迟到下一个循环的I/O回调
3. **Idle, prepare阶段**：仅内部使用
4. **Poll阶段**：获取新的I/O事件，执行I/O相关回调
5. **Check阶段**：执行setImmediate()回调
6. **Close callbacks阶段**：执行关闭事件的回调

#### 3. 微任务与宏任务调度

**优先级机制**：
- **微任务**：process.nextTick() > Promise.resolve()
- **宏任务**：setTimeout() > setImmediate() > I/O操作
- **执行规则**：每个阶段结束后清空所有微任务队列

### 代码实现要点

#### Node.js事件循环机制深度实现

```javascript
/**
 * Node.js事件循环机制完整实现和分析
 * 
 * 设计原理：
 * 1. 深入理解事件循环的六个阶段
 * 2. 分析微任务和宏任务的执行顺序
 * 3. 实现事件循环性能监控
 * 4. 提供最佳实践和优化策略
 */

const fs = require('fs');
const util = require('util');
const { performance } = require('perf_hooks');

// ==================== 事件循环阶段演示 ====================

/**
 * 事件循环各阶段执行顺序演示
 */
class EventLoopDemo {
    constructor() {
        this.phaseCount = {
            timer: 0,
            immediate: 0,
            nextTick: 0,
            promise: 0,
            io: 0
        };
    }

    /**
     * 完整的事件循环阶段演示
     */
    demonstrateEventLoop() {
        console.log('=== 事件循环阶段演示开始 ===');
        
        // 1. Timer阶段 - setTimeout
        setTimeout(() => {
            console.log('1. Timer阶段: setTimeout 0ms');
            this.phaseCount.timer++;
        }, 0);
        
        setTimeout(() => {
            console.log('2. Timer阶段: setTimeout 1ms');
            this.phaseCount.timer++;
        }, 1);
        
        // 2. setImmediate - Check阶段
        setImmediate(() => {
            console.log('3. Check阶段: setImmediate');
            this.phaseCount.immediate++;
        });
        
        // 3. I/O操作 - Poll阶段
        fs.readFile(__filename, () => {
            console.log('4. Poll阶段: fs.readFile回调');
            this.phaseCount.io++;
            
            // 在I/O回调中再次测试优先级
            setTimeout(() => {
                console.log('5. Timer阶段: 嵌套setTimeout');
            }, 0);
            
            setImmediate(() => {
                console.log('6. Check阶段: 嵌套setImmediate');
            });
        });
        
        // 4. 微任务 - process.nextTick
        process.nextTick(() => {
            console.log('7. 微任务: process.nextTick');
            this.phaseCount.nextTick++;
        });
        
        // 5. 微任务 - Promise
        Promise.resolve().then(() => {
            console.log('8. 微任务: Promise.resolve');
            this.phaseCount.promise++;
        });
        
        // 6. 同步代码
        console.log('9. 同步代码: 立即执行');
        
        // 7. 嵌套的process.nextTick
        process.nextTick(() => {
            console.log('10. 微任务: 第一个nextTick');
            process.nextTick(() => {
                console.log('11. 微任务: 嵌套nextTick');
            });
        });
        
        // 统计结果
        setTimeout(() => {
            console.log('\n=== 事件循环统计结果 ===');
            console.log(`Timer阶段执行次数: ${this.phaseCount.timer}`);
            console.log(`Check阶段执行次数: ${this.phaseCount.immediate}`);
            console.log(`NextTick执行次数: ${this.phaseCount.nextTick}`);
            console.log(`Promise执行次数: ${this.phaseCount.promise}`);
            console.log(`I/O回调执行次数: ${this.phaseCount.io}`);
        }, 100);
    }

    /**
     * 微任务优先级演示
     */
    demonstrateMicrotaskPriority() {
        console.log('\n=== 微任务优先级演示 ===');
        
        // process.nextTick的优先级最高
        Promise.resolve().then(() => console.log('Promise 1'));
        process.nextTick(() => console.log('NextTick 1'));
        Promise.resolve().then(() => console.log('Promise 2'));
        process.nextTick(() => console.log('NextTick 2'));
        
        setTimeout(() => console.log('Timer 1'), 0);
        setImmediate(() => console.log('Immediate 1'));
        
        console.log('同步代码执行');
    }

    /**
     * 复杂嵌套场景演示
     */
    demonstrateComplexNesting() {
        console.log('\n=== 复杂嵌套场景演示 ===');
        
        setTimeout(() => {
            console.log('外层 setTimeout');
            process.nextTick(() => {
                console.log('setTimeout 中的 nextTick');
            });
            Promise.resolve().then(() => {
                console.log('setTimeout 中的 Promise');
            });
        }, 0);
        
        setImmediate(() => {
            console.log('外层 setImmediate');
            process.nextTick(() => {
                console.log('setImmediate 中的 nextTick');
            });
            Promise.resolve().then(() => {
                console.log('setImmediate 中的 Promise');
            });
        });
        
        process.nextTick(() => {
            console.log('外层 nextTick');
            setTimeout(() => {
                console.log('nextTick 中的 setTimeout');
            }, 0);
        });
    }
}

// ==================== 事件循环性能监控 ====================

/**
 * 事件循环性能监控器
 */
class EventLoopMonitor {
    constructor() {
        this.metrics = {
            lagHistory: [],
            cpuUsage: [],
            memoryUsage: [],
            activeHandles: 0,
            activeRequests: 0
        };
        this.isMonitoring = false;
    }

    /**
     * 开始监控事件循环性能
     */
    startMonitoring(interval = 1000) {
        if (this.isMonitoring) return;
        
        this.isMonitoring = true;
        console.log('开始监控事件循环性能...');
        
        this.monitorInterval = setInterval(() => {
            this.collectMetrics();
            this.reportMetrics();
        }, interval);
        
        // 监控事件循环延迟
        this.monitorEventLoopLag();
    }

    /**
     * 停止监控
     */
    stopMonitoring() {
        if (!this.isMonitoring) return;
        
        this.isMonitoring = false;
        clearInterval(this.monitorInterval);
        console.log('停止监控事件循环性能');
    }

    /**
     * 监控事件循环延迟
     */
    monitorEventLoopLag() {
        const lagChecker = () => {
            const start = process.hrtime.bigint();
            
            setImmediate(() => {
                const lag = Number(process.hrtime.bigint() - start) / 1e6; // 转换为毫秒
                this.metrics.lagHistory.push(lag);
                
                // 保持历史数据在合理范围内
                if (this.metrics.lagHistory.length > 60) {
                    this.metrics.lagHistory.shift();
                }
                
                if (this.isMonitoring) {
                    lagChecker();
                }
            });
        };
        
        lagChecker();
    }

    /**
     * 收集性能指标
     */
    collectMetrics() {
        // CPU使用率
        const cpuUsage = process.cpuUsage();
        this.metrics.cpuUsage.push(cpuUsage);
        
        // 内存使用情况
        const memUsage = process.memoryUsage();
        this.metrics.memoryUsage.push(memUsage);
        
        // 活跃句柄和请求数
        this.metrics.activeHandles = process._getActiveHandles().length;
        this.metrics.activeRequests = process._getActiveRequests().length;
    }

    /**
     * 报告性能指标
     */
    reportMetrics() {
        const avgLag = this.getAverageEventLoopLag();
        const maxLag = Math.max(...this.metrics.lagHistory);
        const currentMemory = this.metrics.memoryUsage[this.metrics.memoryUsage.length - 1];
        
        console.log('\n=== 事件循环性能报告 ===');
        console.log(`平均延迟: ${avgLag.toFixed(2)}ms`);
        console.log(`最大延迟: ${maxLag.toFixed(2)}ms`);
        console.log(`RSS内存: ${(currentMemory.rss / 1024 / 1024).toFixed(2)}MB`);
        console.log(`堆内存使用: ${(currentMemory.heapUsed / 1024 / 1024).toFixed(2)}MB`);
        console.log(`活跃句柄数: ${this.metrics.activeHandles}`);
        console.log(`活跃请求数: ${this.metrics.activeRequests}`);
        
        // 性能告警
        if (avgLag > 10) {
            console.warn('⚠️  事件循环延迟过高，可能存在阻塞操作！');
        }
        
        if (currentMemory.heapUsed > 100 * 1024 * 1024) { // 100MB
            console.warn('⚠️  内存使用量较高，注意内存泄漏！');
        }
    }

    /**
     * 获取平均事件循环延迟
     */
    getAverageEventLoopLag() {
        if (this.metrics.lagHistory.length === 0) return 0;
        
        const sum = this.metrics.lagHistory.reduce((acc, lag) => acc + lag, 0);
        return sum / this.metrics.lagHistory.length;
    }

    /**
     * 检测潜在的阻塞操作
     */
    detectBlockingOperations() {
        const threshold = 100; // 100ms阈值
        const blockingOperations = this.metrics.lagHistory.filter(lag => lag > threshold);
        
        if (blockingOperations.length > 0) {
            console.warn(`检测到 ${blockingOperations.length} 次可能的阻塞操作`);
            console.warn(`最长阻塞时间: ${Math.max(...blockingOperations).toFixed(2)}ms`);
        }
    }
}

// ==================== 异步流控制实现 ====================

/**
 * 异步操作流控制器
 */
class AsyncFlowController {
    constructor() {
        this.concurrencyLimit = 10;
        this.activeOperations = 0;
        this.pendingOperations = [];
    }

    /**
     * 并发控制的异步操作执行器
     */
    async executeWithConcurrencyControl(operations) {
        const results = [];
        
        for (let i = 0; i < operations.length; i++) {
            const operation = operations[i];
            
            // 如果达到并发限制，等待有空闲位置
            while (this.activeOperations >= this.concurrencyLimit) {
                await this.waitForFreeSlot();
            }
            
            this.activeOperations++;
            
            // 异步执行操作
            this.executeOperation(operation)
                .then(result => {
                    results[i] = result;
                    this.activeOperations--;
                })
                .catch(error => {
                    results[i] = { error: error.message };
                    this.activeOperations--;
                });
        }
        
        // 等待所有操作完成
        while (this.activeOperations > 0) {
            await new Promise(resolve => setTimeout(resolve, 10));
        }
        
        return results;
    }

    /**
     * 等待有空闲执行位置
     */
    async waitForFreeSlot() {
        return new Promise(resolve => {
            const checkSlot = () => {
                if (this.activeOperations < this.concurrencyLimit) {
                    resolve();
                } else {
                    setTimeout(checkSlot, 1);
                }
            };
            checkSlot();
        });
    }

    /**
     * 执行单个异步操作
     */
    async executeOperation(operation) {
        const startTime = performance.now();
        
        try {
            const result = await operation();
            const endTime = performance.now();
            
            return {
                success: true,
                result,
                duration: endTime - startTime
            };
        } catch (error) {
            const endTime = performance.now();
            
            return {
                success: false,
                error: error.message,
                duration: endTime - startTime
            };
        }
    }

    /**
     * Promise.all的优化版本，支持并发限制
     */
    async allWithLimit(promises, limit = this.concurrencyLimit) {
        const results = [];
        const executing = [];
        
        for (const [index, promise] of promises.entries()) {
            const promiseWrapper = Promise.resolve(promise).then(
                value => ({ status: 'fulfilled', value, index }),
                reason => ({ status: 'rejected', reason, index })
            );
            
            results.push(promiseWrapper);
            
            if (results.length >= limit) {
                executing.push(promiseWrapper);
            }
            
            if (executing.length >= limit) {
                await Promise.race(executing);
                executing.splice(executing.findIndex(p => p === promiseWrapper), 1);
            }
        }
        
        return Promise.all(results);
    }

    /**
     * 批处理异步操作
     */
    async batchProcess(items, processor, batchSize = 100) {
        const results = [];
        
        for (let i = 0; i < items.length; i += batchSize) {
            const batch = items.slice(i, i + batchSize);
            const batchPromises = batch.map(item => processor(item));
            
            const batchResults = await Promise.allSettled(batchPromises);
            results.push(...batchResults);
            
            // 在批次之间让出控制权
            await new Promise(resolve => setImmediate(resolve));
        }
        
        return results;
    }
}

// ==================== 内存泄漏检测 ====================

/**
 * 内存泄漏检测器
 */
class MemoryLeakDetector {
    constructor() {
        this.snapshots = [];
        this.timers = new Set();
        this.intervals = new Set();
        this.immediates = new Set();
    }

    /**
     * 开始内存泄漏检测
     */
    startDetection(interval = 5000) {
        console.log('开始内存泄漏检测...');
        
        this.detectionInterval = setInterval(() => {
            this.takeSnapshot();
            this.analyzeMemoryTrend();
            this.checkEventListeners();
            this.checkTimers();
        }, interval);
    }

    /**
     * 停止检测
     */
    stopDetection() {
        if (this.detectionInterval) {
            clearInterval(this.detectionInterval);
            console.log('停止内存泄漏检测');
        }
    }

    /**
     * 拍摄内存快照
     */
    takeSnapshot() {
        const usage = process.memoryUsage();
        const timestamp = Date.now();
        
        this.snapshots.push({
            timestamp,
            rss: usage.rss,
            heapUsed: usage.heapUsed,
            heapTotal: usage.heapTotal,
            external: usage.external,
            arrayBuffers: usage.arrayBuffers
        });
        
        // 保持最近20个快照
        if (this.snapshots.length > 20) {
            this.snapshots.shift();
        }
    }

    /**
     * 分析内存使用趋势
     */
    analyzeMemoryTrend() {
        if (this.snapshots.length < 5) return;
        
        const recent = this.snapshots.slice(-5);
        const heapGrowth = recent[recent.length - 1].heapUsed - recent[0].heapUsed;
        const timeSpan = recent[recent.length - 1].timestamp - recent[0].timestamp;
        const growthRate = heapGrowth / timeSpan * 1000; // 每秒增长字节数
        
        console.log(`\n=== 内存使用分析 ===`);
        console.log(`当前堆内存: ${(recent[recent.length - 1].heapUsed / 1024 / 1024).toFixed(2)}MB`);
        console.log(`内存增长率: ${(growthRate / 1024).toFixed(2)}KB/s`);
        
        if (growthRate > 1024 * 100) { // 100KB/s
            console.warn('⚠️  检测到持续的内存增长，可能存在内存泄漏！');
            this.suggestMemoryOptimization();
        }
    }

    /**
     * 检查事件监听器
     */
    checkEventListeners() {
        const emitters = process.listeners('warning');
        if (emitters.length > 10) {
            console.warn('⚠️  检测到大量事件监听器，可能存在内存泄漏！');
        }
    }

    /**
     * 检查定时器
     */
    checkTimers() {
        const activeHandles = process._getActiveHandles();
        const timerCount = activeHandles.filter(handle => 
            handle.constructor.name === 'Timeout' || 
            handle.constructor.name === 'Immediate'
        ).length;
        
        if (timerCount > 50) {
            console.warn(`⚠️  检测到 ${timerCount} 个活跃定时器，请检查是否正确清理！`);
        }
    }

    /**
     * 提供内存优化建议
     */
    suggestMemoryOptimization() {
        console.log('\n💡 内存优化建议:');
        console.log('1. 检查是否有未清理的定时器和事件监听器');
        console.log('2. 避免创建大量闭包和全局变量');
        console.log('3. 及时释放不再使用的对象引用');
        console.log('4. 使用对象池复用对象');
        console.log('5. 考虑使用流处理大量数据');
    }

    /**
     * 强制垃圾回收（仅用于测试）
     */
    forceGC() {
        if (global.gc) {
            console.log('执行垃圾回收...');
            global.gc();
            
            setTimeout(() => {
                this.takeSnapshot();
                console.log('垃圾回收后内存使用情况已更新');
            }, 100);
        } else {
            console.log('垃圾回收不可用，请使用 --expose-gc 标志运行');
        }
    }
}

// ==================== 使用示例和测试 ====================

/**
 * 综合示例演示
 */
class EventLoopExample {
    constructor() {
        this.monitor = new EventLoopMonitor();
        this.flowController = new AsyncFlowController();
        this.leakDetector = new MemoryLeakDetector();
    }

    /**
     * 运行完整演示
     */
    async runDemo() {
        console.log('🚀 Node.js事件循环完整演示开始\n');
        
        // 1. 基础事件循环演示
        const demo = new EventLoopDemo();
        demo.demonstrateEventLoop();
        
        await this.sleep(200);
        
        // 2. 微任务优先级演示
        demo.demonstrateMicrotaskPriority();
        
        await this.sleep(200);
        
        // 3. 复杂嵌套演示
        demo.demonstrateComplexNesting();
        
        await this.sleep(500);
        
        // 4. 性能监控演示
        await this.demonstratePerformanceMonitoring();
        
        // 5. 异步流控制演示
        await this.demonstrateAsyncFlowControl();
        
        // 6. 内存检测演示
        await this.demonstrateMemoryDetection();
    }

    /**
     * 性能监控演示
     */
    async demonstratePerformanceMonitoring() {
        console.log('\n📊 开始性能监控演示...');
        
        this.monitor.startMonitoring(2000);
        
        // 模拟一些负载
        this.simulateLoad();
        
        await this.sleep(5000);
        
        this.monitor.stopMonitoring();
        this.monitor.detectBlockingOperations();
    }

    /**
     * 异步流控制演示
     */
    async demonstrateAsyncFlowControl() {
        console.log('\n🔄 异步流控制演示...');
        
        // 创建一些模拟的异步操作
        const operations = Array.from({ length: 20 }, (_, i) => 
            () => this.simulateAsyncOperation(i, Math.random() * 100 + 50)
        );
        
        console.time('并发控制执行');
        const results = await this.flowController.executeWithConcurrencyControl(operations);
        console.timeEnd('并发控制执行');
        
        const successCount = results.filter(r => r.success).length;
        console.log(`成功执行: ${successCount}/${results.length} 个操作`);
    }

    /**
     * 内存检测演示
     */
    async demonstrateMemoryDetection() {
        console.log('\n🔍 内存泄漏检测演示...');
        
        this.leakDetector.startDetection(2000);
        
        // 模拟一些可能导致内存泄漏的操作
        this.simulateMemoryLeakScenarios();
        
        await this.sleep(8000);
        
        this.leakDetector.stopDetection();
        
        // 尝试强制垃圾回收
        this.leakDetector.forceGC();
    }

    /**
     * 模拟负载
     */
    simulateLoad() {
        // 创建一些定时器
        for (let i = 0; i < 10; i++) {
            setTimeout(() => {
                // 模拟一些CPU密集型操作
                const start = Date.now();
                while (Date.now() - start < 50) {
                    Math.random() * Math.random();
                }
            }, Math.random() * 1000);
        }
        
        // 创建一些I/O操作
        for (let i = 0; i < 5; i++) {
            fs.readFile(__filename, () => {
                // I/O回调
            });
        }
    }

    /**
     * 模拟异步操作
     */
    async simulateAsyncOperation(id, delay) {
        return new Promise((resolve, reject) => {
            setTimeout(() => {
                if (Math.random() > 0.1) {
                    resolve(`操作${id}成功`);
                } else {
                    reject(new Error(`操作${id}失败`));
                }
            }, delay);
        });
    }

    /**
     * 模拟可能导致内存泄漏的场景
     */
    simulateMemoryLeakScenarios() {
        // 场景1: 未清理的定时器
        const timers = [];
        for (let i = 0; i < 100; i++) {
            const timer = setInterval(() => {
                // 一些操作
            }, 1000);
            timers.push(timer);
        }
        
        // 场景2: 累积的数组
        const largeArray = [];
        const arrayInterval = setInterval(() => {
            largeArray.push(new Array(1000).fill('data'));
            if (largeArray.length > 100) {
                clearInterval(arrayInterval);
            }
        }, 100);
        
        // 场景3: 闭包引用
        const createClosure = () => {
            const largeData = new Array(10000).fill('closure data');
            return () => largeData.length;
        };
        
        const closures = [];
        for (let i = 0; i < 50; i++) {
            closures.push(createClosure());
        }
        
        // 6秒后清理部分资源
        setTimeout(() => {
            timers.forEach(timer => clearTimeout(timer));
            console.log('清理了部分定时器');
        }, 6000);
    }

    /**
     * 工具函数：睡眠
     */
    sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
}

// ==================== 性能优化最佳实践 ====================

/**
 * 性能优化最佳实践集合
 */
class EventLoopOptimization {
    
    /**
     * 避免阻塞事件循环的方法
     */
    static avoidBlocking() {
        console.log('\n🚀 避免阻塞事件循环的最佳实践:');
        
        // 1. 使用setImmediate分割CPU密集型任务
        const processLargeArray = (array, callback) => {
            if (array.length === 0) {
                return callback();
            }
            
            // 分批处理
            const batchSize = 1000;
            const batch = array.splice(0, batchSize);
            
            // 处理当前批次
            batch.forEach(item => {
                // 处理逻辑
            });
            
            // 让出控制权，继续处理下一批
            setImmediate(() => processLargeArray(array, callback));
        };
        
        // 2. 使用Worker Threads处理CPU密集型任务
        const { Worker, isMainThread, parentPort, workerData } = require('worker_threads');
        
        if (isMainThread) {
            const runCPUIntensiveTask = (data) => {
                return new Promise((resolve, reject) => {
                    const worker = new Worker(__filename, {
                        workerData: data
                    });
                    
                    worker.on('message', resolve);
                    worker.on('error', reject);
                    worker.on('exit', (code) => {
                        if (code !== 0) {
                            reject(new Error(`Worker stopped with exit code ${code}`));
                        }
                    });
                });
            };
        } else {
            // Worker线程中的处理逻辑
            const processData = (data) => {
                // CPU密集型计算
                let result = 0;
                for (let i = 0; i < data.iterations; i++) {
                    result += Math.sqrt(i);
                }
                return result;
            };
            
            const result = processData(workerData);
            parentPort.postMessage(result);
        }
        
        // 3. 使用流处理大文件
        const processLargeFile = (filePath) => {
            const readStream = fs.createReadStream(filePath);
            const writeStream = fs.createWriteStream(filePath + '.processed');
            
            readStream.on('data', (chunk) => {
                // 处理数据块
                const processed = chunk.toString().toUpperCase();
                writeStream.write(processed);
            });
            
            readStream.on('end', () => {
                writeStream.end();
                console.log('文件处理完成');
            });
        };
    }

    /**
     * 内存优化策略
     */
    static optimizeMemory() {
        console.log('\n💾 内存优化策略:');
        
        // 1. 对象池模式
        class ObjectPool {
            constructor(createFn, resetFn, initialSize = 10) {
                this.createFn = createFn;
                this.resetFn = resetFn;
                this.pool = [];
                
                // 预创建对象
                for (let i = 0; i < initialSize; i++) {
                    this.pool.push(this.createFn());
                }
            }
            
            acquire() {
                return this.pool.length > 0 ? this.pool.pop() : this.createFn();
            }
            
            release(obj) {
                this.resetFn(obj);
                this.pool.push(obj);
            }
        }
        
        // 2. 弱引用使用
        const cache = new WeakMap();
        
        const cacheData = (key, value) => {
            cache.set(key, value);
        };
        
        // 3. 及时清理事件监听器
        const cleanupEventListeners = () => {
            const emitter = require('events').EventEmitter;
            const instance = new emitter();
            
            const handler = () => {};
            instance.on('data', handler);
            
            // 确保清理
            instance.removeListener('data', handler);
        };
    }

    /**
     * 异步操作优化
     */
    static optimizeAsyncOperations() {
        console.log('\n⚡ 异步操作优化:');
        
        // 1. 避免过深的回调嵌套
        const processDataPromise = async (data) => {
            try {
                const step1 = await performStep1(data);
                const step2 = await performStep2(step1);
                const step3 = await performStep3(step2);
                return step3;
            } catch (error) {
                console.error('处理失败:', error);
                throw error;
            }
        };
        
        // 2. 批量处理异步操作
        const batchAsyncOperations = async (items, batchSize = 10) => {
            const results = [];
            
            for (let i = 0; i < items.length; i += batchSize) {
                const batch = items.slice(i, i + batchSize);
                const batchResults = await Promise.all(
                    batch.map(item => processItem(item))
                );
                results.push(...batchResults);
                
                // 在批次间让出控制权
                await new Promise(resolve => setImmediate(resolve));
            }
            
            return results;
        };
        
        // 3. 使用AsyncIterator处理流数据
        async function* processStream(stream) {
            for await (const chunk of stream) {
                yield processChunk(chunk);
            }
        }
    }
}

// 模拟函数（实际应用中需要具体实现）
const performStep1 = async (data) => data;
const performStep2 = async (data) => data;
const performStep3 = async (data) => data;
const processItem = async (item) => item;
const processChunk = (chunk) => chunk;

// ==================== 执行演示 ====================

// 如果直接运行此文件，执行演示
if (require.main === module) {
    const example = new EventLoopExample();
    example.runDemo().catch(console.error);
}

// 导出核心类供其他模块使用
module.exports = {
    EventLoopDemo,
    EventLoopMonitor,
    AsyncFlowController,
    MemoryLeakDetector,
    EventLoopOptimization
};
```

## 🎯 面试要点总结

### 技术深度体现
- **事件循环机制**：深入理解六个阶段的执行顺序和调度原理
- **微任务与宏任务**：掌握process.nextTick、Promise、setTimeout等的优先级
- **性能监控技术**：事件循环延迟监控、内存使用分析、阻塞操作检测
- **并发控制策略**：异步流控制、批处理、Worker Threads的合理使用

### 生产实践经验
- **性能优化实践**：避免阻塞操作、内存泄漏预防、异步操作优化
- **监控告警机制**：事件循环健康度监控、性能指标收集
- **问题排查能力**：内存泄漏定位、性能瓶颈分析、阻塞操作识别
- **架构设计考虑**：高并发处理、资源管理、错误处理机制

### 面试回答要点
- **核心原理阐述**：事件循环的工作机制和各阶段的职责
- **优化策略分享**：如何提高Node.js应用的性能和稳定性
- **实战问题解决**：常见的事件循环相关问题及解决方案
- **最佳实践总结**：在实际项目中如何合理使用异步编程

---

*本解决方案展示了Node.js事件循环的完整工作原理和性能优化策略，体现了对异步编程和性能调优的深度理解* ⚡ 