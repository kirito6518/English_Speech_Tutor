from flask import Blueprint, request, jsonify
from app.services.feihualing import FeiHuaLingService
import traceback
import logging

# 设置日志记录
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

bp = Blueprint('feihualing', __name__, url_prefix='/api/feihualing')

@bp.route('/create', methods=['POST'])
def create_game():
    """
    创建一个新的飞花令游戏
    可以接受自定义关键字列表，如果没有提供则使用默认关键字
    返回游戏会话ID、当前关卡(level)和当前关键字(keyword)
    """
    try:
        logger.info("接收到创建游戏请求")
        # 获取自定义关键字列表（可选）
        keywords = request.json.get('keywords')
        logger.debug(f"自定义关键字: {keywords}")
        
        # 创建新游戏
        logger.info("调用 FeiHuaLingService.create_game")
        result = FeiHuaLingService.create_game(keywords)
        
        logger.info("游戏创建成功")
        return jsonify(result), 200
    except Exception as e:
        error_message = str(e)
        stack_trace = traceback.format_exc()
        logger.error(f"创建游戏时发生错误: {error_message}")
        logger.error(f"堆栈跟踪: {stack_trace}")
        return jsonify({"error": error_message, "stack_trace": stack_trace}), 500

@bp.route('/submit', methods=['POST'])
def submit_answer():
    """
    提交用户的诗句回答，并获取AI的回应
    需要提供会话ID和用户的回答
    
    关卡机制说明：
    1. 每个关卡有固定的关键字
    2. 用户需要在当前关卡成功回答指定次数(默认3次)才能进入下一关
    3. 只有进入新关卡时才会更换关键字
    4. 总共有5个关卡，完成全部关卡后游戏结束
    
    响应说明：
    - level: 当前关卡
    - keyword: 当前关键字
    - correct_answers: 当前关卡已答对次数
    - required_answers: 进入下一关所需的答对次数
    - level_changed: 是否升级到下一关
    - new_keyword: 如果升级，下一关的关键字
    - game_completed: 是否已完成所有关卡
    """
    try:
        logger.info("接收到提交回答请求")
        data = request.json
        
        # 验证必要参数
        if 'session_id' not in data or 'user_response' not in data:
            logger.warning("缺少必要参数：session_id 或 user_response")
            return jsonify({"error": "缺少必要参数：session_id 或 user_response"}), 400
            
        session_id = data['session_id']
        user_response = data['user_response']
        logger.debug(f"会话ID: {session_id}, 用户回答: {user_response}")
        
        # 提交回答并获取响应
        logger.info("调用 FeiHuaLingService.submit_answer")
        result = FeiHuaLingService.submit_answer(session_id, user_response)
        
        logger.info("回答提交成功")
        return jsonify(result), 200
    except Exception as e:
        error_message = str(e)
        stack_trace = traceback.format_exc()
        logger.error(f"提交回答时发生错误: {error_message}")
        logger.error(f"堆栈跟踪: {stack_trace}")
        return jsonify({"error": error_message, "stack_trace": stack_trace}), 500
