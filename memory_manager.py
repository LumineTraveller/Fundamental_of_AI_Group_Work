# memory_manager.py
import json
import os
import threading
import time
import queue
from datetime import datetime
from collections import defaultdict
from profile_extractor import ProfileExtractor

# 记忆管理器
class EnhancedMemoryManager:
    """增强的记忆管理系统"""
    def __init__(self, api_client, storage_dir="memory_data"):  # 修复参数名
        self.storage_dir = storage_dir
        self.user_profiles = defaultdict(dict)  # 用户画像
        self.conversation_histories = defaultdict(list)  # 对话历史
        self.profile_extractor = ProfileExtractor(api_client)  # 画像提取器
        self.lock = threading.Lock()
        self.save_queue = queue.Queue()
        self.save_thread = None
        self.running = True
        
        os.makedirs(self.storage_dir, exist_ok=True)
        self._load_data()
        self._migrate_old_data()
        
        # 加载知识分类
        self._load_categories()
        
        # 启动保存线程
        self.save_thread = threading.Thread(target=self._save_worker, daemon=True)
        self.save_thread.start()
    
    def _load_categories(self):
        """从磁盘加载知识分类"""
        category_path = os.path.join(self.storage_dir, "knowledge_categories.json")
        try:
            if os.path.exists(category_path):
                with open(category_path, "r", encoding="utf-8") as f:
                    self.predefined_categories = json.load(f)
            else:
                # 默认分类
                self.predefined_categories = {
                    "LLM": ["llm", "大语言模型", "语言模型", "gpt", "chatgpt", "deepseek"],
                    "教育": ["教育", "学校", "大学", "学院", "学习", "教学", "课程"],
                    "技术": ["技术", "编程", "代码", "开发", "软件", "硬件", "算法"],
                    "健康": ["健康", "医疗", "医生", "医院", "疾病", "治疗"],
                    "金融": ["金融", "投资", "股票", "银行", "理财", "经济"],
                    "艺术": ["艺术", "音乐", "绘画", "设计", "文学", "创作"],
                    "体育": ["体育", "运动", "比赛", "健身", "锻炼", "奥运"],
                    "游戏": ["游戏", "电竞", "玩家", "手游", "主机游戏"],
                    "旅行": ["旅行", "旅游", "景点", "酒店", "航班"],
                    "美食": ["美食", "烹饪", "餐厅", "食谱", "食材"]
                }
                self._save_categories()
        except Exception as e:
            print(f"加载知识分类失败: {e}")
            self.predefined_categories = {}
    
    def _save_categories(self):
        """保存分类到文件"""
        try:
            category_path = os.path.join(self.storage_dir, "knowledge_categories.json")
            with open(category_path, "w", encoding="utf-8") as f:
                json.dump(self.predefined_categories, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存知识分类失败: {e}")
    
    def _migrate_old_data(self):
        """迁移旧数据结构到新格式"""
        for user_id, profile in self.user_profiles.items():
            # 确保有explicit_info字段
            if "explicit_info" not in profile:
                profile["explicit_info"] = {}
            # 确保有implicit_info字段
            if "implicit_info" not in profile:
                profile["implicit_info"] = {
                    "interests": [],
                    "preferences": {},
                    "knowledge_level": {}
                }
    
    def _load_data(self):
        """从磁盘加载保存的数据"""
        # 加载用户画像
        profile_path = os.path.join(self.storage_dir, "user_profiles.json")
        if os.path.exists(profile_path):
            try:
                with open(profile_path, "r", encoding="utf-8") as f:
                    self.user_profiles = defaultdict(dict, json.load(f))
            except Exception as e:
                print(f"加载用户画像失败: {e}")
        
        # 加载对话历史
        history_path = os.path.join(self.storage_dir, "conversation_histories.json")
        if os.path.exists(history_path):
            try:
                with open(history_path, "r", encoding="utf-8") as f:
                    self.conversation_histories = defaultdict(list, json.load(f))
            except Exception as e:
                print(f"加载对话历史失败: {e}")
    
    def _save_worker(self):
        """后台保存线程"""
        while self.running:
            try:
                # 每5秒检查一次保存队列
                time.sleep(5)
                
                # 获取所有待保存数据
                save_tasks = []
                while not self.save_queue.empty():
                    save_tasks.append(self.save_queue.get())
                
                if not save_tasks:
                    continue
                
                # 批量保存
                with self.lock:
                    # 保存用户画像
                    profile_path = os.path.join(self.storage_dir, "user_profiles.json")
                    with open(profile_path, "w", encoding="utf-8") as f:
                        json.dump(dict(self.user_profiles), f, ensure_ascii=False, indent=2)
                    
                    # 保存对话历史
                    history_path = os.path.join(self.storage_dir, "conversation_histories.json")
                    with open(history_path, "w", encoding="utf-8") as f:
                        json.dump(dict(self.conversation_histories), f, ensure_ascii=False, indent=2)
                    
                    print(f"保存了 {len(save_tasks)} 项更新")
                
                # 标记任务完成
                for _ in save_tasks:
                    self.save_queue.task_done()
                    
            except Exception as e:
                print(f"保存线程错误: {e}")
    
    def schedule_save(self):
        """安排异步保存"""
        self.save_queue.put(1)
    
    def shutdown(self):
        """关闭记忆管理器"""
        self.running = False
        if self.save_thread and self.save_thread.is_alive():
            self.save_thread.join(timeout=5.0)
    
    def get_user_profile(self, user_id):
        """获取用户画像（确保有默认结构）"""
        profile = self.user_profiles.get(user_id, {})
        
        # 确保有基本结构
        if "explicit_info" not in profile:
            profile["explicit_info"] = {}
        if "implicit_info" not in profile:
            profile["implicit_info"] = {
                "interests": [],
                "preferences": {},
                "knowledge_level": {}
            }
        
        return profile
    
    def get_profile_prompt(self, user_id):
        """生成用于提示工程的用户画像摘要"""
        profile = self.get_user_profile(user_id)
        if not profile:
            return ""
        
        prompt_lines = []
        
        # 显式信息
        explicit_info = profile.get("explicit_info", {})
        if explicit_info:
            explicit = ", ".join(
                [f"{k}: {v}" for k, v in explicit_info.items()]
            )
            prompt_lines.append(f"用户基本信息: {explicit}")
        
        # 隐式信息
        implicit_info = profile.get("implicit_info", {})
        if implicit_info:
            # 去重兴趣列表
            interests = list(set(implicit_info.get("interests", [])))
            if interests:
                prompt_lines.append(f"用户兴趣: {', '.join(interests)}")
            
            preferences = implicit_info.get("preferences", {})
            if preferences:
                # 去重偏好值
                unique_prefs = {}
                for k, v in preferences.items():
                    if isinstance(v, list):
                        unique_prefs[k] = list(set(v))
                    else:
                        unique_prefs[k] = v
                
                prefs = ", ".join(
                    [f"{k}: {v}" for k, v in unique_prefs.items()]
                )
                prompt_lines.append(f"沟通偏好: {prefs}")
            
            knowledge_level = implicit_info.get("knowledge_level", {})
            if knowledge_level:
                # 去重知识水平
                unique_knowledge = {}
                for k, v in knowledge_level.items():
                    if isinstance(v, list):
                        unique_knowledge[k] = list(set(v))
                    else:
                        unique_knowledge[k] = v
                
                knowledge = ", ".join(
                    [f"{k}: {v}" for k, v in unique_knowledge.items()]
                )
                prompt_lines.append(f"知识水平: {knowledge}")
        
        return "\n".join(prompt_lines) if prompt_lines else ""
    
    def get_conversation_history(self, conversation_id, max_messages=20):
        """获取最近的对话历史（限制数量）"""
        history = self.conversation_histories.get(conversation_id, [])
        # 只返回最近的消息
        return history[-max_messages:].copy()
    
    def add_to_conversation_history(self, conversation_id, message):
        """添加消息到对话历史"""
        with self.lock:
            if conversation_id not in self.conversation_histories:
                self.conversation_histories[conversation_id] = []
            
            # 添加到历史
            self.conversation_histories[conversation_id].append(message)
            
            # 限制历史长度
            if len(self.conversation_histories[conversation_id]) > 100:
                self.conversation_histories[conversation_id] = self.conversation_histories[conversation_id][-100:]
            
            # 安排异步保存
            self.schedule_save()
    
    def extract_and_update_profile(self, conversation_id, user_id):
        """使用大模型提取并更新用户画像 - 改进合并逻辑"""
        try:
            history = self.get_conversation_history(conversation_id, max_messages=20)
            if not history:
                return self.get_user_profile(user_id)
            
            # 使用大模型提取画像
            new_profile = self.profile_extractor.extract_profile(history)
            if not new_profile:
                return self.get_user_profile(user_id)
            
            # 合并到现有画像
            with self.lock:
                profile = self.get_user_profile(user_id)
                
                # 合并显式信息
                explicit_info = new_profile.get("explicit_info", {})
                if explicit_info:
                    profile["explicit_info"].update(explicit_info)
                
                # 合并隐式信息
                implicit_info = new_profile.get("implicit_info", {})
                if implicit_info:
                    # 合并兴趣（关键改进）
                    new_interests = implicit_info.get("interests", [])
                    existing_interests = set(profile["implicit_info"].get("interests", []))
                    
                    # 标准化并合并兴趣
                    for interest in new_interests:
                        # 标准化兴趣名称
                        normalized_interest = self._normalize_interest(interest)
                        if normalized_interest:
                            existing_interests.add(normalized_interest)
                    
                    profile["implicit_info"]["interests"] = list(existing_interests)
                    
                    # 合并偏好
                    preferences = implicit_info.get("preferences", {})
                    for key, value in preferences.items():
                        # 如果是列表类型，合并并去重
                        if key in profile["implicit_info"]["preferences"]:
                            if isinstance(value, list) and isinstance(profile["implicit_info"]["preferences"][key], list):
                                combined = set(profile["implicit_info"]["preferences"][key]) | set(value)
                                profile["implicit_info"]["preferences"][key] = list(combined)
                            else:
                                profile["implicit_info"]["preferences"][key] = value
                        else:
                            profile["implicit_info"]["preferences"][key] = value
                    
                    # 合并知识水平（关键改进）
                    new_knowledge = implicit_info.get("knowledge_level", {})
                    existing_knowledge = profile["implicit_info"].get("knowledge_level", {})
                    
                    # 创建一个标准化知识领域字典
                    normalized_knowledge = {}
                    
                    # 首先标准化新知识领域
                    for domain, level in new_knowledge.items():
                        normalized_domain = self._normalize_knowledge_area(domain)
                        if normalized_domain:
                            normalized_knowledge[normalized_domain] = level
                    
                    # 然后标准化现有知识领域
                    for domain, level in existing_knowledge.items():
                        normalized_domain = self._normalize_knowledge_area(domain)
                        if normalized_domain:
                            # 合并水平描述
                            if normalized_domain in normalized_knowledge:
                                # 如果领域已存在，合并水平描述
                                normalized_knowledge[normalized_domain] = self._merge_knowledge_levels(
                                    normalized_knowledge[normalized_domain], 
                                    level
                                )
                            else:
                                normalized_knowledge[normalized_domain] = level
                    
                    profile["implicit_info"]["knowledge_level"] = normalized_knowledge
                
                profile["last_updated"] = datetime.now().isoformat()
                self.user_profiles[user_id] = profile
                self.schedule_save()
            
            return profile
        except Exception as e:
            print(f"AI画像更新失败: {e}")
            return self.get_user_profile(user_id)
    
    def _normalize_knowledge_area(self, area):
        """智能标准化知识领域名称"""
        if not area:
            return None
        
        # 1. 首先检查预定义分类
        area_lower = area.lower()
        for category, keywords in self.predefined_categories.items():
            if any(keyword in area_lower for keyword in keywords):
                return category
        
        # 2. 使用大模型进行智能分类（当本地规则不足时）
        return self._classify_with_ai(area)
    
    def _classify_with_ai(self, area):
        """使用大模型对知识领域进行分类"""
        if not area or len(area) < 2:
            return area
        
        try:
            # 创建分类提示
            prompt = f"""
请将以下知识领域分类到最合适的类别中。如果没有合适类别，请创建新类别。
可用类别: {', '.join(self.predefined_categories.keys())}

知识领域: "{area}"
分类结果（只返回类别名称）:
"""
            
            # 使用大模型生成分类
            response = self.profile_extractor.client.generate(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
                top_p=0.9,
                max_tokens=50
            )
            
            # 提取分类结果
            category = response.strip()
            
            # 验证结果是否为有效类别
            valid_categories = list(self.predefined_categories.keys())
            if category not in valid_categories:
                # 如果模型创建了新类别，添加到预定义分类
                self._add_new_category(category, [area])
                return category
            
            return category
        except Exception as e:
            print(f"AI分类失败: {e}")
            # 分类失败时返回原始值
            return area
    
    def _add_new_category(self, category, keywords):
        """添加新分类到预定义类别"""
        if category not in self.predefined_categories:
            self.predefined_categories[category] = keywords
            # 保存更新到文件
            self._save_categories()
    
    def _normalize_interest(self, interest):
        """标准化兴趣名称"""
        if not interest:
            return None
        
        # 基本清理
        interest = interest.strip().lower()
        
        # 常见兴趣的同义词映射
        synonym_map = {
            "人工智能": ["ai", "人工智能", "机器智能"],
            "编程": ["编程", "写代码", "软件开发", "编码"],
            "阅读": ["读书", "阅读", "看小说"],
            "运动": ["锻炼", "健身", "运动", "体育活动"],
            "旅游": ["旅行", "旅游", "观光"],
            "电影": ["看电影", "影视", "电影院"],
            "音乐": ["听歌", "音乐", "演唱会"],
            "游戏": ["打游戏", "电子游戏", "网游", "手游"],
            "烹饪": ["做饭", "烹饪", "烘焙"],
            "摄影": ["拍照", "摄影", "摄像"]
        }
        
        # 查找同义词
        for standard_interest, synonyms in synonym_map.items():
            if interest in synonyms or any(syn in interest for syn in synonyms):
                return standard_interest
        
        # 如果没有匹配的同义词，返回原始值
        return interest.capitalize()
    
    def _merge_knowledge_levels(self, level1, level2):
        """合并两个知识水平描述"""
        # 如果相同，直接返回
        if level1 == level2:
            return level1
        
        # 提取水平关键词
        level_keywords = {
            "初级": ["初级", "入门", "基础", "新手"],
            "中级": ["中级", "中等", "熟练", "有一定经验"],
            "高级": ["高级", "专家", "精通", "深入"]
        }
        
        # 确定每个描述的水平
        def get_level_score(desc):
            desc_lower = desc.lower()
            for level, keywords in level_keywords.items():
                if any(kw in desc_lower for kw in keywords):
                    return level
            return "未知"
        
        level1_score = get_level_score(level1)
        level2_score = get_level_score(level2)
        
        # 合并策略：取最高水平
        level_order = ["未知", "初级", "中级", "高级"]
        if level_order.index(level1_score) > level_order.index(level2_score):
            return level1
        return level2