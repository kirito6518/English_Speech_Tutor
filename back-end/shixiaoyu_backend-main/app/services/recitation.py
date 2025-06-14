import random
import logging
import traceback
import json
import os
import pymysql
import pymysql.cursors
import Levenshtein
import re
from app.services.audio import AudioService

# 设置日志记录
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class RecitationService:
    # 数据库连接配置
    DB_CONFIG = {
        'host': 'localhost',
        'user': 'sxy',  # 按实际用户名修改
        'password': 'cfyxYDz62eTrxBPG',  # 按实际密码修改，留空表示无密码
        'db': 'sxy',
        'charset': 'utf8mb4',
        'cursorclass': pymysql.cursors.DictCursor
    }
    
    # 存储进行中的背诵会话
    recitation_sessions = {}
    
    @staticmethod
    def get_db_connection():
        """获取数据库连接"""
        try:
            connection = pymysql.connect(**RecitationService.DB_CONFIG)
            return connection
        except Exception as e:
            logger.error(f"数据库连接失败: {str(e)}")
            return None
    
    @staticmethod
    def remove_punctuation(text):
        """移除标点符号，只保留汉字、字母和数字字符"""
        return re.sub(r'[^\w\s\u4e00-\u9fff]', '', text)
    
    @staticmethod
    def load_poems_from_db(limit=40):
        """从数据库中按poem_id字典序加载指定数量的诗词"""
        try:
            logger.info(f"从数据库按poem_id字典序加载{limit}首诗词")
            poems = []
            
            connection = RecitationService.get_db_connection()
            if not connection:
                logger.error("无法获取数据库连接")
                return []
                
            try:
                with connection.cursor() as cursor:
                    # 按poem_id字典序获取诗词
                    sql = "SELECT poem_id, poem_name, author, title FROM poem ORDER BY poem_id ASC LIMIT %s"
                    cursor.execute(sql, (limit,))
                    poem_results = cursor.fetchall()
                    
                    for poem_row in poem_results:
                        poem_id = poem_row['poem_id']
                        
                        # 获取诗词的所有行
                        sql = "SELECT line_number, content FROM poem_lines WHERE poem_id = %s ORDER BY line_number"
                        cursor.execute(sql, (poem_id,))
                        line_results = cursor.fetchall()
                        
                        # 组合诗词内容
                        content_lines = []
                        for line in line_results:
                            content_lines.append(line['content'])
                        
                        # 创建诗词对象
                        poem = {
                            'poem_id': poem_id,
                            'title': poem_row['title'],
                            'author': poem_row['author'],
                            'poem_name': poem_row['poem_name'],
                            'content': content_lines,
                            'full_text': ''.join(content_lines)
                        }
                        poems.append(poem)
                        logger.debug(f"成功加载诗词ID={poem_id}, 标题={poem['title']}, 作者={poem['author']}")
                    
            finally:
                connection.close()
            
            logger.info(f"成功从数据库加载{len(poems)}首诗词")
            return poems
        except Exception as e:
            error_message = str(e)
            stack_trace = traceback.format_exc()
            logger.error(f"从数据库加载诗词失败: {error_message}")
            logger.error(f"堆栈跟踪: {stack_trace}")
            return []
    
    @staticmethod
    def create_recitation_session():
        """创建一个新的诗词背诵会话"""
        try:
            logger.info("开始创建诗词背诵会话")
            
            # 加载诗词
            poems = RecitationService.load_poems_from_db(40)
            if not poems:
                logger.error("没有可用的诗词")
                return {"error": "没有可用的诗词"}
            
            # 生成会话ID
            session_id = f"recitation_{random.randint(1000, 9999)}"
            
            # 初始化会话状态
            session_state = {
                'poems': poems,
                'current_poem_index': 0,
                'completed_poems': [],
                'total_poems': len(poems)
            }
            
            # 存储会话状态
            RecitationService.recitation_sessions[session_id] = session_state
            
            # 返回初始状态
            current_poem = poems[0]
            logger.info(f"诗词背诵会话创建成功，会话ID: {session_id}, 总诗词数: {len(poems)}")
            
            return {
                'session_id': session_id,
                'poem': {
                    'poem_id': current_poem['poem_id'],
                    'title': current_poem['title'],
                    'author': current_poem['author'],
                    'poem_name': current_poem['poem_name'],
                    'content': current_poem['content']
                },
                'poem_number': 1,
                'total_poems': len(poems)
            }
        except Exception as e:
            error_message = str(e)
            stack_trace = traceback.format_exc()
            logger.error(f"创建诗词背诵会话失败: {error_message}")
            logger.error(f"堆栈跟踪: {stack_trace}")
            return {"error": error_message}
    
    @staticmethod
    def submit_text_recitation(session_id, recitation_text, poem_index=None):
        """提交文本背诵并评分"""
        try:
            logger.info(f"提交文本背诵，会话ID: {session_id}")
            
            if session_id not in RecitationService.recitation_sessions:
                logger.error(f"找不到会话ID: {session_id}")
                return {"error": "无效的背诵会话"}
            
            session_state = RecitationService.recitation_sessions[session_id]
            
            # 使用指定的诗词索引或当前索引
            current_index = poem_index if poem_index is not None else session_state['current_poem_index']
            
            # 确保索引有效
            if current_index < 0 or current_index >= len(session_state['poems']):
                logger.error(f"无效的诗词索引: {current_index}")
                return {"error": f"无效的诗词索引: {current_index}，有效范围: 0-{len(session_state['poems'])-1}"}
            
            # 更新当前索引
            if poem_index is not None and poem_index != session_state['current_poem_index']:
                session_state['current_poem_index'] = poem_index
                logger.info(f"前端指定切换到诗词索引: {poem_index}")
            
            current_poem = session_state['poems'][current_index]
            correct_text = current_poem['full_text']
            
            # 预处理文本，移除标点符号
            clean_recitation = RecitationService.remove_punctuation(recitation_text)
            clean_correct = RecitationService.remove_punctuation(correct_text)
            
            logger.debug(f"背诵文本: '{clean_recitation}'")
            logger.debug(f"正确文本: '{clean_correct}'")
            
            # 计算编辑距离
            distance = Levenshtein.distance(clean_recitation, clean_correct)
            
            # 基于编辑距离和文本长度计算得分
            text_length = len(clean_correct)
            if text_length == 0:
                accuracy = 0  # 避免除以零
            else:
                accuracy = max(0, 1 - (distance / text_length))
            
            # 根据精确度确定得分等级
            if accuracy >= 0.95:  # 几乎完全正确
                score = 5
                feedback = "优秀！背诵非常精确。"
            elif accuracy >= 0.9:  # 轻微错误
                score = 4
                feedback = "很好！有少量小错误。"
            elif accuracy >= 0.8:  # 多个错误但整体可接受
                score = 3
                feedback = "良好。存在一些错误，但整体不错。"
            elif accuracy >= 0.6:  # 多个错误
                score = 2
                feedback = "需要改进。存在较多错误。"
            else:  # 大量错误或完全不同
                score = 1
                feedback = "需要重新背诵。与原文相差较大。"
            
            # 标记诗词为已完成
            completed_data = {
                'poem_index': current_index,
                'score': score,
                'accuracy': accuracy
            }
            
            # 更新或添加到已完成列表
            completed_found = False
            for i, comp in enumerate(session_state['completed_poems']):
                if comp['poem_index'] == current_index:
                    session_state['completed_poems'][i] = completed_data
                    completed_found = True
                    break
            
            if not completed_found:
                session_state['completed_poems'].append(completed_data)
            
            # 准备所有诗词信息
            all_poems = []
            for idx, poem in enumerate(session_state['poems']):
                poem_data = {
                    'poem_id': poem['poem_id'],
                    'title': poem['title'],
                    'author': poem['author'],
                    'poem_name': poem['poem_name'],
                    'is_completed': False,
                    'score': 0
                }
                
                # 添加完成状态
                for comp in session_state['completed_poems']:
                    if comp['poem_index'] == idx:
                        poem_data['is_completed'] = True
                        poem_data['score'] = comp['score']
                        break
                
                all_poems.append(poem_data)
            
            # 构建响应
            result = {
                'score': score,
                'accuracy': round(accuracy * 100, 2),  # 转换为百分比
                'feedback': feedback,
                'correct_text': correct_text,
                'recitation_text': recitation_text,
                'poem_number': current_index + 1,
                'total_poems': len(session_state['poems']),
                'current_index': current_index,
                'current_poem': {
                    'poem_id': current_poem['poem_id'],
                    'title': current_poem['title'],
                    'author': current_poem['author'],
                    'poem_name': current_poem['poem_name'],
                    'content': current_poem['content']
                },
                'all_poems': all_poems
            }
            
            logger.info(f"背诵评分结果: {score}/5, 准确率: {round(accuracy * 100, 2)}%")
            return result
            
        except Exception as e:
            error_message = str(e)
            stack_trace = traceback.format_exc()
            logger.error(f"提交背诵失败: {error_message}")
            logger.error(f"堆栈跟踪: {stack_trace}")
            return {"error": error_message}
    
    @staticmethod
    def submit_audio_recitation(session_id, audio_file_path, poem_index=None):
        """通过语音文件提交背诵并评分"""
        try:
            logger.info(f"通过语音提交背诵，会话ID: {session_id}")
            
            if session_id not in RecitationService.recitation_sessions:
                logger.error(f"找不到会话ID: {session_id}")
                return {"error": "无效的背诵会话"}
            
            # 使用语音识别服务识别背诵内容
            recognized_text = AudioService.recognize_audio(audio_file_path)
            logger.debug(f"语音识别结果: '{recognized_text}'")
            
            if recognized_text == "识别失败":
                logger.error("语音识别失败")
                return {"error": "语音识别失败，请重试或直接输入文字"}
            
            # 提交识别后的文本
            result = RecitationService.submit_text_recitation(session_id, recognized_text, poem_index)
            
            # 添加语音识别结果到返回值
            if "error" not in result:
                result["recognized_text"] = recognized_text
            
            return result
            
        except Exception as e:
            error_message = str(e)
            stack_trace = traceback.format_exc()
            logger.error(f"语音背诵失败: {error_message}")
            logger.error(f"堆栈跟踪: {stack_trace}")
            return {"error": error_message}
    
    @staticmethod
    def record_and_recite(session_id, poem_index=None, duration=15):
        """录制语音并提交背诵"""
        try:
            logger.info(f"开始录音并提交背诵，会话ID: {session_id}")
            
            # 录制音频
            audio_file = 'recitation_audio.wav'
            
            logger.info(f"开始录制音频，时长: {duration}秒")
            AudioService.record_audio(audio_file, duration)
            
            # 提交音频背诵
            result = RecitationService.submit_audio_recitation(session_id, audio_file, poem_index)
            
            return result
            
        except Exception as e:
            error_message = str(e)
            stack_trace = traceback.format_exc()
            logger.error(f"录音并背诵失败: {error_message}")
            logger.error(f"堆栈跟踪: {stack_trace}")
            return {"error": error_message} 