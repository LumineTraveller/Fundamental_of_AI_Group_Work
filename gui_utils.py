import tkinter as tk
from tkinter import scrolledtext

class GUIUtils:
    """GUI实用工具类"""
    @staticmethod
    def create_scrolled_text(parent, **kwargs):
        """创建滚动文本框"""
        text_widget = scrolledtext.ScrolledText(
            parent,
            wrap=tk.WORD,
            **kwargs
        )
        return text_widget
    
    @staticmethod
    def display_message(text_widget, role, text, model_name="", tags_config=None):
        """在文本框中显示消息"""
        if tags_config is None:
            tags_config = {
                "user": {"foreground": "blue"},
                "assistant": {"foreground": "green"},
                "system": {"foreground": "red", "font": ("Helvetica", 10, "italic")}
            }
        
        text_widget.config(state='normal')
        
        # 应用标签配置
        for tag, config in tags_config.items():
            if not text_widget.tag_cget(tag, "foreground"):
                text_widget.tag_configure(tag, **config)
        
        # 显示消息
        if role == "user":
            text_widget.insert(tk.END, f"You:\n", "user")
            text_widget.insert(tk.END, f"{text}\n\n")
        elif role == "assistant":
            header = f"{model_name}:\n" if model_name else "Assistant:\n"
            text_widget.insert(tk.END, header, "assistant")
            text_widget.insert(tk.END, f"{text}\n\n")
        elif role == "system":
            text_widget.insert(tk.END, f"System: {text}\n\n", "system")
            
        text_widget.config(state='disabled')
        text_widget.yview(tk.END)
    
    @staticmethod
    def display_streaming_chunk(text_widget, chunk, model_name=""):
        """显示流式响应的单个块 - 修复顺序问题"""
        text_widget.config(state='normal')
        
        # 直接插入到文本末尾
        text_widget.insert(tk.END, chunk)
        text_widget.config(state='disabled')
        text_widget.yview(tk.END)