import random
import logging
import traceback
import json
import os
import pymysql
import pymysql.cursors
from app.services.audio import AudioService

# 设置日志记录
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class QuestionOfNineGrid:
    def __init__(self, title, answer):
        self.title = title  # 九宫格标题，是一个3x3的二维数组
        self.answer = answer  # 答案，是一个字符串
    
    def to_dict(self):
        return {
            "title": self.title,
            "answer": self.answer
        }

class QuestionOfNineGridEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, QuestionOfNineGrid):
            return obj.to_dict()
        return super(QuestionOfNineGridEncoder, self).default(obj)

class NineGridService:
    # 游戏配置
    GAME_CONFIG = {
        'recording_time': 10  # 录音时长(秒)
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
    
    # 存储进行中的游戏会话
    games = {}
    
    @staticmethod
    def get_db_connection():
        """获取数据库连接"""
        try:
            connection = pymysql.connect(**NineGridService.DB_CONFIG)
            return connection
        except Exception as e:
            logger.error(f"数据库连接失败: {str(e)}")
            return None
    
    @staticmethod
    def load_questions_from_db():
        """从数据库中加载九宫格题目"""
        try:
            logger.info("从数据库加载九宫格题目")
            questions = []
            
            connection = NineGridService.get_db_connection()
            if not connection:
                logger.error("无法获取数据库连接")
                return []
                
            try:
                with connection.cursor() as cursor:
                    # 查询grid表中的所有题目
                    sql = "SELECT grid_id, question, answer FROM grid"
                    cursor.execute(sql)
                    results = cursor.fetchall()
                    
                    for row in results:
                        try:
                            grid_id = row['grid_id']
                            question_str = row['question']
                            answer = row['answer']
                            
                            # 解析题目字符串为3x3网格
                            # 假设问题格式为"字1,字2,字3;字4,字5,字6;字7,字8,字9"
                            # 或者直接是JSON格式
                            # 或者是九个字符的字符串"字1字2字3字4字5字6字7字8字9"
                            try:
                                # 尝试解析为JSON
                                title = json.loads(question_str)
                            except json.JSONDecodeError:
                                # 如果不是JSON，尝试解析为自定义格式或九字格式
                                title = []
                                
                                # 尝试判断是否为九字字符串格式
                                if len(question_str) == 9:
                                    # 如果是9个字符的字符串，按3x3拆分
                                    title = [
                                        [question_str[0], question_str[1], question_str[2]],
                                        [question_str[3], question_str[4], question_str[5]],
                                        [question_str[6], question_str[7], question_str[8]]
                                    ]
                                    logger.debug(f"解析九字格式题目: {question_str} -> {title}")
                                else:
                                    # 否则尝试解析为分号分隔的格式
                                    rows = question_str.split(';')
                                    if len(rows) != 3:
                                        logger.warning(f"题目格式不正确，行数不是3: {question_str}")
                                        continue
                                        
                                    for row_str in rows:
                                        cells = row_str.split(',')
                                        if len(cells) != 3:
                                            logger.warning(f"题目格式不正确，列数不是3: {row_str}")
                                            break
                                        title.append(cells)
                                    
                                    if len(title) != 3:
                                        continue
                            
                            question = QuestionOfNineGrid(title, answer)
                            questions.append(question)
                            logger.debug(f"成功加载题目ID={grid_id}, 题目={title}, 答案={answer}")
                        except Exception as e:
                            logger.warning(f"解析题目失败: {str(e)}, 题目数据: {row}")
                            continue
            finally:
                connection.close()
            
            logger.info(f"成功从数据库加载{len(questions)}道九宫格题目")
            return questions
        except Exception as e:
            error_message = str(e)
            stack_trace = traceback.format_exc()
            logger.error(f"从数据库加载九宫格题目失败: {error_message}")
            logger.error(f"堆栈跟踪: {stack_trace}")
            return []
    
    @staticmethod
    def load_questions(file_path=None):
        """
        从文件加载九宫格题目（保留兼容性）
        实际优先使用数据库加载
        """
        # 优先从数据库加载题目
        db_questions = NineGridService.load_questions_from_db()
        if db_questions:
            return db_questions
            
        # 数据库加载失败，则尝试从文件加载（作为备选方案）
        logger.info("从数据库加载题目失败，尝试从文件加载")
        try:
            if file_path is None:
                # 使用默认路径
                file_path = os.path.join(os.path.dirname(__file__), '../../data/ninegrid_questions.txt')
            
            logger.info(f"从文件加载九宫格题目: {file_path}")
            questions = []
            
            with open(file_path, 'r', encoding='utf-8') as file:
                lines = file.readlines()
                i = 0
                while i < len(lines):
                    line = lines[i].strip()
                    if line.startswith('#'):
                        topic = []
                        # 读取3x3的二维数组
                        i += 1  # 跳过"#"行
                        if i < len(lines):
                            i += 1  # 跳过可能的空行
                        
                        # 读取3行九宫格内容
                        for j in range(3):
                            if i + j < len(lines):
                                row = lines[i + j].strip().split()
                                if len(row) == 3:  # 确保每行有3个字
                                    topic.append(row)
                                else:
                                    logger.warning(f"九宫格行格式不正确，期望3个字，实际为{len(row)}个字: {row}")
                        
                        i += 3  # 跳过3行九宫格内容
                        
                        # 读取答案
                        answer = ""
                        if i < len(lines):
                            answer = lines[i].strip()
                            i += 1
                        
                        # 如果九宫格和答案均有效，则添加题目
                        if len(topic) == 3 and all(len(row) == 3 for row in topic) and answer:
                            question = QuestionOfNineGrid(topic, answer)
                            questions.append(question)
                            logger.debug(f"成功加载题目: {topic}, 答案: {answer}")
                        else:
                            logger.warning(f"无效的题目格式: 九宫格={topic}, 答案={answer}")
                    else:
                        i += 1  # 跳过无关行
            
            logger.info(f"成功从文件加载{len(questions)}道九宫格题目")
            return questions
        except Exception as e:
            error_message = str(e)
            stack_trace = traceback.format_exc()
            logger.error(f"加载九宫格题目失败: {error_message}")
            logger.error(f"堆栈跟踪: {stack_trace}")
            return []
    
    @staticmethod
    def create_game(custom_questions=None):
        """创建一个新的九宫格游戏会话"""
        try:
            logger.info("开始创建九宫格游戏")
            
            # 加载题目
            questions = custom_questions if custom_questions else NineGridService.load_questions_from_db()
            if not questions:
                logger.error("没有可用的九宫格题目")
                return {"error": "没有可用的九宫格题目"}
            
            # 打乱题目顺序
            random.shuffle(questions)
            
            # 生成会话ID
            session_id = f"ninegrid_{random.randint(1000, 9999)}"
            
            # 初始化游戏状态
            game_state = {
                'questions': questions,
                'current_question_index': 0,
                'score': 0,
                'total_questions': len(questions)
            }
            
            # 存储游戏状态
            NineGridService.games[session_id] = game_state
            
            # 返回初始状态
            current_question = questions[0]
            logger.info(f"九宫格游戏创建成功，会话ID: {session_id}, 总题数: {len(questions)}")
            
            return {
                'session_id': session_id,
                'question': current_question.to_dict(),
                'question_number': 1,
                'total_questions': len(questions),
                'score': 0
            }
        except Exception as e:
            error_message = str(e)
            stack_trace = traceback.format_exc()
            logger.error(f"创建九宫格游戏失败: {error_message}")
            logger.error(f"堆栈跟踪: {stack_trace}")
            return {"error": error_message}
    
    @staticmethod
    def submit_answer(session_id, user_answer=None, question_index=None):
        """
        提交用户答案，用户可以直接提交文本答案或上传语音文件
        
        参数:
            session_id: 游戏会话ID
            user_answer: 用户提交的答案
            question_index: 当前题目索引，由前端指定（从0开始），若为None则使用当前索引
        """
        try:
            logger.info(f"提交九宫格游戏答案，会话ID: {session_id}")
            
            if session_id not in NineGridService.games:
                logger.error(f"找不到会话ID: {session_id}")
                return {"error": "无效的游戏会话"}
            
            game_state = NineGridService.games[session_id]
            
            # 使用前端指定的题目索引或当前索引
            current_index = question_index if question_index is not None else game_state['current_question_index']
            
            # 确保索引在有效范围内
            if current_index < 0 or current_index >= len(game_state['questions']):
                logger.error(f"无效的题目索引: {current_index}")
                return {"error": f"无效的题目索引: {current_index}，有效范围: 0-{len(game_state['questions'])-1}"}
                
            # 更新当前索引（如果前端指定了不同的索引）
            if question_index is not None and question_index != game_state['current_question_index']:
                game_state['current_question_index'] = question_index
                logger.info(f"前端指定切换到题目索引: {question_index}")
            
            current_question = game_state['questions'][current_index]
            correct_answer = current_question.answer
            
            # 处理用户答案
            is_correct = False
            recognized_text = ""
            
            if user_answer is not None:
                # 如果直接提供了文本答案，进行严格匹配
                recognized_text = user_answer
                # 严格匹配 - 完全相等才算正确
                is_correct = user_answer.strip() == correct_answer.strip()
                logger.debug(f"文本答案: '{user_answer}'，正确答案: '{correct_answer}'，是否正确: {is_correct}")
                
                # 如果答案正确且尚未得分，则加分
                if is_correct and not game_state.get(f'question_{current_index}_correct', False):
                    game_state['score'] += 1
                    game_state[f'question_{current_index}_correct'] = True
                    logger.info(f"答案正确，题目{current_index+1}得分+1")
            else:
                # 没有提供答案
                logger.error("未提供答案")
                return {"error": "必须提供答案"}
            
            # 构建响应包含所有题目信息
            all_questions = []
            for idx, q in enumerate(game_state['questions']):
                question_data = q.to_dict()
                # 去掉返回给前端的答案字段
                if 'answer' in question_data:
                    del question_data['answer']
                question_data['is_completed'] = game_state.get(f'question_{idx}_correct', False)
                all_questions.append(question_data)
            
            # 构建基本响应
            result = {
                "is_correct": is_correct,
                "correct_answer": correct_answer,
                "recognized_text": recognized_text,
                "score": game_state['score'],
                "current_index": current_index,
                "question_number": current_index + 1,
                "total_questions": game_state['total_questions'],
                "all_questions": all_questions,
                "current_question": current_question.to_dict()
            }
            
            logger.info(f"答案提交结果: {'正确' if is_correct else '错误'}, 当前得分: {game_state['score']}")
            return result
            
        except Exception as e:
            error_message = str(e)
            stack_trace = traceback.format_exc()
            logger.error(f"提交九宫格游戏答案失败: {error_message}")
            logger.error(f"堆栈跟踪: {stack_trace}")
            return {"error": error_message}
    
    @staticmethod
    def submit_audio_answer(session_id, audio_file_path, question_index=None):
        """通过语音文件提交答案"""
        try:
            logger.info(f"通过语音提交九宫格游戏答案，会话ID: {session_id}")
            
            if session_id not in NineGridService.games:
                logger.error(f"找不到会话ID: {session_id}")
                return {"error": "无效的游戏会话"}
            
            # 使用语音识别服务识别用户回答
            recognized_text = AudioService.recognize_audio(audio_file_path)
            logger.debug(f"语音识别结果: '{recognized_text}'")
            
            if recognized_text == "识别失败":
                logger.error("语音识别失败")
                return {"error": "语音识别失败，请重试或直接输入文字答案"}
            
            # 提交识别后的文本答案
            result = NineGridService.submit_answer(session_id, recognized_text, question_index)
            
            # 添加语音识别结果到返回值
            if "error" not in result:
                result["recognized_text"] = recognized_text
            
            return result
            
        except Exception as e:
            error_message = str(e)
            stack_trace = traceback.format_exc()
            logger.error(f"语音提交九宫格游戏答案失败: {error_message}")
            logger.error(f"堆栈跟踪: {stack_trace}")
            return {"error": error_message}
    
    @staticmethod
    def record_and_answer(session_id, question_index=None):
        """录制语音并提交答案（用于直接在服务器上录音的场景）"""
        try:
            logger.info(f"开始录音并提交九宫格答案，会话ID: {session_id}")
            
            # 录制音频
            audio_file = 'ninegrid_answer.wav'
            recording_time = NineGridService.GAME_CONFIG['recording_time']
            
            logger.info(f"开始录制音频，时长: {recording_time}秒")
            AudioService.record_audio(audio_file, recording_time)
            
            # 提交音频答案
            result = NineGridService.submit_audio_answer(session_id, audio_file, question_index)
            
            return result
            
        except Exception as e:
            error_message = str(e)
            stack_trace = traceback.format_exc()
            logger.error(f"录音并提交九宫格答案失败: {error_message}")
            logger.error(f"堆栈跟踪: {stack_trace}")
            return {"error": error_message} 