# profile_extractor.py
import json
import re
from api_clients import DeepSeekClient

# 画像提取器
class ProfileExtractor:
    """使用大模型智能提取用户画像"""
    def __init__(self, api_client):
        self.client = api_client
        
    def extract_profile(self, conversation_history):
        """使用大模型提取用户画像"""
        prompt = self._create_extraction_prompt(conversation_history)
        
        try:
            # 使用同步生成方法
            response = self.client.generate(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
                top_p=0.9,
                max_tokens=500
            )
            
            # 确保响应是字符串
            if not isinstance(response, str):
                response = str(response)
                
            return self._parse_extraction_response(response)
        except Exception as e:
            print(f"画像提取失败: {e}")
            return {}
    
    def _create_extraction_prompt(self, history):
        """创建画像提取提示"""
        # 将对话历史格式化为文本
        history_text = "\n".join(
            [f"{msg['role']}: {msg['content']}" for msg in history]
        )
        
        return f"""
请分析以下对话历史，提取用户画像信息，并按照JSON格式返回：

要求：
1. 提取用户明确提到的个人信息（姓名、年龄、职业等）
2. 推断用户的兴趣、偏好和知识领域
3. 分析用户的沟通风格（简洁/详细，正式/随意）
4. 评估用户在不同领域的知识水平（初级/中级/高级）
5. 返回格式：
{{
  "explicit_info": {{...}},
  "implicit_info": {{
    "interests": [...],
    "preferences": {{...}},
    "knowledge_level": {{...}}
  }}
}}

对话历史：
{history_text}
"""
    
    def _parse_extraction_response(self, response):
        """解析模型的响应为JSON"""
        try:
            # 提取JSON部分
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                return json.loads(json_match.group(0))
            return {}
        except json.JSONDecodeError:
            print("无法解析画像JSON")
            return {}