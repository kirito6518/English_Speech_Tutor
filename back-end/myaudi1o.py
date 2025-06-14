import pyaudio
import wave
import dashscope
from http import HTTPStatus
from dashscope.audio.asr import Transcription

# 设置API key
dashscope.api_key = 'sk-fecd4af8fab74a6d88572540dee60baf'

# 录音
def record_audio(filename, stop_event=None):
    CHUNK = 1024
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 16000

    audio = pyaudio.PyAudio()

    stream = audio.open(format=FORMAT, channels=CHANNELS,
                       rate=RATE, input=True,
                       frames_per_buffer=CHUNK)

    print("Recording...")
    frames = []
    
    try:
        while not (stop_event and stop_event.is_set()):
            data = stream.read(CHUNK)
            frames.append(data)
    except Exception as e:
        print(f"Recording error: {str(e)}")
    finally:
        stream.stop_stream()
        stream.close()
        audio.terminate()
        
        if frames:  # 只有在有录音数据时才保存文件
            wf = wave.open(filename, 'wb')
            wf.setnchannels(CHANNELS)
            wf.setsampwidth(audio.get_sample_size(FORMAT))
            wf.setframerate(RATE)
            wf.writeframes(b''.join(frames))
            wf.close()
            print('Recording saved')

# 识别
def recognize_audio(audio_file):
    try:
        print(f"正在识别文件: {audio_file}")
        
        # 检查文件
        import os
        if not os.path.exists(audio_file):
            print(f"错误：文件不存在: {audio_file}")
            return "识别失败"
            
        print("调用识别API...")
        response = Transcription.call(
            model='paraformer-v2',
            file_urls=[audio_file],  # 使用file_urls参数
            language_hints=['zh', 'en']
        )
        
        # 打印完整的返回结果，用于调试
        import json
        print("API返回结果:")
        print(json.dumps(response.output.__dict__, indent=2, ensure_ascii=False))
        
        if response.status_code == HTTPStatus.OK:
            try:
                # 按照正确的结构解析结果
                if hasattr(response.output, 'transcripts') and response.output.transcripts:
                    result = response.output.transcripts[0].text
                    print(f"识别成功，结果: {result}")
                    return result
                else:
                    print("错误：未找到识别结果")
                    return "识别失败"
            except Exception as e:
                print(f"解析结果时出错: {str(e)}")
                return "识别失败"
        else:
            print(f"识别失败: {response.message}")
            return "识别失败"
            
    except Exception as e:
        import traceback
        print(f"识别错误: {str(e)}")
        print(f"错误堆栈: {traceback.format_exc()}")
        return "识别失败"