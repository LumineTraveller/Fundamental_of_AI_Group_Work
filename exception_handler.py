import time
import logging
import re

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("ExceptionHandler")

def retry_with_exponential_backoff(max_retries=3, initial_delay=1, backoff_factor=2):
    """
    带指数退避的重试装饰器
    :param max_retries: 最大重试次数
    :param initial_delay: 初始延迟时间（秒）
    :param backoff_factor: 退避因子
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            delay = initial_delay
            for attempt in range(max_retries + 1):  # +1 包含首次尝试
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_retries:
                        logger.error(f"操作失败，达到最大重试次数 {max_retries}: {str(e)}")
                        raise
                    
                    logger.warning(f"尝试 {attempt+1}/{max_retries} 失败: {str(e)}。{delay}秒后重试...")
                    time.sleep(delay)
                    delay *= backoff_factor
        return wrapper
    return decorator

class StructuredOutputHandler:
    """处理API输出的结构化错误"""
    @staticmethod
    def handle_api_output(output):
        """处理API输出，检测错误信息"""
        error_keywords = ["error", "exception", "fail", "invalid", "not found"]
        
        if any(keyword in output.lower() for keyword in error_keywords):
            # 提取错误信息
            error_match = re.search(r"Error: (.*?)(?:\n|$)", output, re.IGNORECASE)
            if error_match:
                return f"API错误: {error_match.group(1)}"
            return "API返回了错误信息"
        return output