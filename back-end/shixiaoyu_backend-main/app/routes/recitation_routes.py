from flask import Blueprint, request, jsonify
import traceback
import logging
import os
from werkzeug.utils import secure_filename
from app.services.recitation import RecitationService

# 设置日志记录
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

bp = Blueprint('recitation', __name__, url_prefix='/api/recitation')

# 设置临时文件存储路径
UPLOAD_FOLDER = 'temp_uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

@bp.route('/create', methods=['POST'])
def create_session():
    """
    创建一个新的诗词背诵会话
    从数据库中按poem_id升序加载40首诗词
    返回游戏会话ID、第一首诗词内容和总诗词数
    """
    try:
        logger.info("接收到创建诗词背诵会话请求")
        
        # 创建新的背诵会话
        result = RecitationService.create_recitation_session()
        
        if "error" in result:
            return jsonify(result), 500
            
        logger.info("诗词背诵会话创建成功")
        return jsonify(result), 200
    except Exception as e:
        error_message = str(e)
        stack_trace = traceback.format_exc()
        logger.error(f"创建诗词背诵会话时发生错误: {error_message}")
        logger.error(f"堆栈跟踪: {stack_trace}")
        return jsonify({"error": error_message, "stack_trace": stack_trace}), 500

@bp.route('/submit_text', methods=['POST'])
def submit_text_recitation():
    """
    提交诗词背诵的文本
    需要提供会话ID和用户的背诵文本
    可选提供诗词索引（从0开始）
    返回评分结果、反馈、正确文本和所有诗词信息
    """
    try:
        logger.info("接收到提交文本背诵请求")
        data = request.json
        
        # 验证必要参数
        if not data or 'session_id' not in data or 'recitation_text' not in data:
            logger.warning("缺少必要参数：session_id 或 recitation_text")
            return jsonify({"error": "缺少必要参数：session_id 或 recitation_text"}), 400
            
        session_id = data['session_id']
        recitation_text = data['recitation_text']
        # 获取诗词索引参数，默认为None（使用当前索引）
        poem_index = data.get('poem_index')
        if poem_index is not None:
            try:
                poem_index = int(poem_index)
            except ValueError:
                logger.warning(f"无效的诗词索引值: {poem_index}")
                return jsonify({"error": f"无效的诗词索引值: {poem_index}，必须为整数"}), 400
        
        logger.debug(f"会话ID: {session_id}, 背诵文本: {recitation_text}, 诗词索引: {poem_index}")
        
        # 提交背诵并获取响应
        result = RecitationService.submit_text_recitation(session_id, recitation_text, poem_index)
        
        if "error" in result:
            status_code = 404 if "无效的背诵会话" in result["error"] else 500
            return jsonify(result), status_code
            
        logger.info("文本背诵提交成功")
        return jsonify(result), 200
    except Exception as e:
        error_message = str(e)
        stack_trace = traceback.format_exc()
        logger.error(f"提交文本背诵时发生错误: {error_message}")
        logger.error(f"堆栈跟踪: {stack_trace}")
        return jsonify({"error": error_message, "stack_trace": stack_trace}), 500

@bp.route('/submit_audio', methods=['POST'])
def submit_audio_recitation():
    """
    提交诗词背诵的语音
    接受上传的音频文件，使用语音识别后评分
    可选提供诗词索引（从0开始）
    返回识别结果、评分、反馈、正确文本和所有诗词信息
    """
    try:
        logger.info("接收到提交语音背诵请求")
        
        # 验证会话ID
        session_id = request.form.get('session_id')
        if not session_id:
            logger.warning("缺少必要参数：session_id")
            return jsonify({"error": "缺少必要参数：session_id"}), 400
        
        # 获取诗词索引参数，默认为None（使用当前索引）
        poem_index = request.form.get('poem_index')
        if poem_index is not None:
            try:
                poem_index = int(poem_index)
            except ValueError:
                logger.warning(f"无效的诗词索引值: {poem_index}")
                return jsonify({"error": f"无效的诗词索引值: {poem_index}，必须为整数"}), 400
        
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
        
        # 处理语音背诵
        result = RecitationService.submit_audio_recitation(session_id, file_path, poem_index)
        
        # 删除临时文件
        try:
            os.remove(file_path)
            logger.debug(f"临时文件已删除: {file_path}")
        except Exception as file_error:
            logger.warning(f"删除临时文件失败: {str(file_error)}")
        
        if "error" in result:
            status_code = 404 if "无效的背诵会话" in result["error"] else 500
            return jsonify(result), status_code
            
        logger.info("语音背诵提交成功")
        return jsonify(result), 200
    except Exception as e:
        error_message = str(e)
        stack_trace = traceback.format_exc()
        logger.error(f"提交语音背诵时发生错误: {error_message}")
        logger.error(f"堆栈跟踪: {stack_trace}")
        return jsonify({"error": error_message, "stack_trace": stack_trace}), 500

@bp.route('/record', methods=['POST'])
def record_and_recite():
    """
    在服务器上直接录音并提交背诵
    需要提供会话ID
    可选提供诗词索引（从0开始）和录音时长（秒）
    返回录音识别结果、评分、反馈、正确文本和所有诗词信息
    """
    try:
        logger.info("接收到录音并背诵请求")
        data = request.json
        
        # 验证必要参数
        if not data or 'session_id' not in data:
            logger.warning("缺少必要参数：session_id")
            return jsonify({"error": "缺少必要参数：session_id"}), 400
            
        session_id = data['session_id']
        
        # 获取诗词索引参数，默认为None（使用当前索引）
        poem_index = data.get('poem_index')
        
        # 获取录音时长，默认为15秒
        duration = data.get('duration', 15)
        
        logger.debug(f"会话ID: {session_id}, 诗词索引: {poem_index}, 录音时长: {duration}秒")
        
        # 录音并提交背诵
        result = RecitationService.record_and_recite(session_id, poem_index, duration)
        
        if "error" in result:
            status_code = 404 if "无效的背诵会话" in result["error"] else 500
            return jsonify(result), status_code
            
        logger.info("录音并背诵成功")
        return jsonify(result), 200
    except Exception as e:
        error_message = str(e)
        stack_trace = traceback.format_exc()
        logger.error(f"录音并背诵时发生错误: {error_message}")
        logger.error(f"堆栈跟踪: {stack_trace}")
        return jsonify({"error": error_message, "stack_trace": stack_trace}), 500 