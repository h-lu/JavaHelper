import re
from typing import Dict, List, Optional
from dataclasses import dataclass
import os

@dataclass
class ContentNode:
    title: str
    content: str
    prompt: Optional[str] = None
    children: List['ContentNode'] = None
    
    def __post_init__(self):
        if self.children is None:
            self.children = []

class GuideParser:
    def __init__(self, file_path: str):
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"找不到文件: {file_path}")
            
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                self.content = f.read()
            self.root = self.parse_document()
        except Exception as e:
            raise Exception(f"解析文档时出错: {str(e)}")
    
    def extract_prompt(self, content: str) -> tuple[str, str]:
        """提取AI提示词，返回(提示词, 剩余内容)"""
        if "**AI提示词：**" not in content:
            return None, content
            
        parts = content.split("**AI提示词：**")
        before_prompt = parts[0]
        
        # 查找提示词部分（在```之间的内容）
        prompt_part = parts[1]
        prompt_start = prompt_part.find("```")
        if prompt_start == -1:
            return None, content
            
        prompt_end = prompt_part.find("```", prompt_start + 3)
        if prompt_end == -1:
            return None, content
            
        prompt = prompt_part[prompt_start + 3:prompt_end].strip()
        remaining_content = before_prompt + prompt_part[prompt_end + 3:].strip()
        
        return prompt, remaining_content
    
    def parse_document(self) -> Dict[str, ContentNode]:
        """解析文档结构"""
        sections = {}
        current_section = None
        current_subsection = None
        
        # 分割文档内容
        lines = self.content.split('\n')
        buffer = []
        skip_content = False
        
        for line in lines:
            # 跳过目录部分
            if line.startswith('## 目录'):
                skip_content = True
                continue
            elif skip_content and line.startswith('## '):
                skip_content = False
            
            if skip_content:
                continue
                
            # 匹配主标题 (## 开头)
            if line.startswith('## '):
                # 保存之前的内容
                if current_subsection and buffer:
                    content = '\n'.join(buffer)
                    prompt, cleaned_content = self.extract_prompt(content)
                    current_subsection.prompt = prompt
                    current_subsection.content = cleaned_content
                elif current_section and buffer:
                    current_section.content = '\n'.join(buffer)
                buffer = []
                
                title = line.replace('## ', '').strip()
                current_section = ContentNode(title=title, content='')
                sections[title] = current_section
                current_subsection = None
                
            # 匹配子标题 (### 开头)
            elif line.startswith('### '):
                # 保存之前的内容
                if current_subsection and buffer:
                    content = '\n'.join(buffer)
                    prompt, cleaned_content = self.extract_prompt(content)
                    current_subsection.prompt = prompt
                    current_subsection.content = cleaned_content
                elif current_section and buffer:
                    current_section.content = '\n'.join(buffer)
                buffer = []
                
                if current_section:
                    title = line.replace('### ', '').strip()
                    current_subsection = ContentNode(title=title, content='')
                    current_section.children.append(current_subsection)
            
            # 累积内容
            buffer.append(line)
            
        # 保存最后一个节点的内容
        if current_subsection and buffer:
            content = '\n'.join(buffer)
            prompt, cleaned_content = self.extract_prompt(content)
            current_subsection.prompt = prompt
            current_subsection.content = cleaned_content
        elif current_section and buffer:
            current_section.content = '\n'.join(buffer)
        
        # 清理内容
        for section in sections.values():
            # 如果有子节点，清除主节点的内容中的子节点部分
            if section.children:
                main_content = []
                lines = section.content.split('\n')
                for line in lines:
                    if line.startswith('### '):
                        break
                    main_content.append(line)
                section.content = '\n'.join(main_content).strip()
                
        return sections