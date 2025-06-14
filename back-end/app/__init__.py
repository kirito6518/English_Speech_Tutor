from flask import Flask
from flask_cors import CORS
import secrets  # 用来生成随机的 secret_key

def create_app():
    app = Flask(__name__)

    # 设置 secret_key，用于加密 session 数据
    app.secret_key = secrets.token_hex(16)  # 使用 secrets 来生成随机的 secret_key

    # 初始化 CORS 扩展，允许所有来源访问
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    # 注册蓝图
    from .routes import audio_bp
    from .routes import chat_bp
    
    app.register_blueprint(audio_bp)
    app.register_blueprint(chat_bp)
    
    return app
