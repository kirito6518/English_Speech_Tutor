from flask import Blueprint, request, jsonify
from app.services.audio import AudioService
from datetime import datetime
import os
import pyaudio
import threading
import wave
import tempfile

bp = Blueprint('audio', __name__, url_prefix='/api/audio')

# 设置全局变量用于控制录音状态
is_recording = False
audio = pyaudio.PyAudio()
stream = None
frames = []

# 开始录音
@bp.route('/start', methods=['POST'])
def start_recording():
    global is_recording, stream, frames

    if is_recording:
        return jsonify({"message": "Recording is already in progress."}), 400

    # 初始化录音流
    is_recording = True
    CHUNK = 1024
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 16000

    stream = audio.open(format=FORMAT, channels=CHANNELS,
                        rate=RATE, input=True,
                        frames_per_buffer=CHUNK)
    
    frames = []
    
    def record():
        while is_recording:
            data = stream.read(CHUNK)
            frames.append(data)

    # 启动录音线程
    threading.Thread(target=record).start()

    return jsonify({"message": "Recording started"}), 200

# 停止录音
@bp.route('/stop', methods=['POST'])
def stop_recording():
    global is_recording, stream, frames

    if not is_recording:
        return jsonify({"message": "No recording in progress."}), 400

    # 停止录音
    is_recording = False
    stream.stop_stream()
    stream.close()

    # 保存录音文件
    file_name = "dynamic_audio.wav"
    with wave.open(file_name, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(audio.get_sample_size(pyaudio.paInt16))
        wf.setframerate(16000)
        wf.writeframes(b''.join(frames))

    return jsonify({
            "message": "Recording completed successfully",
            "file_name": file_name
        }), 200



@bp.route('/stop_and_recognize', methods=['POST'])
def stop_and_recognize():
    global is_recording, stream, frames

    if not is_recording:
        return jsonify({"message": "No recording in progress."}), 400

    # 停止录音
    is_recording = False
    stream.stop_stream()
    stream.close()

            # 创建临时文件保存上传的音频
    with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_file:
        # audio_file.save(temp_file.name)
        temp_file_path = temp_file.name

    # 保存录音文件
    with wave.open(temp_file_path, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(audio.get_sample_size(pyaudio.paInt16))
        wf.setframerate(16000)
        wf.writeframes(b''.join(frames))
    
    try:
        try:
            # 调用 AudioService 进行音频识别
            result = AudioService.recognize_audio(temp_file_path)
            
            # 如果识别结果不为空，返回成功结果
            if result and len(result) > 0:
                return jsonify({
                    "success": True,
                    "text": result[0]
                }), 200
            else:
                return jsonify({
                    "success": False,
                    "error": "识别失败，未能获取有效结果"
                }), 500

        finally:
            # 清理临时文件
            try:
                print(f"Rec File:{temp_file_path}")
                # os.unlink(temp_file_path)
            except Exception as e:
                print(f"清理临时文件失败: {str(e)}")

    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"处理音频文件时发生错误: {str(e)}"
        }), 500



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
        # 检查是否有文件上传
        if 'audio' not in request.files:
            return jsonify({
                "success": False,
                "error": "没有收到音频文件"
            }), 400

        audio_file = request.files['audio']
        
        # 创建临时文件保存上传的音频
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_file:
            audio_file.save(temp_file.name)
            temp_file_path = temp_file.name

        try:
            # 调用 AudioService 进行音频识别
            result = AudioService.recognize_audio(temp_file_path)
            
            # 如果识别结果不为空，返回成功结果
            if result and len(result) > 0:
                return jsonify({
                    "success": True,
                    "text": result[0]
                }), 200
            else:
                return jsonify({
                    "success": False,
                    "error": "识别失败，未能获取有效结果"
                }), 500

        finally:
            # 清理临时文件
            try:
                print(f"Rec File:{temp_file_path}")
                # os.unlink(temp_file_path)
            except Exception as e:
                print(f"清理临时文件失败: {str(e)}")

    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"处理音频文件时发生错误: {str(e)}"
        }), 500
