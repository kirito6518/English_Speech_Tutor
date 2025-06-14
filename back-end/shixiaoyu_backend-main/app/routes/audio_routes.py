from flask import Blueprint, request, jsonify
from app.services.audio import AudioService
from datetime import datetime
import os

bp = Blueprint('audio', __name__, url_prefix='/api/audio')

@bp.route('/record', methods=['POST'])
def record_audio():
    try:
        # 获取前端传递的录音时长
        duration = request.json.get('duration', 5)  # 默认录音时长 5 秒
        
        # 获取当前时间并生成文件名
        file_name = "audio.wav"
        
        # 调用 AudioService 来录制音频
        AudioService.record_audio(file_name, duration)

        return jsonify({
            "message": "Recording completed successfully",
            "file_name": file_name
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@bp.route('/recognize', methods=['POST'])
def recognize_audio():
    try:
        # 获取音频文件名或文件本身（假设文件名来自前端请求）
        file_name = request.json.get('file_name')
        
        if not file_name:
            return jsonify({"error": "File name is required"}), 400
        
        # 调用 AudioService 来识别音频文件
        result = AudioService.recognize_audio(file_name)
        
        if result:
            return jsonify({"result": result}), 200
        else:
            return jsonify({"error": "Recognition failed"}), 500

    except Exception as e:
        return jsonify({"error": str(e)}), 500
