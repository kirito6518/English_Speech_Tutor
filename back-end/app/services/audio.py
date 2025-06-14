import requests
import pyaudio
import wave
import json
import base64
import subprocess
import os
import tempfile

API_KEY = '9vNHYQw9YNSuGnUwTGtJ7rib'
SECRET_KEY = '8dUiPfOPv0dcWsHmoFnVOXQzkCJqti18'

# 录音
class AudioService:
    
    @staticmethod
    def record_audio(filename, duration):
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
        
        for i in range(0, int(RATE / CHUNK * duration)):
            data = stream.read(CHUNK)
            frames.append(data)

        stream.stop_stream()
        stream.close()
        audio.terminate()
        
        # 保存录制的音频
        wf = wave.open(filename, 'wb')
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(audio.get_sample_size(FORMAT))
        wf.setframerate(RATE)
        wf.writeframes(b''.join(frames))
        wf.close()
        
        print('Recording finished')

    @staticmethod
    def get_access_token():
        """
        使用 AK，SK 生成鉴权签名（Access Token）
        :return: access_token，或是None(如果错误)
        """
        url = "https://aip.baidubce.com/oauth/2.0/token"
        params = {"grant_type": "client_credentials", "client_id": API_KEY, "client_secret": SECRET_KEY}
        response = requests.post(url, params=params)
        
        result = response.json()
        
        if "access_token" in result:
            print("成功获取access_token")
            return result["access_token"]
        else:
            print(f"获取access_token失败: {result.get('error_msg')}")
            return None

    @staticmethod
    def convert_webm_to_wav(webm_path):
        """将webm格式转换为wav格式"""
        try:
            # 创建临时wav文件
            wav_path = tempfile.mktemp(suffix='.wav')
            
            # 使用ffmpeg进行转换
            command = [
                'ffmpeg',
                '-i', webm_path,
                '-acodec', 'pcm_s16le',  # 设置音频编码
                '-ar', '16000',          # 设置采样率
                '-ac', '1',              # 设置声道数
                '-y',                    # 覆盖已存在的文件
                wav_path
            ]
            
            # 执行转换命令
            subprocess.run(command, check=True, capture_output=True)
            
            return wav_path
        except Exception as e:
            print(f"音频转换失败: {str(e)}")
            return None

    @staticmethod
    def recognize_audio(audio_file_path):
        try:
            print(f"开始处理音频文件: {audio_file_path}")
            
            # 检查文件是否存在
            if not os.path.exists(audio_file_path):
                print(f"错误：文件不存在: {audio_file_path}")
                return None
                
            # 检查文件大小
            file_size = os.path.getsize(audio_file_path)
            print(f"音频文件大小: {file_size} 字节")
            
            access_token = AudioService.get_access_token()
            if access_token is None:
                print("获取access_token失败")
                return None
            
            url = "https://vop.baidu.com/pro_api"
            # url = "https://vop.baidu.com/server_api"

            # 打开音频文件并读取其二进制内容
            with open(audio_file_path, "rb") as audio_file:
                audio_data = audio_file.read()
                print(f"成功读取音频文件，数据长度: {len(audio_data)} 字节")

            # 将二进制音频数据编码为base64
            audio_base64 = base64.b64encode(audio_data).decode('utf-8')
            print("成功将音频数据转换为base64格式")

            # 准备请求的payload
            payload = json.dumps({
                "format": "wav",
                "rate": 16000,
                "channel": 1,
                "cuid": "s2EMNsNdM13pVrKEpc4wUsuGa0cX0NS5",
                "dev_pid": 80001,
                # "dev_pid": 1537,
                # "lan":"zh",
                "token": access_token,
                "len": len(audio_data),
                "speech": audio_base64
            })
            
            headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }
            
            print("开始发送识别请求...")
            # 发起请求
            response = requests.post(url, headers=headers, data=payload.encode("utf-8"))
            
            # 打印完整的响应内容用于调试
            print(f"API响应状态码: {response.status_code}")
            print(f"API响应内容: {response.text}")
            
            if response.status_code == 200:
                response_data = response.json()
                if 'result' in response_data:
                    print(f"识别结果: {response_data['result']}")
                    return response_data['result']
                else:
                    print(f"识别失败，API返回: {response_data}")
                    return None
            else:
                print(f"请求失败，状态码: {response.status_code}")
                print(f"错误信息: {response.text}")
                return None
                
        except Exception as e:
            print(f"识别过程中发生错误: {str(e)}")
            import traceback
            print(f"错误堆栈: {traceback.format_exc()}")
            return None
        finally:
            # 清理临时文件
            if 'wav_path' in locals() and os.path.exists(wav_path):
                try:
                    os.unlink(wav_path)
                except Exception as e:
                    print(f"清理临时文件失败: {str(e)}")

'''# 示例：录制并识别音频
file_name = 'test_audio.wav'
AudioService.record_audio(file_name, 5)  # 录制 5 秒音频
AudioService.recognize_audio(file_name)'''
