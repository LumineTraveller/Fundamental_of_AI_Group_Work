# LLM安全聊天应用

这是一个支持API密钥加密存储的LLM对话应用，支持DeepSeek和Qwen模型的并行对话。

## 🔒 安全特性

### 1. API密钥加密
- 使用AES-256加密算法保护API密钥
- 基于PBKDF2的主密码派生，100,000次迭代
- 密钥永不明文存储在磁盘上

### 2. 主密码保护
- 首次使用需设置主密码（至少6位）
- 支持主密码更改功能
- 最多3次密码验证尝试

### 3. 安全存储
- 配置文件完全加密
- 自动备份功能
- 内存敏感数据自动清理

### 4. 输入安全
- 敏感词过滤
- 指令注入防护
- 输入内容预处理

## 📦 安装

### 自动安装
```bash
python install.py
```

### 手动安装
```bash
pip install -r requirements.txt
```

### 必需依赖
- Python 3.8+
- openai>=1.0.0
- dashscope>=1.14.0
- python-dotenv>=1.0.0
- cryptography>=41.0.0

## 🚀 使用方法

### 首次启动
1. 运行 `python main_gui.py`
2. 设置主密码（至少6位字符）
3. 输入API密钥并点击"保存密钥"

### 日常使用
1. 启动应用
2. 输入主密码解锁
3. 选择模型开始对话

## 🔧 功能说明

### 模型支持
- **DeepSeek**: 支持deepseek-chat模型
- **Qwen**: 支持Qwen系列模型
- **并行对话**: 可同时与两个模型对话

### 参数调整
- **Temperature**: 控制回复的创造性 (0.0-1.0)
- **Top_p**: 核采样参数 (0.0-1.0)  
- **Max Tokens**: 最大输出长度

### 对话管理
- 多对话会话支持
- 对话历史保存
- 新建/删除对话

### 安全设置
- API密钥加密保存
- 主密码更改
- 配置备份与恢复

## 🛡️ 安全最佳实践

### 密码安全
- 使用强密码（建议12位以上）
- 包含大小写字母、数字和特殊字符
- 定期更改主密码
- 不要在多个地方使用相同密码

### 存储安全
- 定期备份配置文件
- 备份文件同样加密保护
- 不要在网络上传输配置文件
- 卸载时清理所有配置文件

### 使用安全
- 不要在公共场所输入密码
- 使用完毕及时关闭应用
- 不要截图包含API密钥的界面
- 定期检查API密钥使用情况

## 📁 文件结构

```
llm-secure-chat/
├── main_gui.py              # 主界面（加密版）
├── crypto_utils.py          # 加密工具类
├── secure_config.py         # 安全配置管理
├── api_clients.py           # API客户端
├── input_processor.py       # 输入处理器
├── gui_utils.py            # GUI工具类
├── exception_handler.py     # 异常处理
├── install.py              # 安装脚本
├── requirements.txt        # 依赖列表
└── secure_config/          # 配置目录
    ├── encrypted_config.json  # 加密配置文件
    ├── key.salt               # 密钥盐值
    └── backups/               # 备份目录
```

##