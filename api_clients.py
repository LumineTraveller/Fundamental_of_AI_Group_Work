# api_clients.py (更新)
import os
import openai
import dashscope
from abc import ABC, abstractmethod
import time
from exception_handler import retry_with_exponential_backoff
from schemas import validate_input  # 新增导入

# API 客户端实现
class BaseAPIClient:
    """API客户端的抽象基类"""
    def __init__(self, api_key):
        if not api_key:
            raise ValueError("API Key is required.")
        self.api_key = api_key

    def generate_stream(self, messages, temperature, top_p, max_tokens, callback):
        """流式生成回复的抽象方法"""
        raise NotImplementedError("子类必须实现generate_stream方法")
    
    def generate(self, messages, temperature, top_p, max_tokens):
        """同步生成回复的抽象方法"""
        raise NotImplementedError("子类必须实现generate方法")

class DeepSeekClient(BaseAPIClient):
    """DeepSeek API 客户端"""
    def __init__(self, api_key):
        super().__init__(api_key)
        try:
            import openai
            self.client = openai.OpenAI(
                api_key=self.api_key,
                base_url="https://api.deepseek.com"
            )
        except ImportError:
            raise ImportError("OpenAI库未安装，请运行'pip install openai'")

    def generate_stream(self, messages, temperature, top_p, max_tokens, callback):
        try:
            stream = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=messages,
                temperature=temperature,
                top_p=top_p,
                max_tokens=max_tokens,
                stream=True
            )
            
            full_response = ""
            for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    content = chunk.choices[0].delta.content
                    full_response += content
                    callback(content)
            return full_response
        except Exception as e:
            callback(f"DeepSeek API Error: {e}")
            raise
    
    def generate(self, messages, temperature, top_p, max_tokens):
        """同步生成回复"""
        try:
            response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=messages,
                temperature=temperature,
                top_p=top_p,
                max_tokens=max_tokens
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"DeepSeek API Error: {str(e)}"

class QwenClient(BaseAPIClient):
    """Qwen (Dashscope) API 客户端"""
    def __init__(self, api_key):
        super().__init__(api_key)
        try:
            import dashscope
            dashscope.api_key = self.api_key
            self.dashscope = dashscope
        except ImportError:
            raise ImportError("Dashscope库未安装，请运行'pip install dashscope'")

    def generate_stream(self, messages, temperature, top_p, max_tokens, callback):
        # Dashscope的temperature范围是(0, 2)，需要转换
        temp_for_qwen = max(0.01, min(temperature * 2, 1.99))

        try:
            response = self.dashscope.Generation.call(
                model=self.dashscope.Generation.Models.qwen_turbo,
                messages=messages,
                temperature=temp_for_qwen,
                top_p=top_p,
                max_tokens=max_tokens,
                result_format='message',
                stream=True
            )
            
            full_response = ""
            last_content = ""  # 跟踪上次接收到的内容
            
            for chunk in response:
                if chunk.status_code == 200:
                    if 'content' in chunk.output.choices[0]['message']:
                        current_content = chunk.output.choices[0]['message']['content']
                        
                        # 计算新增内容（避免重复）
                        if current_content.startswith(last_content):
                            new_content = current_content[len(last_content):]
                        else:
                            # 如果不匹配，可能是新的响应，使用完整内容
                            new_content = current_content
                        
                        if new_content:
                            full_response += new_content
                            callback(new_content)  # 只发送新增内容
                            last_content = current_content  # 更新最后内容
                else:
                    error_msg = f"Qwen API Error: Code: {chunk.status_code}, Message: {chunk.message}"
                    callback(error_msg)
                    return full_response
            return full_response
        except Exception as e:
            callback(f"Qwen API Error: {e}")
            raise
    
    def generate(self, messages, temperature, top_p, max_tokens):
        """同步生成回复"""
        # Dashscope的temperature范围是(0, 2)，需要转换
        temp_for_qwen = max(0.01, min(temperature * 2, 1.99))
        
        try:
            response = self.dashscope.Generation.call(
                model=self.dashscope.Generation.Models.qwen_turbo,
                messages=messages,
                temperature=temp_for_qwen,
                top_p=top_p,
                max_tokens=max_tokens,
                result_format='message'
            )
            if response.status_code == 200:
                return response.output.choices[0].message.content
            return f"Qwen API Error: {response.message}"
        except Exception as e:
            return f"Qwen API Error: {e}"