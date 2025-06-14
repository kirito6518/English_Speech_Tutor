from flask import Blueprint, request, jsonify
import traceback
import logging
import os
from werkzeug.utils import secure_filename
from app.services.ninegrid import NineGridService, QuestionOfNineGridEncoder
import json

# 设置日志记录
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

bp = Blueprint('ninegrid', __name__, url_prefix='/api/ninegrid')

# 设置临时文件存储路径
UPLOAD_FOLDER = 'temp_uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

@bp.route('/create', methods=['POST'])
def create_game():
    """
    创建一个新的九宫格游戏
    从数据库中加载题目
    返回游戏会话ID、第一题内容、当前题号和总题数
    """
    try:
        logger.info("接收到创建九宫格游戏请求")
        
        # 从数据库加载题目创建游戏
        result = NineGridService.create_game()
        
        if "error" in result:
            return jsonify(result), 500
            
        logger.info("九宫格游戏创建成功")
        return jsonify(result), 200
    except Exception as e:
        error_message = str(e)
        stack_trace = traceback.format_exc()
        logger.error(f"创建九宫格游戏时发生错误: {error_message}")
        logger.error(f"堆栈跟踪: {stack_trace}")
        return jsonify({"error": error_message, "stack_trace": stack_trace}), 500

@bp.route('/submit', methods=['POST'])
def submit_answer():
    """
    提交九宫格游戏的文本答案
    需要提供会话ID和用户的文本答案
    可选提供题目索引（从0开始）
    注意：答案将进行严格匹配，必须与标准答案完全一致才算正确
    返回判断结果、是否正确、正确答案、当前得分和所有题目信息
    """
    try:
        logger.info("接收到提交九宫格答案请求")
        data = request.json
        
        # 验证必要参数
        if not data or 'session_id' not in data or 'answer' not in data:
            logger.warning("缺少必要参数：session_id 或 answer")
            return jsonify({"error": "缺少必要参数：session_id 或 answer"}), 400
            
        session_id = data['session_id']
        user_answer = data['answer']
        # 获取题目索引参数，默认为None（使用当前索引）
        question_index = data.get('question_index')
        
        logger.debug(f"会话ID: {session_id}, 用户答案: {user_answer}, 题目索引: {question_index}")
        
        # 提交答案并获取响应
        result = NineGridService.submit_answer(session_id, user_answer, question_index)
        
        if "error" in result:
            status_code = 404 if "无效的游戏会话" in result["error"] else 500
            return jsonify(result), status_code
            
        logger.info("答案提交成功")
        return jsonify(result), 200
    except Exception as e:
        error_message = str(e)
        stack_trace = traceback.format_exc()
        logger.error(f"提交九宫格答案时发生错误: {error_message}")
        logger.error(f"堆栈跟踪: {stack_trace}")
        return jsonify({"error": error_message, "stack_trace": stack_trace}), 500

@bp.route('/submit_audio', methods=['POST'])
def submit_audio_answer():
    """
    提交九宫格游戏的语音答案
    接受上传的音频文件，使用语音识别后提交答案
    可选提供题目索引（从0开始）
    返回识别结果、判断结果、正确答案和所有题目信息
    """
    try:
        logger.info("接收到提交九宫格语音答案请求")
        
        # 验证会话ID
        session_id = request.form.get('session_id')
        if not session_id:
            logger.warning("缺少必要参数：session_id")
            return jsonify({"error": "缺少必要参数：session_id"}), 400
        
        # 获取题目索引参数，默认为None（使用当前索引）
        question_index = request.form.get('question_index')
        if question_index is not None:
            try:
                question_index = int(question_index)
            except ValueError:
                logger.warning(f"无效的题目索引值: {question_index}")
                return jsonify({"error": f"无效的题目索引值: {question_index}，必须为整数"}), 400
        
        # 检查是否上传了文件
        if 'audio_file' not in request.files:
            logger.warning("未上传音频文件")
            return jsonify({"error": "未上传音频文件"}), 400
            
        audio_file = request.files['audio_file']
        if audio_file.filename == '':
            logger.warning("文件名为空")
            return jsonify({"error": "文件名为空"}), 400
            
        # 保存上传的文件
        filename = secure_filename(f"{session_id}_{audio_file.filename}")
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        audio_file.save(file_path)
        logger.debug(f"音频文件已保存到: {file_path}")
        
        # 使用语音识别处理文件
        result = NineGridService.submit_audio_answer(session_id, file_path, question_index)
        
        # 删除临时文件
        try:
            os.remove(file_path)
            logger.debug(f"临时文件已删除: {file_path}")
        except Exception as file_error:
            logger.warning(f"删除临时文件失败: {str(file_error)}")
        
        if "error" in result:
            status_code = 404 if "无效的游戏会话" in result["error"] else 500
            return jsonify(result), status_code
            
        logger.info("音频答案提交成功")
        return jsonify(result), 200
    except Exception as e:
        error_message = str(e)
        stack_trace = traceback.format_exc()
        logger.error(f"提交九宫格语音答案时发生错误: {error_message}")
        logger.error(f"堆栈跟踪: {stack_trace}")
        return jsonify({"error": error_message, "stack_trace": stack_trace}), 500

@bp.route('/record', methods=['POST'])
def record_and_answer():
    """
    在服务器上直接录音并提交九宫格答案
    需要提供会话ID
    可选提供题目索引（从0开始）
    返回录音识别结果、判断结果、正确答案和所有题目信息
    """
    try:
        logger.info("接收到录音并提交九宫格答案请求")
        data = request.json
        
        # 验证必要参数
        if not data or 'session_id' not in data:
            logger.warning("缺少必要参数：session_id")
            return jsonify({"error": "缺少必要参数：session_id"}), 400
            
        session_id = data['session_id']
        
        # 获取题目索引参数，默认为None（使用当前索引）
        question_index = data.get('question_index')
        
        logger.debug(f"会话ID: {session_id}, 题目索引: {question_index}")
        
        # 录音并提交答案
        result = NineGridService.record_and_answer(session_id, question_index)
        
        if "error" in result:
            status_code = 404 if "无效的游戏会话" in result["error"] else 500
            return jsonify(result), status_code
            
        logger.info("录音并提交答案成功")
        return jsonify(result), 200
    except Exception as e:
        error_message = str(e)
        stack_trace = traceback.format_exc()
        logger.error(f"录音并提交九宫格答案时发生错误: {error_message}")
        logger.error(f"堆栈跟踪: {stack_trace}")
        return jsonify({"error": error_message, "stack_trace": stack_trace}), 500

# 注册自定义JSON编码器
@bp.after_request
def after_request(response):
    """为九宫格游戏的路由添加自定义JSON编码器"""
    if response.headers.get('Content-Type') == 'application/json':
        json_data = response.get_json()
        if json_data:
            # 使用自定义编码器重新编码
            response.data = json.dumps(json_data, cls=QuestionOfNineGridEncoder).encode('utf-8')
    return response 