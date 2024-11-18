import os
from dotenv import load_dotenv
import streamlit as st

# 加载环境变量
load_dotenv()

# 配置项
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")  # DeepSeek API密钥

# 如果环境变量中没有，则尝试从 Streamlit Secrets 获取
if not DEEPSEEK_API_KEY:
    try:
        DEEPSEEK_API_KEY = st.secrets["DEEPSEEK_API_KEY"]
    except:
        pass