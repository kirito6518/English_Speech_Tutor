from flask import Blueprint, request, jsonify, Response, session
import requests
from flask_cors import CORS

bp = Blueprint('chat', __name__, url_prefix='/api/chat')

# 填写你的 API Key
API_KEY = "sk-b9b51caa4cb648869dfb197a8e1e8165"  

url = "https://api.deepseek.com/chat/completions"
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {API_KEY}"
}

# 启用 CORS
CORS(bp, resources={r"/api/*": {"origins": "*"}})

# 后端接收用户输入并获取 DeepSeek API 的响应
@bp.route('/get_and_return', methods=['GET'])
def chat():
    user_input = request.args.get('user_input')  # 获取 GET 请求中的用户输入

    # 确保有用户输入
    if not user_input:
        return jsonify({"error": "User input is required!"}), 400

    # 如果 session 中没有 conversation_history，则初始化
    if 'conversation_history' not in session:
        session['conversation_history'] = [
            {"role": "system", "content": "你是一个知识渊博的中国古代诗词大师，对于用户输入的诗人、诗名、诗句等，你都能详细讲述相关背景知识。"}
        ]
    
    # 将用户输入加入到对话历史中
    session['conversation_history'].append({"role": "user", "content": user_input})

    # 创建请求数据
    data = {
        "model": "deepseek-chat",  # 使用 deepseek-chat 模型
        "messages": session['conversation_history'],  # 发送当前的消息上下文
        "stream": True  # 开启流式传输
    }

    # 创建流式请求
    def generate():
        with requests.post(url, headers=headers, json=data, stream=True) as response:
            # 逐行读取响应数据
            for line in response.iter_lines():
                if line:
                    decoded_line = line.decode('utf-8')
                    # 解析响应
                    try:
                        message = decoded_line.strip()
                        print(message)  # 打印每行的响应
                        yield f"data: {message}\n\n"  # 每行数据通过 SSE 发送给前端
                    except Exception as e:
                        print("Error processing message:", e)

    return Response(generate(), content_type='text/event-stream')
