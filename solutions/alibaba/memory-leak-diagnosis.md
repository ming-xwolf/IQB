# 阿里巴巴Java面试 - 内存泄漏诊断完整实现

## 🎯 解决方案概述

本文档提供生产环境内存泄漏定位和解决的完整代码实现，包括堆转储分析、运行时监控、常见泄漏场景预防等核心技术方案。

## 💡 关键技术点

- **堆转储分析**：MAT工具的编程化使用
- **运行时监控**：内存增长趋势检测
- **泄漏场景识别**：ThreadLocal、监听器、缓存等常见泄漏模式
- **自动化诊断**：内存分析工具的自动化集成

## 📝 题目2：内存泄漏定位和解决

### 内存泄漏诊断工具

```java
import org.eclipse.mat.api.*;
import org.eclipse.mat.snapshot.*;
import java.io.File;
import java.util.*;
import java.util.concurrent.ConcurrentHashMap;

/**
 * 内存泄漏诊断工具集
 * 提供堆转储分析和内存泄漏自动检测功能
 */
public class MemoryLeakDiagnostics {
    
    private static final Logger log = LoggerFactory.getLogger(MemoryLeakDiagnostics.class);
    
    /**
     * 分析堆转储文件，查找内存泄漏线索
     * @param heapDumpPath 堆转储文件路径
     * @return 分析结果报告
     */
    public static MemoryAnalysisReport analyzeHeapDump(String heapDumpPath) {
        MemoryAnalysisReport report = new MemoryAnalysisReport();
        
        try {
            // 1. 加载堆转储文件
            ISnapshot snapshot = SnapshotFactory.openSnapshot(new File(heapDumpPath), 
                new HashMap<String, String>(), new VoidProgressListener());
            
            // 2. 分析占用内存最多的对象
            List<ObjectInfo> topObjects = findTopMemoryConsumers(snapshot);
            report.setTopMemoryConsumers(topObjects);
            
            // 3. 查找可疑的大对象
            List<ObjectInfo> suspiciousObjects = findSuspiciousLargeObjects(snapshot);
            report.setSuspiciousObjects(suspiciousObjects);
            
            // 4. 分析类加载器泄漏
            List<ClassLoaderLeakInfo> classLoaderLeaks = detectClassLoaderLeaks(snapshot);
            report.setClassLoaderLeaks(classLoaderLeaks);
            
            // 5. 分析线程泄漏
            List<ThreadLeakInfo> threadLeaks = detectThreadLeaks(snapshot);
            report.setThreadLeaks(threadLeaks);
            
            // 6. 查找重复对象
            Map<String, DuplicateObjectInfo> duplicates = findDuplicateObjects(snapshot);
            report.setDuplicateObjects(duplicates);
            
            log.info("堆转储分析完成，发现 {} 个可疑对象", suspiciousObjects.size());
            
        } catch (Exception e) {
            log.error("堆转储分析失败", e);
            report.setError("分析失败: " + e.getMessage());
        }
        
        return report;
    }
    
    /**
     * 查找占用内存最多的对象
     */
    private static List<ObjectInfo> findTopMemoryConsumers(ISnapshot snapshot) throws SnapshotException {
        List<ObjectInfo> topObjects = new ArrayList<>();
        
        // 获取所有类的内存占用统计
        Collection<IClass> classes = snapshot.getClasses();
        List<IClass> sortedClasses = classes.stream()
            .sorted((c1, c2) -> Long.compare(c2.getTotalSize(), c1.getTotalSize()))
            .limit(50)
            .collect(Collectors.toList());
        
        for (IClass clazz : sortedClasses) {
            ObjectInfo info = new ObjectInfo();
            info.setClassName(clazz.getName());
            info.setInstanceCount(clazz.getNumberOfObjects());
            info.setTotalSize(clazz.getTotalSize());
            info.setRetainedSize(clazz.getRetainedSize(snapshot.getClasses()));
            
            // 分析引用关系
            info.setReferenceChains(analyzeReferenceChains(snapshot, clazz));
            
            topObjects.add(info);
        }
        
        return topObjects;
    }
    
    /**
     * 查找可疑的大对象（单个对象超过50MB）
     */
    private static List<ObjectInfo> findSuspiciousLargeObjects(ISnapshot snapshot) throws SnapshotException {
        List<ObjectInfo> suspiciousObjects = new ArrayList<>();
        long threshold = 50 * 1024 * 1024; // 50MB
        
        int[] objects = snapshot.getClasses().stream()
            .flatMapToInt(clazz -> Arrays.stream(clazz.getObjectIds()))
            .toArray();
        
        for (int objectId : objects) {
            IObject object = snapshot.getObject(objectId);
            long objectSize = object.getRetainedSize();
            
            if (objectSize > threshold) {
                ObjectInfo info = new ObjectInfo();
                info.setClassName(object.getClazz().getName());
                info.setObjectId(objectId);
                info.setRetainedSize(objectSize);
                info.setShallowSize(object.getUsedHeapSize());
                
                // 分析对象的引用路径
                info.setGCRootPath(findGCRootPath(snapshot, objectId));
                
                suspiciousObjects.add(info);
            }
        }
        
        return suspiciousObjects;
    }
    
    /**
     * 检测类加载器泄漏
     */
    private static List<ClassLoaderLeakInfo> detectClassLoaderLeaks(ISnapshot snapshot) throws SnapshotException {
        List<ClassLoaderLeakInfo> leaks = new ArrayList<>();
        
        Collection<IClass> classLoaderClasses = snapshot.getClasses().stream()
            .filter(clazz -> clazz.getName().contains("ClassLoader"))
            .collect(Collectors.toList());
        
        for (IClass clazz : classLoaderClasses) {
            if (clazz.getNumberOfObjects() > 10) { // 超过10个实例可能有问题
                ClassLoaderLeakInfo leak = new ClassLoaderLeakInfo();
                leak.setClassLoaderType(clazz.getName());
                leak.setInstanceCount(clazz.getNumberOfObjects());
                leak.setTotalSize(clazz.getTotalSize());
                
                // 分析类加载器持有的类
                leak.setLoadedClasses(analyzeLoadedClasses(snapshot, clazz));
                
                leaks.add(leak);
            }
        }
        
        return leaks;
    }
    
    /**
     * 检测线程泄漏
     */
    private static List<ThreadLeakInfo> detectThreadLeaks(ISnapshot snapshot) throws SnapshotException {
        List<ThreadLeakInfo> leaks = new ArrayList<>();
        
        Collection<IClass> threadClasses = snapshot.getClasses().stream()
            .filter(clazz -> clazz.getName().contains("Thread"))
            .collect(Collectors.toList());
        
        for (IClass clazz : threadClasses) {
            if (clazz.getNumberOfObjects() > 100) { // 超过100个线程可能有问题
                ThreadLeakInfo leak = new ThreadLeakInfo();
                leak.setThreadType(clazz.getName());
                leak.setInstanceCount(clazz.getNumberOfObjects());
                leak.setTotalSize(clazz.getTotalSize());
                
                leaks.add(leak);
            }
        }
        
        return leaks;
    }
    
    /**
     * 查找重复对象
     */
    private static Map<String, DuplicateObjectInfo> findDuplicateObjects(ISnapshot snapshot) throws SnapshotException {
        Map<String, DuplicateObjectInfo> duplicates = new HashMap<>();
        
        // 查找重复的字符串对象
        IClass stringClass = snapshot.getClassesByName("java.lang.String", false).iterator().next();
        if (stringClass != null && stringClass.getNumberOfObjects() > 1000) {
            DuplicateObjectInfo info = new DuplicateObjectInfo();
            info.setClassName("java.lang.String");
            info.setInstanceCount(stringClass.getNumberOfObjects());
            info.setTotalSize(stringClass.getTotalSize());
            duplicates.put("String", info);
        }
        
        return duplicates;
    }
    
    // 辅助方法实现...
    private static List<String> analyzeReferenceChains(ISnapshot snapshot, IClass clazz) {
        // 实现引用链分析逻辑
        return Collections.emptyList();
    }
    
    private static String findGCRootPath(ISnapshot snapshot, int objectId) {
        // 实现GC根路径查找逻辑
        return "GC Root Path";
    }
    
    private static List<String> analyzeLoadedClasses(ISnapshot snapshot, IClass classLoader) {
        // 实现类加载器分析逻辑
        return Collections.emptyList();
    }
}
```

### 运行时内存监控

```java
/**
 * 运行时内存监控器
 * 持续监控应用内存使用趋势，及时发现内存泄漏
 */
@Component
public class RuntimeMemoryMonitor {
    
    private static final Logger log = LoggerFactory.getLogger(RuntimeMemoryMonitor.class);
    
    private final Map<String, Long> baselineMemory = new ConcurrentHashMap<>();
    private final Map<String, Queue<MemorySnapshot>> memoryHistory = new ConcurrentHashMap<>();
    private final MeterRegistry meterRegistry;
    private final AlertService alertService;
    
    // 内存增长阈值配置
    private static final double MEMORY_GROWTH_WARNING_THRESHOLD = 0.20; // 20%增长警告
    private static final double MEMORY_GROWTH_CRITICAL_THRESHOLD = 0.50; // 50%增长严重告警
    private static final int HISTORY_SIZE = 100; // 保留100个历史记录
    
    public RuntimeMemoryMonitor(MeterRegistry meterRegistry, AlertService alertService) {
        this.meterRegistry = meterRegistry;
        this.alertService = alertService;
    }
    
    @EventListener
    public void onApplicationReady(ApplicationReadyEvent event) {
        log.info("启动内存监控器");
        recordBaselineMemory();
        scheduleMemoryCheck();
    }
    
    /**
     * 记录应用启动后的基线内存
     */
    private void recordBaselineMemory() {
        MemoryMXBean memoryBean = ManagementFactory.getMemoryMXBean();
        baselineMemory.put("heap", memoryBean.getHeapMemoryUsage().getUsed());
        baselineMemory.put("nonheap", memoryBean.getNonHeapMemoryUsage().getUsed());
        
        // 初始化历史记录
        memoryHistory.put("heap", new ArrayDeque<>(HISTORY_SIZE));
        memoryHistory.put("nonheap", new ArrayDeque<>(HISTORY_SIZE));
        
        log.info("基线内存已记录 - 堆内存: {}MB, 非堆内存: {}MB", 
            baselineMemory.get("heap") / 1024 / 1024,
            baselineMemory.get("nonheap") / 1024 / 1024);
    }
    
    /**
     * 每分钟检查内存增长趋势
     */
    @Scheduled(fixedRate = 60000)
    public void checkMemoryGrowth() {
        MemoryMXBean memoryBean = ManagementFactory.getMemoryMXBean();
        long currentHeap = memoryBean.getHeapMemoryUsage().getUsed();
        long currentNonHeap = memoryBean.getNonHeapMemoryUsage().getUsed();
        
        // 记录当前内存快照
        recordMemorySnapshot("heap", currentHeap);
        recordMemorySnapshot("nonheap", currentNonHeap);
        
        // 检查内存增长趋势
        checkHeapMemoryGrowth(currentHeap);
        checkNonHeapMemoryGrowth(currentNonHeap);
        
        // 检查内存泄漏模式
        detectMemoryLeakPatterns();
    }
    
    /**
     * 记录内存快照
     */
    private void recordMemorySnapshot(String type, long memoryUsage) {
        Queue<MemorySnapshot> history = memoryHistory.get(type);
        
        // 添加新快照
        MemorySnapshot snapshot = new MemorySnapshot(System.currentTimeMillis(), memoryUsage);
        history.offer(snapshot);
        
        // 维护历史记录大小
        if (history.size() > HISTORY_SIZE) {
            history.poll();
        }
        
        // 记录监控指标
        meterRegistry.gauge("memory.usage." + type, memoryUsage);
    }
    
    /**
     * 检查堆内存增长趋势
     */
    private void checkHeapMemoryGrowth(long currentHeap) {
        long baselineHeap = baselineMemory.get("heap");
        double growthRate = (double)(currentHeap - baselineHeap) / baselineHeap;
        
        meterRegistry.gauge("memory.growth.rate.heap", growthRate);
        
        if (growthRate >= MEMORY_GROWTH_CRITICAL_THRESHOLD) {
            alertService.sendCriticalAlert(
                "堆内存严重增长告警",
                String.format("堆内存增长率: %.2f%%, 当前: %dMB, 基线: %dMB", 
                    growthRate * 100, currentHeap / 1024 / 1024, baselineHeap / 1024 / 1024)
            );
            triggerDeepMemoryAnalysis("heap", currentHeap);
        } else if (growthRate >= MEMORY_GROWTH_WARNING_THRESHOLD) {
            alertService.sendWarningAlert(
                "堆内存增长警告",
                String.format("堆内存增长率: %.2f%%, 建议检查", growthRate * 100)
            );
            analyzeMemoryGrowth("heap");
        }
    }
    
    /**
     * 检查非堆内存增长趋势
     */
    private void checkNonHeapMemoryGrowth(long currentNonHeap) {
        long baselineNonHeap = baselineMemory.get("nonheap");
        double growthRate = (double)(currentNonHeap - baselineNonHeap) / baselineNonHeap;
        
        meterRegistry.gauge("memory.growth.rate.nonheap", growthRate);
        
        if (growthRate >= MEMORY_GROWTH_CRITICAL_THRESHOLD) {
            alertService.sendCriticalAlert(
                "非堆内存严重增长告警",
                String.format("非堆内存增长率: %.2f%%, 可能存在类加载器泄漏", growthRate * 100)
            );
            triggerDeepMemoryAnalysis("nonheap", currentNonHeap);
        }
    }
    
    /**
     * 检测内存泄漏模式
     */
    private void detectMemoryLeakPatterns() {
        Queue<MemorySnapshot> heapHistory = memoryHistory.get("heap");
        
        if (heapHistory.size() >= 10) {
            // 检查是否存在持续增长模式
            boolean isContinuousGrowth = checkContinuousGrowthPattern(heapHistory);
            if (isContinuousGrowth) {
                alertService.sendWarningAlert(
                    "检测到内存持续增长模式",
                    "过去10分钟内存持续增长，可能存在内存泄漏"
                );
            }
            
            // 检查内存震荡模式
            boolean isMemoryOscillation = checkMemoryOscillationPattern(heapHistory);
            if (isMemoryOscillation) {
                log.warn("检测到内存震荡模式，可能存在频繁的大对象分配");
            }
        }
    }
    
    /**
     * 检查持续增长模式
     */
    private boolean checkContinuousGrowthPattern(Queue<MemorySnapshot> history) {
        List<MemorySnapshot> snapshots = new ArrayList<>(history);
        if (snapshots.size() < 10) return false;
        
        // 检查最近10个快照是否呈增长趋势
        int growthCount = 0;
        for (int i = 1; i < Math.min(10, snapshots.size()); i++) {
            if (snapshots.get(i).getMemoryUsage() > snapshots.get(i-1).getMemoryUsage()) {
                growthCount++;
            }
        }
        
        // 如果80%以上的时间在增长，认为是持续增长
        return growthCount >= 8;
    }
    
    /**
     * 检查内存震荡模式
     */
    private boolean checkMemoryOscillationPattern(Queue<MemorySnapshot> history) {
        List<MemorySnapshot> snapshots = new ArrayList<>(history);
        if (snapshots.size() < 10) return false;
        
        // 计算内存使用的标准差
        double avg = snapshots.stream()
            .mapToLong(MemorySnapshot::getMemoryUsage)
            .average()
            .orElse(0.0);
        
        double variance = snapshots.stream()
            .mapToDouble(s -> Math.pow(s.getMemoryUsage() - avg, 2))
            .average()
            .orElse(0.0);
        
        double stdDev = Math.sqrt(variance);
        double coefficientOfVariation = stdDev / avg;
        
        // 变异系数大于0.1认为是震荡
        return coefficientOfVariation > 0.1;
    }
    
    /**
     * 分析内存增长原因
     */
    private void analyzeMemoryGrowth(String memoryType) {
        log.info("开始分析{}内存增长原因", memoryType);
        
        // 1. 分析对象统计
        Map<String, Long> objectCounts = getObjectCounts();
        objectCounts.entrySet().stream()
            .sorted(Map.Entry.<String, Long>comparingByValue().reversed())
            .limit(10)
            .forEach(entry -> 
                log.warn("对象数量较多: {} = {}", entry.getKey(), entry.getValue()));
        
        // 2. 检查缓存使用情况
        checkCacheUsage();
        
        // 3. 分析线程状态
        analyzeThreads();
        
        // 4. 检查连接池状态
        checkConnectionPools();
    }
    
    /**
     * 触发深度内存分析
     */
    private void triggerDeepMemoryAnalysis(String memoryType, long currentUsage) {
        log.error("触发深度内存分析 - 类型: {}, 当前使用: {}MB", 
            memoryType, currentUsage / 1024 / 1024);
        
        // 生成堆转储文件
        generateHeapDump();
        
        // 执行内存分析
        CompletableFuture.runAsync(() -> {
            try {
                // 这里可以调用前面的堆转储分析方法
                String dumpPath = "/app/dumps/memory-analysis-" + System.currentTimeMillis() + ".hprof";
                MemoryAnalysisReport report = MemoryLeakDiagnostics.analyzeHeapDump(dumpPath);
                
                // 发送分析报告
                alertService.sendAnalysisReport(report);
            } catch (Exception e) {
                log.error("内存分析失败", e);
            }
        });
    }
    
    // 辅助方法实现...
    private Map<String, Long> getObjectCounts() {
        // 实现对象统计逻辑
        return Collections.emptyMap();
    }
    
    private void checkCacheUsage() {
        // 实现缓存使用检查逻辑
    }
    
    private void analyzeThreads() {
        // 实现线程分析逻辑
    }
    
    private void checkConnectionPools() {
        // 实现连接池检查逻辑
    }
    
    private void generateHeapDump() {
        // 实现堆转储生成逻辑
    }
}

/**
 * 内存快照数据结构
 */
class MemorySnapshot {
    private final long timestamp;
    private final long memoryUsage;
    
    public MemorySnapshot(long timestamp, long memoryUsage) {
        this.timestamp = timestamp;
        this.memoryUsage = memoryUsage;
    }
    
    public long getTimestamp() { return timestamp; }
    public long getMemoryUsage() { return memoryUsage; }
}
```

### 常见内存泄漏场景预防

```java
/**
 * 常见内存泄漏场景的预防和解决方案
 */
public class MemoryLeakPreventionSolutions {
    
    /**
     * 1. ThreadLocal内存泄漏预防
     */
    public static class ThreadLocalSafetyPatterns {
        
        // 错误示例：ThreadLocal未清理
        private static final ThreadLocal<LargeObject> BAD_THREAD_LOCAL = new ThreadLocal<>();
        
        public void badExample() {
            BAD_THREAD_LOCAL.set(new LargeObject());
            // 忘记清理，在线程池环境下会造成内存泄漏
        }
        
        // 正确示例1：使用try-finally确保清理
        private static final ThreadLocal<LargeObject> SAFE_THREAD_LOCAL = new ThreadLocal<>();
        
        public void safeExample() {
            try {
                SAFE_THREAD_LOCAL.set(new LargeObject());
                // 业务逻辑
            } finally {
                SAFE_THREAD_LOCAL.remove(); // 确保清理
            }
        }
        
        // 正确示例2：使用AutoCloseable模式
        public static class ThreadLocalResource implements AutoCloseable {
            private final ThreadLocal<LargeObject> threadLocal = new ThreadLocal<>();
            
            public void set(LargeObject value) {
                threadLocal.set(value);
            }
            
            public LargeObject get() {
                return threadLocal.get();
            }
            
            @Override
            public void close() {
                threadLocal.remove();
            }
        }
        
        // 使用AutoCloseable模式
        public void autoCloseableExample() {
            try (ThreadLocalResource resource = new ThreadLocalResource()) {
                resource.set(new LargeObject());
                // 业务逻辑
            } // 自动清理
        }
        
        // 正确示例3：使用WeakReference
        private static final ThreadLocal<WeakReference<LargeObject>> WEAK_THREAD_LOCAL = new ThreadLocal<>();
        
        public void weakReferenceExample() {
            LargeObject obj = new LargeObject();
            WEAK_THREAD_LOCAL.set(new WeakReference<>(obj));
            
            // 使用时需要检查引用是否还存在
            WeakReference<LargeObject> ref = WEAK_THREAD_LOCAL.get();
            if (ref != null) {
                LargeObject value = ref.get();
                if (value != null) {
                    // 使用对象
                }
            }
        }
    }
    
    /**
     * 2. 监听器和回调泄漏预防
     */
    @Component
    public static class ListenerLeakPrevention {
        
        private final List<EventListener> listeners = new CopyOnWriteArrayList<>();
        private final Map<String, EventListener> namedListeners = new ConcurrentHashMap<>();
        
        // 正确的监听器管理
        public void addListener(EventListener listener) {
            listeners.add(listener);
        }
        
        public void addListener(String name, EventListener listener) {
            namedListeners.put(name, listener);
        }
        
        // 必须提供移除方法
        public boolean removeListener(EventListener listener) {
            return listeners.remove(listener);
        }
        
        public EventListener removeListener(String name) {
            return namedListeners.remove(name);
        }
        
        // 组件销毁时清理所有监听器
        @PreDestroy
        public void cleanup() {
            listeners.clear();
            namedListeners.clear();
            log.info("已清理所有监听器");
        }
        
        // 使用WeakReference管理监听器
        private final Set<WeakReference<EventListener>> weakListeners = 
            ConcurrentHashMap.newKeySet();
        
        public void addWeakListener(EventListener listener) {
            weakListeners.add(new WeakReference<>(listener));
            // 定期清理无效的弱引用
            cleanupWeakReferences();
        }
        
        private void cleanupWeakReferences() {
            weakListeners.removeIf(ref -> ref.get() == null);
        }
    }
    
    /**
     * 3. 缓存泄漏预防
     */
    @Configuration
    public static class CacheLeakPrevention {
        
        // 错误示例：无限增长的缓存
        private static final Map<String, Object> BAD_CACHE = new ConcurrentHashMap<>();
        
        // 正确示例1：使用Caffeine缓存
        @Bean
        public CacheManager safeCacheManager() {
            CaffeineCacheManager cacheManager = new CaffeineCacheManager();
            cacheManager.setCaffeine(Caffeine.newBuilder()
                .maximumSize(10000) // 限制缓存大小
                .expireAfterWrite(30, TimeUnit.MINUTES) // 写入后30分钟过期
                .expireAfterAccess(10, TimeUnit.MINUTES) // 访问后10分钟过期
                .removalListener((key, value, cause) -> {
                    log.debug("缓存项被移除: key={}, cause={}", key, cause);
                    // 处理缓存移除事件，比如释放资源
                    if (value instanceof Closeable) {
                        try {
                            ((Closeable) value).close();
                        } catch (IOException e) {
                            log.warn("关闭缓存资源失败", e);
                        }
                    }
                }));
            return cacheManager;
        }
        
        // 正确示例2：手动管理的安全缓存
        @Component
        public static class SafeManualCache<K, V> {
            private final Map<K, CacheEntry<V>> cache = new ConcurrentHashMap<>();
            private final long ttlMillis;
            
            public SafeManualCache(long ttlMillis) {
                this.ttlMillis = ttlMillis;
                // 启动清理任务
                startCleanupTask();
            }
            
            public void put(K key, V value) {
                cache.put(key, new CacheEntry<>(value, System.currentTimeMillis() + ttlMillis));
            }
            
            public V get(K key) {
                CacheEntry<V> entry = cache.get(key);
                if (entry != null && entry.getExpirationTime() > System.currentTimeMillis()) {
                    return entry.getValue();
                } else {
                    cache.remove(key);
                    return null;
                }
            }
            
            private void startCleanupTask() {
                ScheduledExecutorService scheduler = Executors.newScheduledThreadPool(1);
                scheduler.scheduleAtFixedRate(this::cleanup, 1, 1, TimeUnit.MINUTES);
            }
            
            private void cleanup() {
                long now = System.currentTimeMillis();
                cache.entrySet().removeIf(entry -> entry.getValue().getExpirationTime() <= now);
            }
            
            private static class CacheEntry<V> {
                private final V value;
                private final long expirationTime;
                
                public CacheEntry(V value, long expirationTime) {
                    this.value = value;
                    this.expirationTime = expirationTime;
                }
                
                public V getValue() { return value; }
                public long getExpirationTime() { return expirationTime; }
            }
        }
    }
    
    /**
     * 4. 连接池泄漏预防
     */
    @Component
    public static class ConnectionLeakPrevention {
        
        private final DataSource dataSource;
        
        public ConnectionLeakPrevention(DataSource dataSource) {
            this.dataSource = dataSource;
        }
        
        // 错误示例：连接未关闭
        public void badConnectionUsage() throws SQLException {
            Connection conn = dataSource.getConnection();
            // 执行SQL操作
            // 忘记关闭连接，造成连接泄漏
        }
        
        // 正确示例1：使用try-with-resources
        public void safeConnectionUsage() throws SQLException {
            try (Connection conn = dataSource.getConnection();
                 PreparedStatement stmt = conn.prepareStatement("SELECT * FROM users");
                 ResultSet rs = stmt.executeQuery()) {
                
                // 处理结果集
                while (rs.next()) {
                    // 处理数据
                }
            } // 自动关闭所有资源
        }
        
        // 正确示例2：使用Spring的JdbcTemplate
        @Autowired
        private JdbcTemplate jdbcTemplate;
        
        public List<User> safeJdbcTemplateUsage() {
            return jdbcTemplate.query("SELECT * FROM users", 
                (rs, rowNum) -> new User(rs.getLong("id"), rs.getString("name")));
        }
        
        // 连接池监控
        @Scheduled(fixedRate = 30000) // 每30秒检查一次
        public void monitorConnectionPool() {
            if (dataSource instanceof HikariDataSource) {
                HikariDataSource hikari = (HikariDataSource) dataSource;
                HikariPoolMXBean pool = hikari.getHikariPoolMXBean();
                
                int activeConnections = pool.getActiveConnections();
                int totalConnections = pool.getTotalConnections();
                int idleConnections = pool.getIdleConnections();
                
                log.info("连接池状态 - 活跃: {}, 总数: {}, 空闲: {}", 
                    activeConnections, totalConnections, idleConnections);
                
                // 检查连接泄漏
                if (activeConnections > totalConnections * 0.8) {
                    log.warn("连接池使用率过高，可能存在连接泄漏");
                }
            }
        }
    }
}

// 数据结构定义
class LargeObject {
    private final byte[] data = new byte[1024 * 1024]; // 1MB数据
}

interface EventListener {
    void onEvent(Object event);
}

class User {
    private final Long id;
    private final String name;
    
    public User(Long id, String name) {
        this.id = id;
        this.name = name;
    }
    
    // getters...
}
```

## 🎯 面试要点总结

### 技术亮点
1. **MAT工具集成**：编程化使用Eclipse MAT进行堆分析
2. **运行时监控**：持续监控内存趋势，及时发现泄漏
3. **模式识别**：自动识别常见的内存泄漏模式
4. **预防机制**：针对常见泄漏场景的代码最佳实践

### 回答要点
- **诊断工具**：MAT、JProfiler、VisualVM等工具的使用
- **监控指标**：内存增长率、对象实例数、GC回收效果
- **泄漏场景**：ThreadLocal、监听器、缓存、连接池
- **解决方案**：资源自动清理、弱引用、定期检查

---

[← 返回Java高级面试题](../../questions/company-specific/alibaba/java-advanced.md) 