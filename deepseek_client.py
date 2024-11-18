import os
from openai import OpenAI
from typing import Generator, List, Dict

class DeepSeekClient:
    def __init__(self, api_key: str):
        self.client = OpenAI(
            api_key=api_key,
            base_url="https://api.deepseek.com"
        )

    def get_streaming_response(
        self, 
        messages: List[Dict[str, str]], 
        current_topic: str = None,
        system_prompt: str = None
    ) -> Generator:
        """获取DeepSeek API的流式响应"""
        # 如果没有提供系统提示词，根据当前主题生成
        if not system_prompt:
            system_prompt = self._generate_system_prompt(current_topic)
            
        messages = [{"role": "system", "content": system_prompt}] + messages
        
        try:
            response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=messages,
                stream=True
            )
            
            for chunk in response:
                if chunk.choices[0].delta.content is not None:
                    yield chunk.choices[0].delta.content
                    
        except Exception as e:
            yield f"错误: {str(e)}"
    
    def _generate_system_prompt(self, current_topic: str) -> str:
        """根据当前主题生成系统提示词"""
        if not current_topic:
            return """你是一个专业的教育辅导助手，擅长解答学习过程中的各类问题。
请用清晰、专业的中文回答用户的问题。如果涉及代码或专业概念，请提供详细的解释和示例。"""
            
        return f"""你是一个专业的教育辅导助手，专注于{current_topic}相关内容的指导。
你将帮助学生理解和掌握这个主题的各个方面。

请注意：
1. 使用清晰、专业的中文回答问题
2. 结合实际案例进行解释
3. 循序渐进，由浅入深
4. 如涉及代码，提供详细注释
5. 鼓励学生思考和实践

你的目标是帮助学生：
1. 深入理解{current_topic}的核心概念
2. 掌握相关的实践技能
3. 培养独立解决问题的能力
4. 建立系统性的知识体系"""
            
    def generate_follow_up_questions(
        self,
        chat_history: List[Dict[str, str]],
        current_topic: str
    ) -> List[str]:
        """根据对话历史和当前主题生成相关的追加提问"""
        system_prompt = f"""你是一个专注于{current_topic}的教育辅导专家。
请根据学生的学习对话历史和当前主题，生成3个最相关的追加提问。
这些问题应该：
1. 帮助学生更深入地理解主题
2. 体现渐进式学习
3. 引导学生思考实际应用
4. 关注重要的细节和原理
请直接返回3个问题，每行一个，不要添加序号、空行或其他标记。"""
        
        # 构建提示信息
        prompt = f"""
当前主题：{current_topic}

对话历史：
{self._format_chat_history(chat_history)}

请生成3个相关的追加提问，帮助学生更深入地理解这个主题。每个问题必须是完整的句子。
"""
        
        try:
            response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                stream=False
            )
            
            # 分割响应获取问题列表并过滤空行
            questions = [
                q.strip() for q in response.choices[0].message.content.strip().split('\n')
                if q.strip()  # 只保留非空的问题
            ]
            
            # 如果获取的问题少于3个，补充默认问题
            default_questions = [
                "这个概念还有哪些深入的内容需要了解？",
                "能结合实际项目详细说明一下吗？",
                "有什么常见的问题需要注意？"
            ]
            
            while len(questions) < 3:
                questions.append(default_questions[len(questions)])
            
            # 确保只返回3个问题
            return questions[:3]
            
        except Exception as e:
            return [
                "这个概念还有哪些深入的内容需要了解？",
                "能结合实际项目详细说明一下吗？",
                "有什么常见的问题需要注意？"
            ]
    
    def _format_chat_history(self, chat_history: List[Dict[str, str]]) -> str:
        """格式化对话历史"""
        formatted = []
        for msg in chat_history:
            role = "学生" if msg["role"] == "user" else "助手"
            formatted.append(f"{role}：{msg['content']}")
        return "\n".join(formatted)