#main_gui.py
import tkinter as tk
from tkinter import ttk, messagebox
import threading
import queue
import os
from dotenv import load_dotenv
from api_clients import DeepSeekClient, QwenClient
from input_processor import InputProcessor
from gui_utils import GUIUtils
from exception_handler import StructuredOutputHandler

class LLMChatGUI:
    def __init__(self, master):
        self.master = master
        master.title("LLM API Chat")
        master.geometry("1200x800")

        # 加载环境变量
        load_dotenv()
        self.deepseek_api_key = tk.StringVar(value=os.getenv("DEEPSEEK_API_KEY", ""))
        self.qwen_api_key = tk.StringVar(value=os.getenv("DASHSCOPE_API_KEY", ""))

        # 输入处理器
        self.input_processor = InputProcessor()

        # --- 状态管理 ---
        self.conversations = {}
        self.current_chat_id = None
        self.response_queue = queue.Queue()
        self.active_streams = {}  # 跟踪活动流: {model_name: stream_thread}

        # --- 创建主框架 ---
        main_frame = ttk.Frame(master, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 创建左右两个窗格
        paned_window = ttk.PanedWindow(main_frame, orient=tk.HORIZONTAL)
        paned_window.pack(fill=tk.BOTH, expand=True)

        # --- 左侧面板 (对话列表和设置) ---
        left_pane = ttk.Frame(paned_window, width=300)
        paned_window.add(left_pane, weight=1)

        # --- 右侧面板 (聊天窗口和输入框) ---
        right_pane = ttk.Frame(paned_window)
        paned_window.add(right_pane, weight=4)

        # --- 填充左侧面板 ---
        self._create_left_pane(left_pane)

        # --- 填充右侧面板 ---
        self._create_right_pane(right_pane)
        
        # --- 初始化 ---
        self._create_new_chat()
        self.master.after(100, self._check_queue)
        self.master.protocol("WM_DELETE_WINDOW", self._on_close)

    def _create_left_pane(self, parent):
        # 对话管理
        chat_list_frame = ttk.LabelFrame(parent, text="Conversations", padding="10")
        chat_list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.chat_listbox = tk.Listbox(chat_list_frame, exportselection=False)
        self.chat_listbox.pack(fill=tk.BOTH, expand=True)
        self.chat_listbox.bind("<<ListboxSelect>>", self._on_chat_select)

        btn_frame = ttk.Frame(chat_list_frame)
        btn_frame.pack(fill=tk.X, pady=5)
        
        new_chat_btn = ttk.Button(btn_frame, text="New Chat", command=self._create_new_chat)
        new_chat_btn.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)
        
        delete_chat_btn = ttk.Button(btn_frame, text="Delete Chat", command=self._delete_chat)
        delete_chat_btn.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)

        # API Key 设置
        api_key_frame = ttk.LabelFrame(parent, text="API Keys", padding="10")
        api_key_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(api_key_frame, text="DeepSeek Key:").pack(anchor='w')
        deepseek_entry = ttk.Entry(api_key_frame, textvariable=self.deepseek_api_key, show="*")
        deepseek_entry.pack(fill=tk.X, pady=2)

        ttk.Label(api_key_frame, text="Qwen Key:").pack(anchor='w')
        qwen_entry = ttk.Entry(api_key_frame, textvariable=self.qwen_api_key, show="*")
        qwen_entry.pack(fill=tk.X, pady=2)
        
        # 参数调整
        params_frame = ttk.LabelFrame(parent, text="Parameters", padding="10")
        params_frame.pack(fill=tk.X, padx=5, pady=5)

        self.temp_var = tk.DoubleVar(value=0.7)
        ttk.Label(params_frame, text=f"Temperature:").grid(row=0, column=0, sticky='w')
        temp_scale = ttk.Scale(params_frame, from_=0.0, to=1.0, variable=self.temp_var, orient=tk.HORIZONTAL)
        temp_scale.grid(row=0, column=1, sticky='ew')

        self.top_p_var = tk.DoubleVar(value=0.9)
        ttk.Label(params_frame, text=f"Top_p:").grid(row=1, column=0, sticky='w')
        top_p_scale = ttk.Scale(params_frame, from_=0.0, to=1.0, variable=self.top_p_var, orient=tk.HORIZONTAL)
        top_p_scale.grid(row=1, column=1, sticky='ew')
        
        self.max_tokens_var = tk.IntVar(value=2048)
        ttk.Label(params_frame, text="Max Tokens:").grid(row=2, column=0, sticky='w')
        max_tokens_entry = ttk.Entry(params_frame, textvariable=self.max_tokens_var, width=8)
        max_tokens_entry.grid(row=2, column=1, sticky='w')
        
        params_frame.columnconfigure(1, weight=1)

    def _create_right_pane(self, parent):
        # 模型选择
        model_frame = ttk.LabelFrame(parent, text="Model Selection", padding="10")
        model_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.use_deepseek = tk.BooleanVar(value=True)
        self.use_qwen = tk.BooleanVar(value=False)
        
        ttk.Checkbutton(model_frame, text="DeepSeek", variable=self.use_deepseek).pack(side=tk.LEFT, padx=10)
        ttk.Checkbutton(model_frame, text="Qwen (Parallel)", variable=self.use_qwen).pack(side=tk.LEFT, padx=10)

        # 聊天显示区域 - 改为可分割的窗格
        chat_display_frame = ttk.Frame(parent)
        chat_display_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 创建可调整的分割窗格
        self.paned_window = ttk.PanedWindow(chat_display_frame, orient=tk.HORIZONTAL)
        self.paned_window.pack(fill=tk.BOTH, expand=True)
        
        # 左侧面板 (DeepSeek)
        self.left_frame = ttk.Frame(self.paned_window)
        self.paned_window.add(self.left_frame, weight=1)
        
        self.deepseek_display = GUIUtils.create_scrolled_text(self.left_frame)
        self.deepseek_display.pack(fill=tk.BOTH, expand=True)
        self.deepseek_display.tag_config("user", foreground="blue")
        self.deepseek_display.tag_config("assistant", foreground="green")
        self.deepseek_display.tag_config("system", foreground="red", font=("Helvetica", 10, "italic"))
        
        # 右侧面板 (Qwen)
        self.right_frame = ttk.Frame(self.paned_window)
        self.paned_window.add(self.right_frame, weight=1)
        
        self.qwen_display = GUIUtils.create_scrolled_text(self.right_frame)
        self.qwen_display.pack(fill=tk.BOTH, expand=True)
        self.qwen_display.tag_config("user", foreground="blue")
        self.qwen_display.tag_config("assistant", foreground="purple")  # 使用不同颜色区分
        self.qwen_display.tag_config("system", foreground="red", font=("Helvetica", 10, "italic"))
        
        # 初始隐藏Qwen面板
        self.paned_window.forget(1)  # 隐藏右侧面板
        
        # 输入区域
        input_frame = ttk.Frame(parent, padding="5")
        input_frame.pack(fill=tk.X, padx=5, pady=5)

        self.input_text = tk.Text(input_frame, height=4)
        self.input_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.input_text.bind("<Return>", self._on_enter_key)

        self.send_button = ttk.Button(input_frame, text="Send", command=self._send_message)
        self.send_button.pack(side=tk.RIGHT, padx=5, fill=tk.Y)

    def _on_enter_key(self, event):
        """处理回车键事件，支持Shift+Enter换行"""
        if event.state & 0x0001:  # Shift键按下
            self.input_text.insert(tk.INSERT, "\n")
            return "break"  # 阻止默认行为
        else:
            self._send_message()
            return "break"  # 阻止默认行为

    def _update_display_layout(self):
        """根据选择的模型更新显示布局"""
        use_deepseek = self.use_deepseek.get()
        use_qwen = self.use_qwen.get()
        
        # 获取当前窗格中的所有子窗口
        panes = self.paned_window.panes()
        
        # 移除所有现有窗格
        for pane in panes:
            self.paned_window.forget(pane)
        
        if use_deepseek and use_qwen:
            # 同时显示两个模型
            self.paned_window.add(self.left_frame, weight=1)
            self.paned_window.add(self.right_frame, weight=1)
        elif use_deepseek:
            # 只显示DeepSeek
            self.paned_window.add(self.left_frame, weight=1)
        elif use_qwen:
            # 只显示Qwen
            self.paned_window.add(self.right_frame, weight=1)
    
    def _display_message(self, role, text, model_name=""):
        """显示完整消息到正确的面板"""
        if role == "user" or role == "system":
            # 用户和系统消息同时显示在两个面板
            GUIUtils.display_message(
                self.deepseek_display, 
                role, 
                text, 
                model_name
            )
            GUIUtils.display_message(
                self.qwen_display, 
                role, 
                text, 
                model_name
            )
        elif role == "assistant":
            # 助手消息显示在对应模型的面板
            if model_name == "DeepSeek":
                GUIUtils.display_message(
                    self.deepseek_display, 
                    role, 
                    text, 
                    model_name
                )
            elif model_name == "Qwen":
                GUIUtils.display_message(
                    self.qwen_display, 
                    role, 
                    text, 
                    model_name
                )

    def _display_streaming_chunk(self, model_name, chunk):
        """显示流式响应的单个块到正确面板"""
        if model_name == "DeepSeek":
            GUIUtils.display_streaming_chunk(
                self.deepseek_display, 
                chunk, 
                model_name
            )
        elif model_name == "Qwen":
            GUIUtils.display_streaming_chunk(
                self.qwen_display, 
                chunk, 
                model_name
            )

    def _send_message(self):
        
        self._update_display_layout()
        user_input = self.input_text.get("1.0", tk.END).strip()
        if not user_input:
            return

        # 输入预处理
        processed_input = self.input_processor.process(user_input)
        if processed_input != user_input:
            self._display_message("system", "输入已进行安全处理")

        selected_models = []
        if self.use_deepseek.get():
            selected_models.append("DeepSeek")
        if self.use_qwen.get():
            selected_models.append("Qwen")

        if not selected_models:
            messagebox.showerror("Error", "请至少选择一个模型。")
            return

        self._display_message("user", processed_input)
        self.conversations[self.current_chat_id].append({"role": "user", "content": processed_input})
        self.input_text.delete("1.0", tk.END)

        # 禁用输入和按钮
        self.send_button.config(state='disabled')
        self.input_text.config(state='disabled')

        # 在新线程中调用API
        threading.Thread(
            target=self._get_responses_thread, 
            args=(selected_models, processed_input), 
            daemon=True
        ).start()

    def _get_responses_thread(self, models, user_input):
        history = self.conversations[self.current_chat_id]
        params = {
            "temperature": self.temp_var.get(),
            "top_p": self.top_p_var.get(),
            "max_tokens": self.max_tokens_var.get()
        }

        # 创建每个模型的响应线程
        threads = []
        self.active_streams = {}
        
        for model in models:
            # 为每个模型创建线程
            thread = threading.Thread(
                target=self._call_api_stream, 
                args=(model, history.copy(), params),
                daemon=True
            )
            threads.append(thread)
            self.active_streams[model] = thread
            thread.start()

        # 等待所有线程完成
        for thread in threads:
            thread.join()
        
        # 所有响应接收完毕，恢复输入
        self.response_queue.put(("DONE", None))

    def _call_api_stream(self, model_name, history, params):
        """调用API流式接口并处理响应"""
        # 在流式输出开始前添加助手消息占位符
        self.response_queue.put(("assistant_start", model_name))
        
        try:
            # 获取API客户端
            if model_name == "DeepSeek":
                key = self.deepseek_api_key.get()
                if not key:
                    self.response_queue.put(("system", f"{model_name} API Key 缺失!"))
                    return
                client = DeepSeekClient(key)
            elif model_name == "Qwen":
                key = self.qwen_api_key.get()
                if not key:
                    self.response_queue.put(("system", f"{model_name} API Key 缺失!"))
                    return
                client = QwenClient(key)
            else:
                return

            full_response = ""
            
            # 定义回调函数处理流式响应块
            def callback(chunk):
                nonlocal full_response
                # 处理结构化输出错误
                processed_chunk = StructuredOutputHandler.handle_api_output(chunk)
                full_response += processed_chunk
                # 直接发送chunk内容
                self.response_queue.put(("chunk", (model_name, processed_chunk)))

            # 调用流式生成方法
            client.generate_stream(
                messages=history,
                callback=callback,
                **params
            )
            
            # 将完整响应添加到对话历史
            if not full_response.startswith("API错误"):
                self.conversations[self.current_chat_id].append({
                    "role": "assistant", 
                    "content": full_response,
                    "model": model_name
                })
        except Exception as e:
            self.response_queue.put(("system", f"{model_name} 错误: {str(e)}"))
        finally:
            # 在流式输出结束后添加换行符，确保用户消息在新行开始
            self.response_queue.put(("chunk", (model_name, "\n\n")))
            
            # 从活动流中移除
            if model_name in self.active_streams:
                del self.active_streams[model_name]

    def _check_queue(self):
        """从队列中获取响应并更新GUI"""
        try:
            while True:
                item = self.response_queue.get_nowait()
                if item[0] == "DONE":
                    # 所有响应接收完毕，恢复输入
                    self.send_button.config(state='normal')
                    self.input_text.config(state='normal')
                    self.input_text.focus_set()
                elif item[0] == "system":
                    self._display_message("system", item[1])
                elif item[0] == "assistant_start":
                    # 助手消息开始，添加标题
                    model_name = item[1]
                    self._display_message("assistant", "", model_name)  # 只显示标题
                elif item[0] == "chunk":
                    model_name, chunk = item[1]
                    self._display_streaming_chunk(model_name, chunk)

        except queue.Empty:
            pass
        
        self.master.after(50, self._check_queue)  # 更频繁地检查队列以获得流畅体验

    # --- 对话管理方法 ---
    def _create_new_chat(self):
        """创建新的对话"""
        chat_id = f"Chat {len(self.conversations) + 1}"
        self.conversations[chat_id] = []  # 创建一个空的消息列表
        self.chat_listbox.insert(tk.END, chat_id)
        self.chat_listbox.selection_clear(0, tk.END)
        self.chat_listbox.selection_set(tk.END)
        self.chat_listbox.activate(tk.END)
        self._load_chat_history(chat_id)

    def _delete_chat(self):
        """删除当前选中的对话"""
        try:
            selected_index = self.chat_listbox.curselection()[0]
            chat_id = self.chat_listbox.get(selected_index)
            
            if len(self.conversations) <= 1:
                messagebox.showwarning("Warning", "无法删除最后一个对话。")
                return

            if messagebox.askyesno("确认删除", f"确定要删除 '{chat_id}' 吗?"):
                del self.conversations[chat_id]
                self.chat_listbox.delete(selected_index)
                
                # 自动选择一个新对话
                if selected_index > 0:
                    self.chat_listbox.selection_set(selected_index - 1)
                else:
                    self.chat_listbox.selection_set(0)
                
                self._on_chat_select(None)  # 手动触发加载
        except IndexError:
            pass  # 没有选择任何项目

    def _on_chat_select(self, event):
        """处理对话选择事件"""
        try:
            # 避免因删除项导致的空选择事件触发错误
            if not self.chat_listbox.curselection():
                return
            selected_index = self.chat_listbox.curselection()[0]
            chat_id = self.chat_listbox.get(selected_index)
            if chat_id != self.current_chat_id:
                self._load_chat_history(chat_id)
        except IndexError:
            pass  # 如果列表为空，会发生索引错误

    def _load_chat_history(self, chat_id):
        """加载指定对话的历史记录"""
        self.current_chat_id = chat_id
        
        # 清空两个显示区域
        self.deepseek_display.config(state='normal')
        self.deepseek_display.delete("1.0", tk.END)
        
        self.qwen_display.config(state='normal')
        self.qwen_display.delete("1.0", tk.END)
        
        history = self.conversations.get(chat_id, [])
        for message in history:
            role = message["role"]
            content = message["content"]
            model_name = message.get("model", "")
            
            # 根据消息类型和模型显示到正确面板
            if role == "user" or role == "system":
                GUIUtils.display_message(self.deepseek_display, role, content, model_name)
                GUIUtils.display_message(self.qwen_display, role, content, model_name)
            elif role == "assistant":
                if model_name == "DeepSeek":
                    GUIUtils.display_message(self.deepseek_display, role, content, model_name)
                elif model_name == "Qwen":
                    GUIUtils.display_message(self.qwen_display, role, content, model_name)
        
        self.deepseek_display.config(state='disabled')
        self.deepseek_display.yview(tk.END)
        
        self.qwen_display.config(state='disabled')
        self.qwen_display.yview(tk.END)
        
        # 确保输入框可用
        self.send_button.config(state='normal')
        self.input_text.config(state='normal')
        self.input_text.focus_set()
    
    def _on_close(self):
        """窗口关闭时的处理"""
        self.master.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = LLMChatGUI(root)
    root.mainloop()