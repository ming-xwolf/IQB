# 前端面试题库

## 📚 概述

前端面试题库涵盖了现代前端开发的核心技术栈，从基础的HTML/CSS/JavaScript到流行的框架React和Vue，以及前端工程化和性能优化等高级话题。

## 🎯 核心知识点体系

### 📊 前端技术栈关联图

```mermaid
graph TD
    A[前端技术栈] --> B[基础技术]
    A --> C[框架生态]
    A --> D[工程化工具]
    A --> E[性能优化]
    
    B --> B1[HTML语义化]
    B --> B2[CSS布局&响应式]
    B --> B3[JavaScript核心]
    B --> B4[ES6+特性]
    B --> B5[浏览器API]
    
    C --> C1[React生态]
    C --> C2[Vue生态]
    C --> C3[状态管理]
    C --> C4[路由管理]
    
    D --> D1[构建工具]
    D --> D2[包管理器]
    D --> D3[代码质量]
    D --> D4[测试框架]
    
    E --> E1[性能监控]
    E --> E2[代码分割]
    E --> E3[缓存策略]
    E --> E4[SEO优化]
```

### 🗂️ 学习路径图

```mermaid
flowchart LR
    Start([开始学习]) --> Basic[HTML/CSS/JS基础]
    Basic --> Modern[现代JavaScript]
    Modern --> Framework{选择框架}
    Framework -->|React路径| React[React基础]
    Framework -->|Vue路径| Vue[Vue基础]
    React --> ReactAdv[React高级]
    Vue --> VueAdv[Vue高级]
    ReactAdv --> Engineering[前端工程化]
    VueAdv --> Engineering
    Engineering --> Performance[性能优化]
    Performance --> End([全栈前端])
```

## 📁 题库分类

### 🔰 基础技术
- [HTML语义化与可访问性](./html-semantics.md)
- [CSS布局与响应式设计](./css-layout.md) 
- [JavaScript核心概念](./javascript-core.md)
- [ES6+现代特性](./javascript-es6.md)
- [浏览器原理与Web API](./browser-apis.md)

### ⚛️ React生态
- [React基础概念](./react-basics.md)
- [React Hooks详解](./react-hooks.md)
- [React状态管理](./react-state-management.md)
- [React性能优化](./react-performance.md)

### 🟢 Vue生态  
- [Vue基础概念](./vue-basics.md)
- [Vue组合式API](./vue-composition-api.md)
- [Vue状态管理](./vue-state-management.md)
- [Vue性能优化](./vue-performance.md)

### 🛠️ 工程化与工具
- [构建工具与模块化](./build-tools.md)
- [代码质量与测试](./code-quality.md)
- [版本控制与协作](./version-control.md)

### 🚀 性能优化
- [性能监控与分析](./performance-monitoring.md)
- [代码分割与懒加载](./code-splitting.md)
- [缓存策略与CDN](./caching-strategies.md)
- [SEO与渲染优化](./seo-optimization.md)

### 🏢 企业级应用
- [微前端架构](./micro-frontends.md)
- [TypeScript实践](./typescript-practices.md)
- [安全防护](./security-practices.md)
- [国际化处理](./internationalization.md)

## 📈 难度分级

- 🟢 **初级（1-2年经验）**: 基础语法、常用API、简单交互
- 🟡 **中级（2-4年经验）**: 框架原理、状态管理、性能优化
- 🔴 **高级（4+年经验）**: 架构设计、复杂场景、团队协作

## 💡 面试技巧

### 答题思路
1. **先整体再细节**: 先说整体思路，再深入具体实现
2. **理论结合实践**: 结合实际项目经验阐述
3. **对比分析**: 比较不同方案的优缺点
4. **性能考虑**: 提及性能影响和优化方案

### 常见误区
- ❌ 只背概念，不理解原理
- ❌ 不结合实际场景
- ❌ 忽视浏览器兼容性
- ❌ 不考虑用户体验

## 🔗 相关链接

- [← 返回主目录](../../README.md)
- [后端面试题库](../backend/README.md)
- [算法面试题库](../algorithms/README.md)
- [系统设计题库](../system-design/README.md)

---

*持续更新中，欢迎贡献优质面试题！* 