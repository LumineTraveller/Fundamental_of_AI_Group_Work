import re

class InputProcessor:
    """处理用户输入，包括敏感词过滤和指令注入防护"""
    def __init__(self):
        # 敏感词列表（实际应用中应从文件或数据库加载）
        self.sensitive_words = [
            "密码", "账号", "信用卡", "暴力", "色情", 
            "毒品", "诈骗", "自杀", "杀人", "恐怖主义"
        ]
        # 危险指令模式
        self.dangerous_patterns = [
            r"system\.", r"os\.", r"subprocess\.", 
            r"exec\(|eval\(|open\(", r"rm -rf", r"del .*\\",
            r"<script>", r"drop table", r"delete from"
        ]

    def filter_sensitive_words(self, text):
        """过滤敏感词"""
        for word in self.sensitive_words:
            if word in text:
                # 替换为等长度的星号
                text = text.replace(word, '*' * len(word))
        return text

    def prevent_prompt_injection(self, text):
        """防止指令注入攻击"""
        # 移除潜在的恶意指令
        for pattern in self.dangerous_patterns:
            text = re.sub(pattern, '[removed]', text, flags=re.IGNORECASE)
        
        # 转义特殊字符
        text = re.sub(r"[<>]", lambda m: {"<": "&lt;", ">": "&gt;"}[m.group()], text)
        
        return text

    def process(self, text):
        """处理输入文本"""
        if not text:
            return text
        
        # 先防注入再过滤敏感词
        text = self.prevent_prompt_injection(text)
        text = self.filter_sensitive_words(text)
        return text