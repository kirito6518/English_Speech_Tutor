import random
import re
from typing import List, Dict
from openai import OpenAI
import logging
import traceback
import pymysql
import pymysql.cursors

# 设置日志记录
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class HostAgent:
    def __init__(self, keywords):
        self.keywords = keywords
        self.current_keyword = None
        self.first_round = True
        self.index = 0
        self.used_keywords = []  # 记录最近使用过的关键字
        self.max_history = 5     # 记录最近使用过的关键字数量

    def give_keyword(self):
        if self.first_round:
            # 第一轮按顺序选择
            if self.index < len(self.keywords):
                self.current_keyword = self.keywords[self.index]
                self.index += 1
                
                # 记录使用过的关键字
                self._update_used_keywords(self.current_keyword)
                
                # 检查是否完成第一轮
                if self.index >= len(self.keywords):
                    self.first_round = False
        else:
            # 后续轮次随机选择，但避免选择最近使用过的关键字
            available_keywords = [k for k in self.keywords if k not in self.used_keywords]
            
            # 如果所有关键字都被使用过，则重置使用记录
            if not available_keywords:
                logger.debug("所有关键字都被使用过，重置使用记录")
                self.used_keywords = self.used_keywords[-2:] if len(self.used_keywords) >= 2 else []
                available_keywords = [k for k in self.keywords if k not in self.used_keywords]
            
            self.current_keyword = random.choice(available_keywords)
            self._update_used_keywords(self.current_keyword)
            
        logger.debug(f"选择关键字: {self.current_keyword}, 最近使用过的关键字: {self.used_keywords}")
        return self.current_keyword
    
    def _update_used_keywords(self, keyword):
        """更新最近使用过的关键字列表"""
        if keyword in self.used_keywords:
            self.used_keywords.remove(keyword)
        self.used_keywords.append(keyword)
        
        # 保持列表长度不超过max_history
        if len(self.used_keywords) > self.max_history:
            self.used_keywords = self.used_keywords[-self.max_history:]

class JudgeAgent:
    def __init__(self):
        pass

    def judge(self, sentence, keyword):
        return keyword in sentence

class FeiHuaLingService:
    # 默认关键字列表
    DEFAULT_KEYWORDS = ['月','花', '山', '水', '树', '风', '雨', '云', '天', '雾', '露', '霜', '雪', '声', '草', '木', '石', '鸟', '虫']
    
    # 关卡配置
    LEVEL_CONFIG = {
        'answers_per_level': 3,  # 每个关卡需要答对的次数
        'max_level': 5           # 最大关卡数
    }
    
    # 数据库连接配置
    DB_CONFIG = {
        'host': 'localhost',
        'user': 'sxy',  # 按实际用户名修改
        'password': 'cfyxYDz62eTrxBPG',  # 按实际密码修改，留空表示无密码
        'db': 'sxy',
        'charset': 'utf8mb4',
        'cursorclass': pymysql.cursors.DictCursor
    }
    
    # DeepSeek API配置
    API_KEY = "sk-c67e01d8ca3c4a9e96946055133b662a"
    BASE_URL = "https://api.deepseek.com"
    
    @staticmethod
    def get_db_connection():
        """获取数据库连接"""
        try:
            connection = pymysql.connect(**FeiHuaLingService.DB_CONFIG)
            return connection
        except Exception as e:
            logger.error(f"数据库连接失败: {str(e)}")
            return None
    
    @staticmethod
    def get_poems_by_keyword(keyword):
        """从数据库中查询包含关键字的诗句"""
        connection = FeiHuaLingService.get_db_connection()
        if not connection:
            logger.error("无法获取数据库连接")
            return []
            
        try:
            with connection.cursor() as cursor:
                # 查询包含关键字的诗句
                sql = "SELECT id, poem_id, line_number, content FROM poem_lines WHERE content LIKE %s"
                cursor.execute(sql, f"%{keyword}%")
                result = cursor.fetchall()
                
                # 提取诗句内容
                poems = [row['content'] for row in result]
                logger.info(f"从数据库查询到{len(poems)}条包含'{keyword}'的诗句")
                return poems
        except Exception as e:
            logger.error(f"查询数据库失败: {str(e)}")
            return []
        finally:
            connection.close()
    
    @staticmethod
    def create_game(keywords=None):
        """创建新游戏，返回一个游戏会话ID和初始关键字"""
        try:
            logger.info("开始创建游戏")
            if keywords is None:
                logger.debug("使用默认关键字列表")
                keywords = FeiHuaLingService.DEFAULT_KEYWORDS
            else:
                logger.debug(f"使用自定义关键字列表: {keywords}")
                
            # 创建主持人代理
            logger.debug("创建主持人代理")
            host_agent = HostAgent(keywords)
            
            # 创建裁判代理
            logger.debug("创建裁判代理")
            judge_agent = JudgeAgent()
            
            # 生成一个随机的会话ID
            session_id = f"game_{random.randint(1000, 9999)}"
            logger.debug(f"生成会话ID: {session_id}")
            
            # 保存游戏状态
            logger.debug("保存游戏状态")
            game_state = {
                'host_agent': host_agent,
                'judge_agent': judge_agent,
                'dialogues': [],
                'current_keyword': host_agent.give_keyword(),
                'current_level': 1,             # 当前关卡
                'correct_answers_count': 0      # 当前关卡已答对次数
            }
            
            # 初始化游戏存储
            logger.debug("初始化游戏存储")
            if not hasattr(FeiHuaLingService, 'games'):
                logger.debug("创建games类变量")
                FeiHuaLingService.games = {}
            
            FeiHuaLingService.games[session_id] = game_state
            logger.info(f"游戏创建成功，会话ID: {session_id}, 当前关卡: 1, 当前关键字: {game_state['current_keyword']}")
            
            return {
                'session_id': session_id,
                'level': 1,
                'keyword': game_state['current_keyword']
            }
        except Exception as e:
            error_message = str(e)
            stack_trace = traceback.format_exc()
            logger.error(f"创建游戏时发生错误: {error_message}")
            logger.error(f"堆栈跟踪: {stack_trace}")
            raise
    
    @staticmethod
    def submit_answer(session_id, user_response):
        """提交用户的回答并获取AI的响应"""
        try:
            logger.info(f"提交回答，会话ID: {session_id}")
            if not hasattr(FeiHuaLingService, 'games'):
                logger.error("游戏存储未初始化")
                return {'error': '游戏会话不存在'}
                
            if session_id not in FeiHuaLingService.games:
                logger.error(f"找不到会话ID: {session_id}")
                return {'error': '游戏会话不存在'}
                
            game_state = FeiHuaLingService.games[session_id]
            
            # 获取当前关键字和关卡信息
            current_keyword = game_state['current_keyword']
            current_level = game_state['current_level']
            correct_answers_count = game_state['correct_answers_count']
            
            # 判断用户回答是否有效
            logger.debug("判断用户回答是否有效")
            is_valid = game_state['judge_agent'].judge(user_response, current_keyword)
            logger.debug(f"用户回答是否有效: {is_valid}")
            
            # 记录用户对话
            logger.debug(f"记录用户对话: {user_response}")
            game_state['dialogues'].append({"role": "user", "content": user_response})
            
            if not is_valid:
                logger.info("用户回答无效")
                return {
                    'status': 'failed',
                    'message': f'你的回答中没有包含关键字"{current_keyword}"',
                    'level': current_level,
                    'keyword': current_keyword,
                    'correct_answers': correct_answers_count,
                    'required_answers': FeiHuaLingService.LEVEL_CONFIG['answers_per_level']
                }
            
            # 获取AI响应
            logger.info("获取AI响应")
            ai_response = FeiHuaLingService.get_ai_response(
                current_keyword, 
                user_response, 
                game_state['dialogues']
            )
            
            # 判断AI响应是否有效
            logger.debug("判断AI响应是否有效")
            ai_valid = game_state['judge_agent'].judge(ai_response, current_keyword)
            logger.debug(f"AI响应是否有效: {ai_valid}")
            
            # 将AI响应添加到对话历史中
            logger.debug(f"记录AI对话: {ai_response}")
            game_state['dialogues'].append({"role": "assistant", "content": ai_response})
            
            # 判断是否需要更新关卡
            level_changed = False
            new_keyword = current_keyword
            
            # 如果用户回答正确且AI回答有效，增加正确答题计数
            if is_valid and ai_valid:
                game_state['correct_answers_count'] += 1
                logger.debug(f"答对计数增加，当前关卡({current_level})已答对{game_state['correct_answers_count']}次")
                
                # 检查是否达到关卡升级条件
                if game_state['correct_answers_count'] >= FeiHuaLingService.LEVEL_CONFIG['answers_per_level']:
                    # 更新关卡和关键字
                    next_level = current_level + 1
                    
                    # 检查是否达到最大关卡数
                    if next_level > FeiHuaLingService.LEVEL_CONFIG['max_level']:
                        logger.info(f"已达到最大关卡({FeiHuaLingService.LEVEL_CONFIG['max_level']})，游戏结束")
                        level_changed = True
                        game_completed = True
                    else:
                        logger.info(f"升级到下一关，当前关卡: {current_level} -> {next_level}")
                        game_state['current_level'] = next_level
                        game_state['correct_answers_count'] = 0  # 重置答对计数
                        new_keyword = game_state['host_agent'].give_keyword()
                        game_state['current_keyword'] = new_keyword
                        level_changed = True
                        game_completed = False
                        
                        logger.info(f"关卡更新: {current_level} -> {next_level}, 关键字更新: {current_keyword} -> {new_keyword}")
            
            # 保存更新后的游戏状态
            FeiHuaLingService.games[session_id] = game_state
            logger.debug(f"更新后的对话历史长度: {len(game_state['dialogues'])}")
            
            # 构建结果
            result = {
                'status': 'success' if ai_valid else 'ai_failed',
                'ai_response': ai_response,
                'level': game_state['current_level'],
                'keyword': current_keyword,
                'correct_answers': game_state['correct_answers_count'],
                'required_answers': FeiHuaLingService.LEVEL_CONFIG['answers_per_level'],
                'level_changed': level_changed
            }
            
            # 如果关卡已更新，添加新关键字
            if level_changed:
                if 'game_completed' in locals() and game_completed:
                    result['game_completed'] = True
                    result['message'] = "恭喜您完成了所有关卡！"
                else:
                    result['new_keyword'] = new_keyword
                    result['message'] = f"恭喜您完成第{current_level}关，进入第{game_state['current_level']}关！"
            
            # 如果AI回答失败但不更换关键字，只提示失败
            if not ai_valid:
                result['message'] = "AI无法生成有效回答，但您仍可继续当前关卡。"
            
            return result
        except Exception as e:
            error_message = str(e)
            stack_trace = traceback.format_exc()
            logger.error(f"提交回答时发生错误: {error_message}")
            logger.error(f"堆栈跟踪: {stack_trace}")
            raise
    
    @staticmethod
    def get_ai_response(keyword, user_response, dialogues):
        """调用DeepSeek V3模型生成诗句回复"""
        try:
            logger.info(f"开始获取AI响应，关键字: {keyword}")
            # 复制对话列表以避免修改原始数据
            current_dialogues = list(dialogues)
            
            system_prompt = f"""请严格按照以下要求回复:
1. 只输出一句包含"{keyword}"的古诗句
2. 不要输出任何其他解释文字
3. 不能与之前的对话重复或包含相同诗句
4. 必须是真实存在的古诗句
5. 如果是完整诗句的一部分,必须是独立完整的意思单位
6. 尽量避免使用与之前诗句相似的诗句"""

            # 准备消息列表
            logger.debug("准备消息列表")
            messages = [{"role": "system", "content": system_prompt}]
            
            # 添加历史对话
            for msg in current_dialogues:
                messages.append({"role": msg["role"], "content": msg["content"]})
            
            # 收集历史诗句，用于强化重复检测
            history_poems = []
            for msg in current_dialogues:
                if msg["role"] == "assistant" or msg["role"] == "user":
                    history_poems.append(msg["content"])
            
            max_attempts = 3
            attempt = 0
            
            while attempt < max_attempts:
                try:
                    logger.debug(f"尝试调用DeepSeek API，尝试次数: {attempt+1}/{max_attempts}")
                    # 创建OpenAI客户端
                    logger.debug(f"使用API密钥: {FeiHuaLingService.API_KEY}, 基础URL: {FeiHuaLingService.BASE_URL}")
                    client = OpenAI(
                        api_key=FeiHuaLingService.API_KEY, 
                        base_url=FeiHuaLingService.BASE_URL
                    )
                    
                    # 调用DeepSeek模型
                    logger.debug("发送请求到DeepSeek模型")
                    response = client.chat.completions.create(
                        model="deepseek-chat",  # 使用DeepSeek-V3模型
                        messages=messages,
                        temperature=0.7,  # 增加一些随机性
                        top_p=0.8
                    )
                    
                    assistant_reply = response.choices[0].message.content.strip()
                    logger.debug(f"收到AI回复: {assistant_reply}")
                    
                    # 验证输出格式
                    logger.debug("验证输出格式")
                    if not FeiHuaLingService.is_valid_poem(assistant_reply, keyword):
                        logger.debug("输出格式无效")
                        attempt += 1
                        continue
                    
                    # 增强的重复检测
                    is_duplicate = False
                    for prev_poem in history_poems:
                        # 检查完全相同
                        if assistant_reply == prev_poem:
                            is_duplicate = True
                            break
                        # 检查包含关系(如果一个诗句完全包含在另一个中)
                        if assistant_reply in prev_poem or prev_poem in assistant_reply:
                            # 如果重复的部分超过一定长度，则认为是重复
                            if len(set(assistant_reply) & set(prev_poem)) > len(assistant_reply) * 0.6:
                                is_duplicate = True
                                break
                    
                    if is_duplicate:
                        logger.debug(f"回复重复或高度相似: '{assistant_reply}'")
                        attempt += 1
                        continue
                    
                    # 注意：这里不再更新对话历史，由submit_answer方法负责更新
                    logger.info(f"成功获取AI响应: {assistant_reply}")
                    return assistant_reply
                    
                except Exception as e:
                    error_message = str(e)
                    logger.error(f"调用DeepSeek API错误: {error_message}")
                    attempt += 1
                    
            # 如果多次尝试都失败,从数据库中获取备选答案
            logger.info("API调用失败，使用数据库备选方案")
            fallback_response = FeiHuaLingService.get_fallback_response(keyword, current_dialogues)
            # 注意：这里不再更新对话历史，由submit_answer方法负责更新
            logger.info(f"使用备选回答: {fallback_response}")
            return fallback_response
        except Exception as e:
            error_message = str(e)
            stack_trace = traceback.format_exc()
            logger.error(f"获取AI响应时发生错误: {error_message}")
            logger.error(f"堆栈跟踪: {stack_trace}")
            raise
    
    @staticmethod
    def is_valid_poem(text, keyword):
        """验证是否是合法的诗句格式"""
        # 基本验证
        if not text or not keyword in text:
            return False
            
        # 验证格式(可以根据需要调整)
        if len(text) < 4 or len(text) > 30:  # 诗句长度限制
            return False
            
        # 验证标点符号
        if not re.match(r'^[一-龥，。？！]*$', text):
            return False
            
        return True
    
    @staticmethod
    def get_fallback_response(keyword, dialogues):
        """当AI生成失败时,从数据库中获取备选答案"""
        try:
            logger.info(f"获取备选回答，关键字: {keyword}")
            
            # 收集所有已使用的诗句
            used_poems = set()
            for msg in dialogues:
                if msg["role"] == "assistant" or msg["role"] == "user":
                    used_poems.add(msg["content"])
            
            # 从数据库中查询包含关键字的诗句
            all_poems = FeiHuaLingService.get_poems_by_keyword(keyword)
            
            if all_poems:
                # 过滤掉已经使用过的诗句
                available_poems = [poem for poem in all_poems if poem not in used_poems]
                
                # 进一步过滤相似诗句
                filtered_poems = []
                for poem in available_poems:
                    is_similar = False
                    for used_poem in used_poems:
                        # 检查包含关系和相似度
                        if poem in used_poem or used_poem in poem:
                            if len(set(poem) & set(used_poem)) > len(poem) * 0.6:
                                is_similar = True
                                break
                    if not is_similar:
                        filtered_poems.append(poem)
                
                # 如果有可用的诗句，随机选择一个
                if filtered_poems:
                    selected_poem = random.choice(filtered_poems)
                    logger.info(f"从数据库中选择备选诗句: {selected_poem}")
                    return selected_poem
                
                # 如果所有诗句都已使用，则尝试重新使用
                if available_poems:
                    logger.warning("所有备选诗句已用完，重新使用已有诗句")
                    return random.choice(available_poems)
            
            # 如果没有找到合适的备选诗句，使用默认备选库
            logger.warning(f"数据库中未找到合适的包含'{keyword}'的诗句，使用默认备选")
            # 经典诗句作为最后的备选
            default_poems = {
                '月': [
                    '床前明月光，疑是地上霜',
                    '举头望明月，低头思故乡',
                    '海上生明月，天涯共此时'
                ],
                '花': [
                    '桃花潭水深千尺，不及汪伦送我情',
                    '黄花堂上生秋风，天阶夜色凉如水',
                    '春花秋月何时了，往事知多少'
                ]
            }
            
            if keyword in default_poems:
                # 过滤掉已使用的诗句
                available_default = [p for p in default_poems[keyword] if p not in used_poems]
                if available_default:
                    selected = random.choice(available_default)
                    logger.info(f"从默认备选中选择: {selected}")
                    return selected
            
            # 如果没有找到合适的备选诗句
            logger.warning(f"未找到包含'{keyword}'的备选诗句")
            return f"抱歉,我想不出包含'{keyword}'的诗句了,换个关键字试试吧"
        except Exception as e:
            error_message = str(e)
            logger.error(f"获取备选回答时发生错误: {error_message}")
            return f"抱歉,系统出现了问题,请重试"
