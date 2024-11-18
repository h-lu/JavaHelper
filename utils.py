import streamlit as st
import markdown
from typing import List, Dict

def init_session_state():
    """初始化会话状态变量"""
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    if "conversation_history" not in st.session_state:
        st.session_state.conversation_history = []
        
    if "learning_history" not in st.session_state:
        st.session_state.learning_history = []
        
    if "current_section" not in st.session_state:
        st.session_state.current_section = None
        
    if "current_subsection" not in st.session_state:
        st.session_state.current_subsection = None

def render_markdown(content: str) -> str:
    """渲染markdown内容为HTML，并保持原始格式"""
    # 使用 markdown 扩展来更好地处理内容
    md = markdown.Markdown(extensions=[
        'markdown.extensions.extra',  # 包含表格、代码块等扩展
        'markdown.extensions.toc',    # 支持目录
        'markdown.extensions.fenced_code',  # 支持代码块
        'markdown.extensions.tables'  # 支持表格
    ])
    return content  # 直接返回原始内容，让 streamlit 处理 markdown

def add_message(role: str, content: str):
    """添加消息到对话历史"""
    st.session_state.messages.append({"role": role, "content": content})

def save_learning_progress(section: str, subsection: str, prompt: str, response: str):
    """保存学习进度"""
    if "learning_history" not in st.session_state:
        st.session_state.learning_history = []
        
    st.session_state.learning_history.append({
        "section": section,
        "subsection": subsection,
        "prompt": prompt,
        "response": response
    })