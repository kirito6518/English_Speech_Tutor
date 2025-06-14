from flask import Flask
from flask_cors import CORS
import logging
import sys
import secrets 

def create_app():
    # 配置日志
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('app.log')
        ]
    )
    logger = logging.getLogger(__name__)
    logger.info("开始创建Flask应用")

    app = Flask(__name__)

    # 初始化扩展
    logger.info("配置CORS")
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    logger.info("注册蓝图")
    from .routes import audio_bp, feihualing_bp, ninegrid_bp, recitation_bp,chat_bp
    
    app.secret_key = secrets.token_hex(16)
    
    app.register_blueprint(audio_bp)
    app.register_blueprint(feihualing_bp)
    app.register_blueprint(ninegrid_bp)
    app.register_blueprint(recitation_bp)
    app.register_blueprint(chat_bp)
    logger.info("Flask应用创建完成")
    return app
