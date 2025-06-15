# Interview Question Bank (IQB) 面试题库

## 📋 项目简介

Interview Question Bank (IQB) 是一个全面的面试题库系统，旨在帮助求职者准备技术面试和行为面试。本项目收录了各种技术岗位的常见面试题，包括算法、数据结构、系统设计、编程语言特定问题等。

## ✨ 功能特点

- 📚 **分类清晰**：按技术栈、难度级别、公司类型分类整理
- 🎯 **题型全面**：涵盖算法题、系统设计题、行为面试题
- 💡 **详细解答**：提供标准答案和解题思路
- 🔍 **搜索功能**：快速查找特定类型的面试题
- 📊 **进度追踪**：记录学习进度和掌握情况
- 🌟 **持续更新**：定期添加最新的面试题目

## 📁 项目结构

```
IQB/
├── README.md                   # 项目说明文档
├── docs/                       # 文档目录
│   ├── contribution.md         # 贡献指南
│   └── interview-tips.md       # 面试技巧
├── questions/                  # 题库目录
│   ├── algorithms/             # 算法题
│   ├── data-structures/        # 数据结构题
│   ├── system-design/          # 系统设计题
│   ├── frontend/               # 前端相关题目
│   ├── backend/                # 后端相关题目
│   ├── database/               # 数据库题目
│   ├── behavioral/             # 行为面试题 (通用方法论)
│   └── company-specific/       # 特定公司题目
├── solutions/                  # 解答目录
├── tools/                      # 工具脚本
└── tests/                      # 测试用例
```

## 🚀 使用方法

### 浏览题库
1. 进入 `questions/` 目录查看分类题目
2. 根据自己的需求选择相应的技术栈目录
3. 每个题目文件包含题目描述、难度等级、相关标签

### 查看解答
1. 对应的解答位于 `solutions/` 目录中
2. 解答包含多种语言实现（如适用）
3. 详细的解题思路和时间复杂度分析

### 搜索功能
使用项目根目录的搜索脚本快速查找题目：
```bash
# 搜索特定主题的题目
./tools/search.py --topic "二叉树"

# 按难度筛选
./tools/search.py --difficulty "medium"

# 按公司筛选
./tools/search.py --company "Google"
```

## 📚 题目分类

### 算法与数据结构
- 数组和字符串
- 链表
- 栈和队列
- 树和图
- 动态规划
- 贪心算法
- 排序和搜索

### 系统设计
- 分布式系统
- 数据库设计
- API 设计
- 缓存策略
- 负载均衡
- 微服务架构

### 技术栈专题
- **前端**：JavaScript, React, Vue, HTML/CSS
- **后端**：Java, Python, Go, Node.js
- **数据库**：SQL, NoSQL, 数据库优化
- **云服务**：AWS, Azure, GCP

### 行为面试
- [通用行为面试指南](./questions/behavioral/README.md)
- [STAR方法详解](./questions/behavioral/star-method-guide.md)
- [公司特定行为面试题](./questions/company-specific/README.md)
- 项目经历与团队合作
- 问题解决与领导力
- 职业规划与价值观

## 🤝 贡献指南

我们欢迎所有形式的贡献！您可以：

1. **添加新题目**：提交新的面试题和解答
2. **改进现有内容**：完善题目描述或解答
3. **修复错误**：报告或修复发现的问题
4. **优化工具**：改进搜索和管理工具

### 提交流程
1. Fork 本仓库
2. 创建功能分支 (`git checkout -b feature/new-questions`)
3. 提交更改 (`git commit -am '添加新的算法题目'`)
4. 推送到分支 (`git push origin feature/new-questions`)
5. 创建 Pull Request

## 📖 题目格式规范

每个题目文件应包含以下部分：

```markdown
# 题目标题

## 难度级别
- 初级 / 中级 / 高级

## 标签
- 算法, 数据结构, 动态规划

## 题目描述
[详细的题目描述]

## 示例
[输入输出示例]

## 要求
- 时间复杂度: O(n)
- 空间复杂度: O(1)

## 提示
[解题提示，可选]
```

## 🎯 学习建议

1. **按计划学习**：制定每日学习计划，循序渐进
2. **理解原理**：不仅要记住答案，更要理解解题思路
3. **动手实践**：实际编写代码，验证解答
4. **模拟面试**：找朋友或使用在线平台进行模拟面试
5. **总结复盘**：定期回顾和总结学习内容

## 📞 联系我们

如果您有任何问题或建议，请通过以下方式联系我们：

- 提交 Issue：[GitHub Issues](https://github.com/your-username/IQB/issues)
- 邮箱：contact@iqb.com
- 讨论区：[GitHub Discussions](https://github.com/your-username/IQB/discussions)

## 📄 许可证

本项目采用 MIT 许可证。详情请参阅 [LICENSE](LICENSE) 文件。

## 🙏 致谢

感谢所有为本项目贡献内容的开发者和面试官们！

---

⭐ 如果这个项目对您有帮助，请给我们一个 Star！

**祝您面试成功！** 🎉 