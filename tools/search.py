#!/usr/bin/env python3
"""
Interview Question Bank 搜索工具

用法:
    python search.py --topic "Spring"           # 按主题搜索
    python search.py --difficulty "medium"      # 按难度搜索
    python search.py --company "Google"         # 按公司搜索
    python search.py --tag "Java"               # 按技术栈搜索
"""

import os
import argparse
import re
from pathlib import Path
from typing import List, Dict, Set

class InterviewQuestionSearcher:
    def __init__(self, root_dir: str = "."):
        self.root_dir = Path(root_dir)
        self.questions_dir = self.root_dir / "questions"
        
    def search_by_topic(self, topic: str) -> List[Dict]:
        """按主题搜索面试题"""
        results = []
        topic_pattern = re.compile(topic, re.IGNORECASE)
        
        for md_file in self.questions_dir.rglob("*.md"):
            if md_file.name == "README.md":
                continue
                
            try:
                with open(md_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                if topic_pattern.search(content):
                    metadata = self._extract_metadata(content, md_file)
                    if metadata:
                        results.append(metadata)
            except Exception as e:
                print(f"读取文件错误 {md_file}: {e}")
                
        return results
    
    def search_by_difficulty(self, difficulty: str) -> List[Dict]:
        """按难度级别搜索面试题"""
        results = []
        difficulty_mapping = {
            "easy": "初级",
            "medium": "中级", 
            "hard": "高级",
            "初级": "初级",
            "中级": "中级",
            "高级": "高级"
        }
        
        target_difficulty = difficulty_mapping.get(difficulty.lower(), difficulty)
        difficulty_pattern = re.compile(f"【{target_difficulty}】", re.IGNORECASE)
        
        for md_file in self.questions_dir.rglob("*.md"):
            if md_file.name == "README.md":
                continue
                
            try:
                with open(md_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                if difficulty_pattern.search(content):
                    metadata = self._extract_metadata(content, md_file)
                    if metadata:
                        results.append(metadata)
            except Exception as e:
                print(f"读取文件错误 {md_file}: {e}")
                
        return results
    
    def search_by_tag(self, tag: str) -> List[Dict]:
        """按技术栈标签搜索面试题"""
        results = []
        tag_pattern = re.compile(tag, re.IGNORECASE)
        
        for md_file in self.questions_dir.rglob("*.md"):
            if md_file.name == "README.md":
                continue
                
            try:
                with open(md_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                # 在标签部分搜索
                if "## 🏷️ 标签" in content:
                    tag_section = content.split("## 🏷️ 标签")[1].split("##")[0]
                    if tag_pattern.search(tag_section):
                        metadata = self._extract_metadata(content, md_file)
                        if metadata:
                            results.append(metadata)
            except Exception as e:
                print(f"读取文件错误 {md_file}: {e}")
                
        return results
    
    def search_by_company(self, company: str) -> List[Dict]:
        """按公司搜索面试题"""
        results = []
        company_pattern = re.compile(company, re.IGNORECASE)
        
        company_dir = self.questions_dir / "company-specific"
        if company_dir.exists():
            for md_file in company_dir.rglob("*.md"):
                try:
                    with open(md_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                        
                    if company_pattern.search(content):
                        metadata = self._extract_metadata(content, md_file)
                        if metadata:
                            results.append(metadata)
                except Exception as e:
                    print(f"读取文件错误 {md_file}: {e}")
                    
        return results
    
    def _extract_metadata(self, content: str, file_path: Path) -> Dict:
        """提取面试题元数据"""
        try:
            # 提取标题
            title_match = re.search(r'^# (.+)$', content, re.MULTILINE)
            title = title_match.group(1) if title_match else file_path.stem
            
            # 提取标签
            tags = []
            if "## 🏷️ 标签" in content:
                tag_section = content.split("## 🏷️ 标签")[1].split("##")[0]
                tag_matches = re.findall(r'- 技术栈: (.+)', tag_section)
                if tag_matches:
                    tags.extend([tag.strip() for tag in tag_matches[0].split(',')])
                    
                difficulty_match = re.search(r'- 难度: (.+)', tag_section)
                if difficulty_match:
                    tags.append(f"难度:{difficulty_match.group(1).strip()}")
            
            # 提取问题数量
            question_count = len(re.findall(r'#### \*\*【.+?】\*\*', content))
            
            # 计算相对路径
            relative_path = file_path.relative_to(self.root_dir)
            
            return {
                'title': title,
                'file': str(relative_path),
                'tags': tags,
                'questions': question_count,
                'category': file_path.parent.name
            }
        except Exception as e:
            print(f"提取元数据错误 {file_path}: {e}")
            return None
    
    def list_all_categories(self) -> List[str]:
        """列出所有题目分类"""
        categories = set()
        for item in self.questions_dir.iterdir():
            if item.is_dir():
                categories.add(item.name)
        return sorted(list(categories))
    
    def get_statistics(self) -> Dict:
        """获取题库统计信息"""
        stats = {
            'total_files': 0,
            'total_questions': 0,
            'categories': {},
            'technologies': set()
        }
        
        for md_file in self.questions_dir.rglob("*.md"):
            if md_file.name == "README.md":
                continue
                
            try:
                with open(md_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                stats['total_files'] += 1
                
                # 统计问题数量
                question_count = len(re.findall(r'#### \*\*【.+?】\*\*', content))
                stats['total_questions'] += question_count
                
                # 统计分类
                category = md_file.parent.name
                if category not in stats['categories']:
                    stats['categories'][category] = 0
                stats['categories'][category] += question_count
                
                # 统计技术栈
                if "技术栈:" in content:
                    tech_matches = re.findall(r'技术栈: (.+)', content)
                    for tech_line in tech_matches:
                        techs = [tech.strip() for tech in tech_line.split(',')]
                        stats['technologies'].update(techs)
                        
            except Exception as e:
                print(f"统计错误 {md_file}: {e}")
        
        stats['technologies'] = sorted(list(stats['technologies']))
        return stats

def print_results(results: List[Dict], search_type: str, search_term: str):
    """打印搜索结果"""
    if not results:
        print(f"❌ 没有找到关于 '{search_term}' 的{search_type}相关题目")
        return
    
    print(f"🔍 {search_type}搜索: '{search_term}' - 找到 {len(results)} 个结果\n")
    print("=" * 80)
    
    for i, result in enumerate(results, 1):
        print(f"{i}. 📄 {result['title']}")
        print(f"   📂 文件: {result['file']}")
        print(f"   🏷️  标签: {', '.join(result['tags'])}")
        print(f"   📊 题目数量: {result['questions']}")
        print(f"   📂 分类: {result['category']}")
        print("-" * 80)

def print_statistics(stats: Dict):
    """打印统计信息"""
    print("📊 面试题库统计信息")
    print("=" * 50)
    print(f"📁 总文件数: {stats['total_files']}")
    print(f"❓ 总题目数: {stats['total_questions']}")
    print(f"🏷️  技术栈数: {len(stats['technologies'])}")
    
    print("\n📂 分类统计:")
    for category, count in stats['categories'].items():
        print(f"   {category}: {count} 题")
    
    print(f"\n🔧 涵盖技术:")
    tech_line = ""
    for tech in stats['technologies']:
        if len(tech_line + tech + ", ") > 60:
            print(f"   {tech_line[:-2]}")
            tech_line = ""
        tech_line += tech + ", "
    if tech_line:
        print(f"   {tech_line[:-2]}")

def main():
    parser = argparse.ArgumentParser(description='Interview Question Bank 搜索工具')
    parser.add_argument('--topic', '-t', help='按主题搜索')
    parser.add_argument('--difficulty', '-d', help='按难度搜索 (easy/medium/hard 或 初级/中级/高级)')
    parser.add_argument('--company', '-c', help='按公司搜索')
    parser.add_argument('--tag', '-g', help='按技术栈标签搜索')
    parser.add_argument('--list-categories', '-l', action='store_true', help='列出所有分类')
    parser.add_argument('--stats', '-s', action='store_true', help='显示统计信息')
    parser.add_argument('--root', '-r', default='.', help='项目根目录路径')
    
    args = parser.parse_args()
    
    searcher = InterviewQuestionSearcher(args.root)
    
    if args.list_categories:
        categories = searcher.list_all_categories()
        print("📂 可用分类:")
        for category in categories:
            print(f"   - {category}")
        return
    
    if args.stats:
        stats = searcher.get_statistics()
        print_statistics(stats)
        return
    
    if args.topic:
        results = searcher.search_by_topic(args.topic)
        print_results(results, "主题", args.topic)
    elif args.difficulty:
        results = searcher.search_by_difficulty(args.difficulty)
        print_results(results, "难度", args.difficulty)
    elif args.company:
        results = searcher.search_by_company(args.company)
        print_results(results, "公司", args.company)
    elif args.tag:
        results = searcher.search_by_tag(args.tag)
        print_results(results, "技术栈", args.tag)
    else:
        parser.print_help()

if __name__ == "__main__":
    main() 