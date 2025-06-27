# schemas.py
from jsonschema import validate, ValidationError

# 输入消息的JSON Schema
INPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "role": {
            "type": "string",
            "enum": ["user", "assistant", "system"]
        },
        "content": {
            "type": "string",
            "minLength": 1,
            "maxLength": 5000
        },
        "model": {
            "type": "string",
            "enum": ["DeepSeek", "Qwen"],
            "default": ""
        }
    },
    "required": ["role", "content"]
}

# API参数的JSON Schema
PARAMS_SCHEMA = {
    "type": "object",
    "properties": {
        "temperature": {
            "type": "number",
            "minimum": 0.0,
            "maximum": 1.0
        },
        "top_p": {
            "type": "number",
            "minimum": 0.0,
            "maximum": 1.0
        },
        "max_tokens": {
            "type": "integer",
            "minimum": 100,
            "maximum": 4096
        }
    },
    "required": ["temperature", "top_p", "max_tokens"]
}

# 完整对话历史的JSON Schema
CONVERSATION_SCHEMA = {
    "type": "array",
    "items": INPUT_SCHEMA,
    "minItems": 0,  # 允许空数组
    "maxItems": 50   # 限制对话历史长度
}

def validate_input(data):
    """验证输入消息是否符合规范"""
    try:
        validate(instance=data, schema=INPUT_SCHEMA)
        return True, ""
    except ValidationError as e:
        return False, f"输入验证失败: {e.message}"

def validate_params(params):
    """验证API参数是否符合规范"""
    try:
        validate(instance=params, schema=PARAMS_SCHEMA)
        return True, ""
    except ValidationError as e:
        return False, f"参数验证失败: {e.message}"

def validate_conversation(conversation):
    """验证对话历史是否符合规范"""
    try:
        validate(instance=conversation, schema=CONVERSATION_SCHEMA)
        return True, ""
    except ValidationError as e:
        return False, f"对话历史验证失败: {e.message}"