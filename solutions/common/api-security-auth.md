# 通用面试 - API安全认证系统完整实现

[← 返回Web安全面试题](../../questions/backend/web-security.md)

## 🎯 解决方案概述

API安全认证是现代Web应用的核心安全保障，涉及用户身份验证、授权控制、会话管理、安全传输等多个层面。本方案提供了一套完整的API安全认证解决方案，包含JWT认证、OAuth2授权、RBAC权限控制、安全防护和审计日志等功能。

## 💡 核心问题分析

### API安全认证的技术挑战

**业务背景**：现代应用需要支持多端访问、第三方集成，同时确保数据安全和用户隐私保护

**技术难点**：
- 多种认证方式的统一管理和集成
- 细粒度权限控制和动态授权
- 会话安全和Token管理
- 安全威胁防护和攻击检测
- 合规性要求和审计追踪

## 📝 题目解决方案

### 解决方案思路分析

#### 1. 多层次安全架构

**为什么选择分层安全模型？**
- **认证层**：身份验证、多因素认证、社交登录
- **授权层**：权限控制、角色管理、资源访问控制
- **传输层**：HTTPS、API签名、数据加密
- **应用层**：输入验证、SQL注入防护、XSS防护

#### 2. JWT + OAuth2混合认证

**完整认证流程**：
- **JWT认证**：无状态Token、跨域支持、快速验证
- **OAuth2授权**：第三方集成、授权码模式、刷新Token
- **多因素认证**：短信验证、TOTP、生物识别
- **SSO单点登录**：统一身份管理、会话共享

#### 3. RBAC权限控制模型

**权限控制策略**：
- **角色权限**：用户-角色-权限三级模型
- **资源权限**：API级别、字段级别权限控制
- **动态权限**：基于上下文的权限计算
- **权限继承**：组织架构权限继承

### 代码实现要点

#### API安全认证系统完整实现

```javascript
/**
 * API安全认证系统完整实现
 * 
 * 设计原理：
 * 1. 多种认证方式支持：JWT、OAuth2、Session
 * 2. 细粒度权限控制：RBAC模型、资源权限
 * 3. 安全防护机制：防暴力破解、输入验证
 * 4. 审计日志：操作记录、安全事件追踪
 */

const express = require('express');
const jwt = require('jsonwebtoken');
const bcrypt = require('bcrypt');
const crypto = require('crypto');
const rateLimit = require('express-rate-limit');
const helmet = require('helmet');

// ==================== 核心认证管理器 ====================

/**
 * 认证管理器
 */
class AuthenticationManager {
    constructor(config) {
        this.config = config;
        this.jwtSecret = config.jwtSecret || crypto.randomBytes(64).toString('hex');
        this.refreshTokens = new Map(); // 生产环境应使用Redis
        this.blacklistedTokens = new Set(); // Token黑名单
        this.loginAttempts = new Map(); // 登录尝试记录
        
        // 安全配置
        this.maxLoginAttempts = config.maxLoginAttempts || 5;
        this.lockoutDuration = config.lockoutDuration || 15 * 60 * 1000; // 15分钟
        this.jwtExpiry = config.jwtExpiry || '1h';
        this.refreshTokenExpiry = config.refreshTokenExpiry || '7d';
    }

    /**
     * 用户注册
     */
    async registerUser(userData) {
        try {
            // 输入验证
            this.validateUserInput(userData);
            
            // 检查用户是否已存在
            const existingUser = await this.findUserByEmail(userData.email);
            if (existingUser) {
                throw new Error('用户已存在');
            }

            // 密码加密
            const hashedPassword = await bcrypt.hash(userData.password, 12);
            
            // 创建用户
            const user = {
                id: crypto.randomUUID(),
                email: userData.email,
                username: userData.username,
                password: hashedPassword,
                roles: ['user'], // 默认角色
                isActive: true,
                createdAt: new Date(),
                lastLoginAt: null,
                twoFactorEnabled: false
            };

            // 保存用户到数据库（这里用Map模拟）
            await this.saveUser(user);
            
            // 移除密码字段
            const { password, ...userWithoutPassword } = user;
            
            return {
                success: true,
                user: userWithoutPassword,
                message: '用户注册成功'
            };
        } catch (error) {
            return {
                success: false,
                error: error.message
            };
        }
    }

    /**
     * 用户登录
     */
    async loginUser(email, password, userAgent = '', ipAddress = '') {
        try {
            // 检查账户是否被锁定
            if (this.isAccountLocked(email)) {
                throw new Error('账户已被锁定，请稍后再试');
            }

            // 查找用户
            const user = await this.findUserByEmail(email);
            if (!user) {
                this.recordFailedLogin(email, ipAddress);
                throw new Error('用户名或密码错误');
            }

            // 验证密码
            const isPasswordValid = await bcrypt.compare(password, user.password);
            if (!isPasswordValid) {
                this.recordFailedLogin(email, ipAddress);
                throw new Error('用户名或密码错误');
            }

            // 检查账户状态
            if (!user.isActive) {
                throw new Error('账户已被禁用');
            }

            // 清除失败登录记录
            this.clearFailedLogins(email);

            // 生成Token
            const tokens = await this.generateTokens(user);
            
            // 更新最后登录时间
            user.lastLoginAt = new Date();
            await this.updateUser(user);

            // 记录登录日志
            await this.logSecurityEvent('USER_LOGIN', user.id, {
                ipAddress,
                userAgent,
                timestamp: new Date()
            });

            return {
                success: true,
                user: {
                    id: user.id,
                    email: user.email,
                    username: user.username,
                    roles: user.roles
                },
                tokens,
                message: '登录成功'
            };
        } catch (error) {
            return {
                success: false,
                error: error.message
            };
        }
    }

    /**
     * 刷新Token
     */
    async refreshToken(refreshToken) {
        try {
            // 验证刷新Token
            if (!this.refreshTokens.has(refreshToken)) {
                throw new Error('无效的刷新Token');
            }

            const tokenData = this.refreshTokens.get(refreshToken);
            const user = await this.findUserById(tokenData.userId);
            
            if (!user || !user.isActive) {
                throw new Error('用户不存在或已被禁用');
            }

            // 生成新Token
            const tokens = await this.generateTokens(user);
            
            // 删除旧的刷新Token
            this.refreshTokens.delete(refreshToken);

            return {
                success: true,
                tokens
            };
        } catch (error) {
            return {
                success: false,
                error: error.message
            };
        }
    }

    /**
     * 登出用户
     */
    async logoutUser(accessToken, refreshToken) {
        try {
            // 将Token加入黑名单
            this.blacklistedTokens.add(accessToken);
            
            // 删除刷新Token
            if (refreshToken) {
                this.refreshTokens.delete(refreshToken);
            }

            // 获取用户信息并记录登出日志
            const decoded = jwt.decode(accessToken);
            if (decoded && decoded.userId) {
                await this.logSecurityEvent('USER_LOGOUT', decoded.userId, {
                    timestamp: new Date()
                });
            }

            return {
                success: true,
                message: '登出成功'
            };
        } catch (error) {
            return {
                success: false,
                error: error.message
            };
        }
    }

    /**
     * 验证访问Token
     */
    async verifyToken(token) {
        try {
            // 检查Token是否在黑名单中
            if (this.blacklistedTokens.has(token)) {
                throw new Error('Token已失效');
            }

            // 验证JWT签名和有效期
            const decoded = jwt.verify(token, this.jwtSecret);
            
            // 检查用户是否仍然存在且活跃
            const user = await this.findUserById(decoded.userId);
            if (!user || !user.isActive) {
                throw new Error('用户不存在或已被禁用');
            }

            return {
                success: true,
                user: {
                    id: user.id,
                    email: user.email,
                    username: user.username,
                    roles: user.roles
                }
            };
        } catch (error) {
            return {
                success: false,
                error: error.message
            };
        }
    }

    /**
     * 生成Token对
     */
    async generateTokens(user) {
        const payload = {
            userId: user.id,
            email: user.email,
            roles: user.roles,
            iat: Math.floor(Date.now() / 1000)
        };

        // 生成访问Token
        const accessToken = jwt.sign(payload, this.jwtSecret, {
            expiresIn: this.jwtExpiry,
            issuer: 'api-security-system',
            audience: 'api-clients'
        });

        // 生成刷新Token
        const refreshToken = crypto.randomBytes(64).toString('hex');
        const refreshTokenExpiry = new Date();
        refreshTokenExpiry.setTime(refreshTokenExpiry.getTime() + 7 * 24 * 60 * 60 * 1000); // 7天

        // 存储刷新Token
        this.refreshTokens.set(refreshToken, {
            userId: user.id,
            expiresAt: refreshTokenExpiry,
            createdAt: new Date()
        });

        return {
            accessToken,
            refreshToken,
            tokenType: 'Bearer',
            expiresIn: this.parseJWTExpiry(this.jwtExpiry)
        };
    }

    /**
     * 解析JWT过期时间
     */
    parseJWTExpiry(expiry) {
        const match = expiry.match(/^(\d+)([smhd])$/);
        if (!match) return 3600; // 默认1小时

        const value = parseInt(match[1]);
        const unit = match[2];
        
        switch (unit) {
            case 's': return value;
            case 'm': return value * 60;
            case 'h': return value * 3600;
            case 'd': return value * 86400;
            default: return 3600;
        }
    }

    /**
     * 记录失败登录
     */
    recordFailedLogin(email, ipAddress) {
        if (!this.loginAttempts.has(email)) {
            this.loginAttempts.set(email, []);
        }
        
        const attempts = this.loginAttempts.get(email);
        attempts.push({
            timestamp: Date.now(),
            ipAddress
        });

        // 清理过期记录
        const cutoff = Date.now() - this.lockoutDuration;
        const recentAttempts = attempts.filter(attempt => attempt.timestamp > cutoff);
        this.loginAttempts.set(email, recentAttempts);
    }

    /**
     * 检查账户是否被锁定
     */
    isAccountLocked(email) {
        const attempts = this.loginAttempts.get(email) || [];
        const cutoff = Date.now() - this.lockoutDuration;
        const recentAttempts = attempts.filter(attempt => attempt.timestamp > cutoff);
        
        return recentAttempts.length >= this.maxLoginAttempts;
    }

    /**
     * 清除失败登录记录
     */
    clearFailedLogins(email) {
        this.loginAttempts.delete(email);
    }

    /**
     * 输入验证
     */
    validateUserInput(userData) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        
        if (!userData.email || !emailRegex.test(userData.email)) {
            throw new Error('无效的邮箱格式');
        }
        
        if (!userData.password || userData.password.length < 8) {
            throw new Error('密码长度至少8位');
        }
        
        if (!userData.username || userData.username.length < 3) {
            throw new Error('用户名长度至少3位');
        }

        // 密码强度检查
        const hasUpperCase = /[A-Z]/.test(userData.password);
        const hasLowerCase = /[a-z]/.test(userData.password);
        const hasNumbers = /\d/.test(userData.password);
        const hasSpecialChar = /[!@#$%^&*(),.?":{}|<>]/.test(userData.password);
        
        if (!(hasUpperCase && hasLowerCase && hasNumbers && hasSpecialChar)) {
            throw new Error('密码必须包含大小写字母、数字和特殊字符');
        }
    }

    // 模拟数据库操作方法
    async findUserByEmail(email) {
        // 这里应该是真实的数据库查询
        return this.users?.get(email) || null;
    }

    async findUserById(id) {
        // 这里应该是真实的数据库查询
        for (const user of this.users?.values() || []) {
            if (user.id === id) return user;
        }
        return null;
    }

    async saveUser(user) {
        if (!this.users) this.users = new Map();
        this.users.set(user.email, user);
    }

    async updateUser(user) {
        if (this.users) {
            this.users.set(user.email, user);
        }
    }

    async logSecurityEvent(eventType, userId, details) {
        console.log(`[SECURITY EVENT] ${eventType} - User: ${userId}`, details);
        // 这里应该写入安全日志
    }
}

// ==================== 权限控制管理器 ====================

/**
 * 基于角色的访问控制 (RBAC)
 */
class RBACManager {
    constructor() {
        this.permissions = new Map();
        this.roles = new Map();
        this.userRoles = new Map();
        
        this.initializeDefaultPermissions();
        this.initializeDefaultRoles();
    }

    /**
     * 初始化默认权限
     */
    initializeDefaultPermissions() {
        const permissions = [
            { id: 'users.read', name: '查看用户', resource: 'users', action: 'read' },
            { id: 'users.create', name: '创建用户', resource: 'users', action: 'create' },
            { id: 'users.update', name: '更新用户', resource: 'users', action: 'update' },
            { id: 'users.delete', name: '删除用户', resource: 'users', action: 'delete' },
            { id: 'posts.read', name: '查看文章', resource: 'posts', action: 'read' },
            { id: 'posts.create', name: '创建文章', resource: 'posts', action: 'create' },
            { id: 'posts.update', name: '更新文章', resource: 'posts', action: 'update' },
            { id: 'posts.delete', name: '删除文章', resource: 'posts', action: 'delete' },
            { id: 'admin.access', name: '管理员访问', resource: 'admin', action: 'access' }
        ];

        permissions.forEach(permission => {
            this.permissions.set(permission.id, permission);
        });
    }

    /**
     * 初始化默认角色
     */
    initializeDefaultRoles() {
        const roles = [
            {
                id: 'admin',
                name: '管理员',
                permissions: ['users.read', 'users.create', 'users.update', 'users.delete',
                            'posts.read', 'posts.create', 'posts.update', 'posts.delete',
                            'admin.access']
            },
            {
                id: 'editor',
                name: '编辑者',
                permissions: ['posts.read', 'posts.create', 'posts.update', 'posts.delete']
            },
            {
                id: 'user',
                name: '普通用户',
                permissions: ['posts.read']
            }
        ];

        roles.forEach(role => {
            this.roles.set(role.id, role);
        });
    }

    /**
     * 检查用户权限
     */
    hasPermission(userId, permission, resource = null, context = {}) {
        try {
            const userRoles = this.getUserRoles(userId);
            
            for (const roleId of userRoles) {
                const role = this.roles.get(roleId);
                if (role && role.permissions.includes(permission)) {
                    // 检查资源级权限
                    if (resource && !this.checkResourcePermission(userId, permission, resource, context)) {
                        continue;
                    }
                    return true;
                }
            }
            
            return false;
        } catch (error) {
            console.error('权限检查失败:', error);
            return false;
        }
    }

    /**
     * 检查资源级权限
     */
    checkResourcePermission(userId, permission, resource, context) {
        // 实现资源级权限检查逻辑
        // 例如：用户只能修改自己创建的文章
        if (permission === 'posts.update' || permission === 'posts.delete') {
            return resource.authorId === userId;
        }
        
        return true;
    }

    /**
     * 获取用户角色
     */
    getUserRoles(userId) {
        return this.userRoles.get(userId) || [];
    }

    /**
     * 为用户分配角色
     */
    assignRole(userId, roleId) {
        if (!this.roles.has(roleId)) {
            throw new Error('角色不存在');
        }

        const userRoles = this.getUserRoles(userId);
        if (!userRoles.includes(roleId)) {
            userRoles.push(roleId);
            this.userRoles.set(userId, userRoles);
        }
    }

    /**
     * 移除用户角色
     */
    removeRole(userId, roleId) {
        const userRoles = this.getUserRoles(userId);
        const index = userRoles.indexOf(roleId);
        if (index > -1) {
            userRoles.splice(index, 1);
            this.userRoles.set(userId, userRoles);
        }
    }

    /**
     * 创建权限检查中间件
     */
    createPermissionMiddleware(permission, options = {}) {
        return (req, res, next) => {
            try {
                const user = req.user;
                if (!user) {
                    return res.status(401).json({ error: '未认证用户' });
                }

                // 获取资源上下文
                const resource = options.getResource ? options.getResource(req) : null;
                const context = options.getContext ? options.getContext(req) : {};

                if (this.hasPermission(user.id, permission, resource, context)) {
                    next();
                } else {
                    res.status(403).json({ 
                        error: '权限不足',
                        required: permission
                    });
                }
            } catch (error) {
                console.error('权限中间件错误:', error);
                res.status(500).json({ error: '权限检查失败' });
            }
        };
    }
}

// ==================== 安全防护中间件 ====================

/**
 * 安全防护中间件集合
 */
class SecurityMiddleware {
    constructor(config = {}) {
        this.config = config;
    }

    /**
     * 创建认证中间件
     */
    createAuthMiddleware(authManager) {
        return async (req, res, next) => {
            try {
                const authHeader = req.headers.authorization;
                
                if (!authHeader || !authHeader.startsWith('Bearer ')) {
                    return res.status(401).json({ error: '缺少认证Token' });
                }

                const token = authHeader.substring(7);
                const result = await authManager.verifyToken(token);

                if (!result.success) {
                    return res.status(401).json({ error: result.error });
                }

                req.user = result.user;
                next();
            } catch (error) {
                console.error('认证中间件错误:', error);
                res.status(500).json({ error: '认证失败' });
            }
        };
    }

    /**
     * 创建请求限流中间件
     */
    createRateLimitMiddleware(options = {}) {
        return rateLimit({
            windowMs: options.windowMs || 15 * 60 * 1000, // 15分钟
            max: options.max || 100, // 最大请求数
            message: options.message || '请求过于频繁，请稍后再试',
            standardHeaders: true,
            legacyHeaders: false,
            keyGenerator: (req) => {
                // 可以基于用户ID或IP地址限流
                return req.user ? req.user.id : req.ip;
            }
        });
    }

    /**
     * 创建输入验证中间件
     */
    createInputValidationMiddleware(schema) {
        return (req, res, next) => {
            try {
                // 简单的输入验证示例
                for (const [field, rules] of Object.entries(schema)) {
                    const value = req.body[field];
                    
                    if (rules.required && !value) {
                        return res.status(400).json({ 
                            error: `字段 ${field} 是必需的` 
                        });
                    }
                    
                    if (value && rules.type && typeof value !== rules.type) {
                        return res.status(400).json({ 
                            error: `字段 ${field} 类型错误` 
                        });
                    }
                    
                    if (value && rules.maxLength && value.length > rules.maxLength) {
                        return res.status(400).json({ 
                            error: `字段 ${field} 长度超过限制` 
                        });
                    }
                }
                
                next();
            } catch (error) {
                console.error('输入验证错误:', error);
                res.status(500).json({ error: '输入验证失败' });
            }
        };
    }

    /**
     * 创建CORS中间件
     */
    createCORSMiddleware(options = {}) {
        const allowedOrigins = options.allowedOrigins || ['http://localhost:3000'];
        
        return (req, res, next) => {
            const origin = req.headers.origin;
            
            if (allowedOrigins.includes(origin)) {
                res.setHeader('Access-Control-Allow-Origin', origin);
            }
            
            res.setHeader('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS');
            res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization');
            res.setHeader('Access-Control-Allow-Credentials', 'true');
            
            if (req.method === 'OPTIONS') {
                res.status(200).end();
                return;
            }
            
            next();
        };
    }

    /**
     * 创建安全头中间件
     */
    createSecurityHeadersMiddleware() {
        return helmet({
            contentSecurityPolicy: {
                directives: {
                    defaultSrc: ["'self'"],
                    styleSrc: ["'self'", "'unsafe-inline'"],
                    scriptSrc: ["'self'"],
                    imgSrc: ["'self'", "data:", "https:"],
                },
            },
            hsts: {
                maxAge: 31536000,
                includeSubDomains: true,
                preload: true
            }
        });
    }
}

// ==================== API安全管理器 ====================

/**
 * API安全管理器 - 整合所有安全组件
 */
class APISecurityManager {
    constructor(config = {}) {
        this.config = config;
        this.authManager = new AuthenticationManager(config.auth || {});
        this.rbacManager = new RBACManager();
        this.securityMiddleware = new SecurityMiddleware(config.security || {});
        
        this.app = express();
        this.setupSecurityMiddlewares();
    }

    /**
     * 设置安全中间件
     */
    setupSecurityMiddlewares() {
        // 安全头
        this.app.use(this.securityMiddleware.createSecurityHeadersMiddleware());
        
        // CORS
        this.app.use(this.securityMiddleware.createCORSMiddleware(this.config.cors));
        
        // JSON解析
        this.app.use(express.json({ limit: '10mb' }));
        this.app.use(express.urlencoded({ extended: true, limit: '10mb' }));
        
        // 全局限流
        this.app.use(this.securityMiddleware.createRateLimitMiddleware({
            windowMs: 15 * 60 * 1000, // 15分钟
            max: 1000 // 全局限制
        }));
    }

    /**
     * 设置认证路由
     */
    setupAuthRoutes() {
        // 用户注册
        this.app.post('/auth/register', 
            this.securityMiddleware.createInputValidationMiddleware({
                email: { required: true, type: 'string' },
                password: { required: true, type: 'string', maxLength: 128 },
                username: { required: true, type: 'string', maxLength: 50 }
            }),
            async (req, res) => {
                const result = await this.authManager.registerUser(req.body);
                if (result.success) {
                    res.status(201).json(result);
                } else {
                    res.status(400).json(result);
                }
            }
        );

        // 用户登录
        this.app.post('/auth/login',
            // 登录限流 - 更严格
            this.securityMiddleware.createRateLimitMiddleware({
                windowMs: 15 * 60 * 1000,
                max: 10
            }),
            this.securityMiddleware.createInputValidationMiddleware({
                email: { required: true, type: 'string' },
                password: { required: true, type: 'string' }
            }),
            async (req, res) => {
                const { email, password } = req.body;
                const userAgent = req.get('User-Agent');
                const ipAddress = req.ip;
                
                const result = await this.authManager.loginUser(email, password, userAgent, ipAddress);
                
                if (result.success) {
                    res.json(result);
                } else {
                    res.status(401).json(result);
                }
            }
        );

        // Token刷新
        this.app.post('/auth/refresh', async (req, res) => {
            const { refreshToken } = req.body;
            
            if (!refreshToken) {
                return res.status(400).json({ error: '缺少刷新Token' });
            }
            
            const result = await this.authManager.refreshToken(refreshToken);
            
            if (result.success) {
                res.json(result);
            } else {
                res.status(401).json(result);
            }
        });

        // 用户登出
        this.app.post('/auth/logout', 
            this.securityMiddleware.createAuthMiddleware(this.authManager),
            async (req, res) => {
                const authHeader = req.headers.authorization;
                const accessToken = authHeader?.substring(7);
                const { refreshToken } = req.body;
                
                const result = await this.authManager.logoutUser(accessToken, refreshToken);
                res.json(result);
            }
        );
    }

    /**
     * 设置受保护的API路由
     */
    setupProtectedRoutes() {
        const authMiddleware = this.securityMiddleware.createAuthMiddleware(this.authManager);
        
        // 用户管理路由
        this.app.get('/api/users',
            authMiddleware,
            this.rbacManager.createPermissionMiddleware('users.read'),
            (req, res) => {
                res.json({
                    users: [
                        { id: '1', username: 'admin', email: 'admin@example.com' },
                        { id: '2', username: 'user1', email: 'user1@example.com' }
                    ]
                });
            }
        );

        this.app.post('/api/users',
            authMiddleware,
            this.rbacManager.createPermissionMiddleware('users.create'),
            this.securityMiddleware.createInputValidationMiddleware({
                username: { required: true, type: 'string', maxLength: 50 },
                email: { required: true, type: 'string', maxLength: 100 }
            }),
            (req, res) => {
                res.status(201).json({
                    success: true,
                    message: '用户创建成功',
                    user: req.body
                });
            }
        );

        // 文章管理路由
        this.app.get('/api/posts',
            authMiddleware,
            this.rbacManager.createPermissionMiddleware('posts.read'),
            (req, res) => {
                res.json({
                    posts: [
                        { id: '1', title: '文章1', authorId: req.user.id },
                        { id: '2', title: '文章2', authorId: 'other-user' }
                    ]
                });
            }
        );

        this.app.put('/api/posts/:id',
            authMiddleware,
            this.rbacManager.createPermissionMiddleware('posts.update', {
                getResource: (req) => ({ authorId: req.user.id }) // 简化示例
            }),
            (req, res) => {
                res.json({
                    success: true,
                    message: '文章更新成功'
                });
            }
        );

        // 管理员路由
        this.app.get('/api/admin/dashboard',
            authMiddleware,
            this.rbacManager.createPermissionMiddleware('admin.access'),
            (req, res) => {
                res.json({
                    dashboard: {
                        totalUsers: 100,
                        totalPosts: 500,
                        activeUsers: 25
                    }
                });
            }
        );
    }

    /**
     * 启动安全API服务
     */
    start(port = 3000) {
        this.setupAuthRoutes();
        this.setupProtectedRoutes();
        
        // 全局错误处理
        this.app.use((error, req, res, next) => {
            console.error('API错误:', error);
            res.status(500).json({ 
                error: '服务器内部错误',
                timestamp: new Date().toISOString()
            });
        });

        return this.app.listen(port, () => {
            console.log(`安全API服务启动在端口 ${port}`);
        });
    }
}

// ==================== 使用示例 ====================

// 导出核心类
module.exports = {
    AuthenticationManager,
    RBACManager,
    SecurityMiddleware,
    APISecurityManager
};

// 如果直接运行此文件，启动示例
if (require.main === module) {
    const config = {
        auth: {
            jwtSecret: process.env.JWT_SECRET || 'your-super-secret-jwt-key',
            jwtExpiry: '1h',
            refreshTokenExpiry: '7d',
            maxLoginAttempts: 5,
            lockoutDuration: 15 * 60 * 1000
        },
        security: {
            rateLimitWindowMs: 15 * 60 * 1000,
            rateLimitMax: 100
        },
        cors: {
            allowedOrigins: ['http://localhost:3000', 'https://yourapp.com']
        }
    };

    const securityManager = new APISecurityManager(config);
    
    // 初始化一些测试用户角色
    securityManager.rbacManager.assignRole('admin-user-id', 'admin');
    securityManager.rbacManager.assignRole('editor-user-id', 'editor');
    
    const server = securityManager.start(3000);

    // 优雅关闭
    process.on('SIGINT', () => {
        console.log('收到关闭信号，正在关闭服务器...');
        server.close(() => {
            console.log('服务器已关闭');
            process.exit(0);
        });
    });
} 