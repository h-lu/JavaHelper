import streamlit as st
import os
from deepseek_client import DeepSeekClient
from utils import init_session_state, render_markdown, add_message
from doc_parser import GuideParser
from config import DEEPSEEK_API_KEY
from typing import List
from db import Database
import uuid
from lecture_manager import LectureManager

# 页面配置
st.set_page_config(
    page_title="Java Web学生管理系统开发指南",
    page_icon="📚",
    layout="wide"
)

# 初始化会话状态
init_session_state()

# 初始化教案管理器
lecture_manager = LectureManager()

# 初始化文档解析器
if 'guide_parser' not in st.session_state:
    try:
        # 获取可用的教案
        available_lectures = lecture_manager.get_available_lectures()
        
        if not available_lectures:
            st.error("未找到任何教案文件")
            st.stop()
            
        # 默认加载第一个教案
        st.session_state.guide_parser = lecture_manager.load_lecture(available_lectures[0]["path"])
        st.session_state.current_lecture = available_lectures[0]["path"]
    except Exception as e:
        st.error(f"初始化文档解析器失败: {str(e)}")
        st.stop()

# 初始化AI响应存储
if 'ai_responses' not in st.session_state:
    st.session_state.ai_responses = {}

# 初始化对话历史
if 'chat_histories' not in st.session_state:
    st.session_state.chat_histories = {}

# 初始化 DeepSeek 客户端
try:
    if not DEEPSEEK_API_KEY:
        api_key = st.text_input("请输入 DeepSeek API 密钥:", type="password")
        if not api_key:
            st.warning("请输入 DeepSeek API 密钥以继续")
            st.stop()
    else:
        api_key = DEEPSEEK_API_KEY
        
    deepseek_client = DeepSeekClient(api_key=api_key)
except Exception as e:
    st.error(f"初始化 DeepSeek 客户端失败: {str(e)}")
    st.stop()

# 初始化数据库
db = Database()

# 在会话状态初始化部分添加
if 'session_id' not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

# 侧边栏导航
with st.sidebar:
    st.title("教案选择")
    
    # 获取可用的教案
    available_lectures = lecture_manager.get_available_lectures()
    
    if not available_lectures:
        st.error("未找到任何教案文件")
        st.stop()
    
    # 选择教案
    selected_lecture = st.selectbox(
        "选择学习内容",
        options=available_lectures,
        format_func=lambda x: x["name"]
    )
    
    # 加载选中的教案
    if 'current_lecture' not in st.session_state or \
       st.session_state.current_lecture != selected_lecture["path"]:
        try:
            st.session_state.guide_parser = lecture_manager.load_lecture(selected_lecture["path"])
            st.session_state.current_lecture = selected_lecture["path"]
            # 清除之前的对话历史
            st.session_state.chat_histories = {}
            st.session_state.learning_history = []
        except Exception as e:
            st.error(f"加载教案失败: {str(e)}")
            st.stop()
    
    st.title("学习导航")
    
    try:
        # 主章节选择
        main_section = st.selectbox(
            "选择章节",
            options=list(st.session_state.guide_parser.root.keys())
        )
        
        # 子章节选择
        if main_section:
            current_section = st.session_state.guide_parser.root[main_section]
            if current_section.children:
                sub_section = st.selectbox(
                    "选择小节",
                    options=[node.title for node in current_section.children]
                )
            else:
                sub_section = None
    except Exception as e:
        st.error(f"加载导航失败: {str(e)}")
        st.stop()

# 内容区域
if main_section:
    st.title(main_section)

    try:
        if sub_section:
            # 获取当前子节点
            current_node = next(
                node for node in current_section.children 
                if node.title == sub_section
            )
            
            # 显示子标题
            st.subheader(sub_section)
            
            # 生成当前页面的唯一标识
            page_id = f"{main_section}_{sub_section}"
            
            # 初始化当前页面的对话历史
            if page_id not in st.session_state.chat_histories:
                st.session_state.chat_histories[page_id] = []
            
            # 初始化消息占位符
            if "message_placeholder" not in st.session_state:
                st.session_state.message_placeholder = st.empty()
            
            # 显示历史对话
            for message in st.session_state.chat_histories[page_id]:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])
            
            # 如果还没有对话历史，显示初始提问部分
            if not st.session_state.chat_histories[page_id]:
                # 将内容作为提示词
                edited_prompt = st.text_area(
                    "编辑提示词来获取AI指导",
                    value=current_node.prompt if current_node.prompt else current_node.content,
                    height=150,
                    key=f"prompt_{page_id}"
                )
                
                if st.button("获取AI指导", key=f"button_{page_id}"):
                    try:
                        with st.chat_message("user"):
                            st.markdown(edited_prompt)
                        
                        with st.chat_message("assistant"):
                            message_placeholder = st.empty()
                            full_response = ""
                            
                            # 构建完整的对话历史
                            messages = st.session_state.chat_histories[page_id] + [
                                {"role": "user", "content": edited_prompt}
                            ]
                            
                            # 流式输出响应
                            for response_chunk in deepseek_client.get_streaming_response(
                                messages=messages,
                                current_topic=f"{selected_lecture['name']} - {main_section} - {sub_section}"
                            ):
                                full_response += response_chunk
                                message_placeholder.markdown(full_response + "▌")
                            
                            message_placeholder.markdown(full_response)
                            
                            # 保存到对话历史
                            st.session_state.chat_histories[page_id].extend([
                                {"role": "user", "content": edited_prompt},
                                {"role": "assistant", "content": full_response}
                            ])
                            
                            # 保存到学习历史
                            st.session_state.learning_history.append({
                                "section": main_section,
                                "subsection": sub_section,
                                "prompt": edited_prompt,
                                "response": full_response
                            })
                            
                            # 使用新的 rerun 方法
                            st.rerun()
                            
                    except Exception as e:
                        st.error(f"获取AI响应失败: {str(e)}")
            
            # 修改显示建议的追加提问部分
            if st.session_state.chat_histories[page_id]:
                # 初始化问题状态
                if f"questions_{page_id}" not in st.session_state:
                    st.session_state[f"questions_{page_id}"] = deepseek_client.generate_follow_up_questions(
                        chat_history=st.session_state.chat_histories[page_id],
                        current_topic=f"{main_section} - {sub_section}"
                    )
                
                # 显示建议的追加提问按钮
                st.write("建议的追加提问：")
                
                # 垂直显示题按钮
                for idx, question in enumerate(st.session_state[f"questions_{page_id}"]):
                    if st.button(
                        question,
                        key=f"suggest_{page_id}_{len(st.session_state.chat_histories[page_id])}_{idx}",
                        use_container_width=True  # 使按钮宽度填满
                    ):
                        try:
                            with st.chat_message("user"):
                                st.markdown(question)
                                
                            with st.chat_message("assistant"):
                                message_placeholder = st.empty()
                                full_response = ""
                                
                                # 构建完整的对话历史
                                messages = st.session_state.chat_histories[page_id] + [
                                    {"role": "user", "content": question}
                                ]
                                
                                # 流式输出响应
                                for response_chunk in deepseek_client.get_streaming_response(
                                    messages=messages,
                                    current_topic=f"{selected_lecture['name']} - {main_section} - {sub_section}"
                                ):
                                    full_response += response_chunk
                                    message_placeholder.markdown(full_response + "▌")
                                
                                message_placeholder.markdown(full_response)
                                
                                # 保存到对话历史
                                st.session_state.chat_histories[page_id].extend([
                                    {"role": "user", "content": question},
                                    {"role": "assistant", "content": full_response}
                                ])
                                
                                # 保存到学习历史
                                st.session_state.learning_history.append({
                                    "section": main_section,
                                    "subsection": sub_section,
                                    "prompt": question,
                                    "response": full_response
                                })
                                
                                # 生成新的问题集
                                st.session_state[f"questions_{page_id}"] = deepseek_client.generate_follow_up_questions(
                                    chat_history=st.session_state.chat_histories[page_id],
                                    current_topic=f"{main_section} - {sub_section}"
                                )
                                
                                # 使用新的 rerun 方法
                                st.rerun()
                        except Exception as e:
                            st.error(f"获取AI响应失败: {str(e)}")
                
                # 在最后显示"换一组问题"按钮
                if st.button(
                    "换一组问题", 
                    key=f"refresh_questions_{page_id}",
                    use_container_width=True  # 使按钮宽度填满
                ):
                    st.session_state[f"questions_{page_id}"] = deepseek_client.generate_follow_up_questions(
                        chat_history=st.session_state.chat_histories[page_id],
                        current_topic=f"{main_section} - {sub_section}"
                    )
                    st.rerun()
                
                # 添加一些间距
                st.write("")
                
                # 自义提问输入框
                st.write("或者自定义提问：")
                follow_up = st.text_area(
                    "进一步提问",
                    value="",  # 设置为空字符串，确保每次都是空白输入框
                    height=100,
                    key=f"follow_up_{page_id}_{len(st.session_state.chat_histories[page_id])}"  # 动态key，确保每次都是新的输入框
                )
                
                if st.button("发送提问", key=f"follow_up_button_{page_id}_{len(st.session_state.chat_histories[page_id])}"):
                    if follow_up.strip():  # 只有当输入不为空时才处理
                        try:
                            with st.chat_message("user"):
                                st.markdown(follow_up)
                                
                            with st.chat_message("assistant"):
                                message_placeholder = st.empty()
                                full_response = ""
                                
                                # 构建完整的对话历
                                messages = st.session_state.chat_histories[page_id] + [
                                    {"role": "user", "content": follow_up}
                                ]
                                
                                # 流式输出响应
                                for response_chunk in deepseek_client.get_streaming_response(
                                    messages=messages,
                                    current_topic=f"{selected_lecture['name']} - {main_section} - {sub_section}"
                                ):
                                    full_response += response_chunk
                                    message_placeholder.markdown(full_response + "▌")
                                
                                message_placeholder.markdown(full_response)
                                
                                # 保存到对话历史
                                st.session_state.chat_histories[page_id].extend([
                                    {"role": "user", "content": follow_up},
                                    {"role": "assistant", "content": full_response}
                                ])
                                
                                # 保存学习历史
                                st.session_state.learning_history.append({
                                    "section": main_section,
                                    "subsection": sub_section,
                                    "prompt": follow_up,
                                    "response": full_response
                                })
                                
                                # 使用新的 rerun 方法
                                st.rerun()
                                
                        except Exception as e:
                            st.error(f"获取AI响应失败: {str(e)}")
        else:
            # 显示主章节内容
            st.markdown(render_markdown(current_section.content), unsafe_allow_html=True)

    except Exception as e:
        st.error(f"显示内容失败: {str(e)}")

# 显示学习历史
if st.sidebar.checkbox("显示学习历史"):
    st.sidebar.subheader("学习历史")
    for idx, item in enumerate(st.session_state.learning_history):
        with st.sidebar.expander(
            f"{item['section']} - {item['subsection']}"
        ):
            st.write("提示词：", item['prompt'])
            st.write("AI回应：", item['response']) 