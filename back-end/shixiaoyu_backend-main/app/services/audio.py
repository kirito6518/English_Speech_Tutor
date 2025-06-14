import requests
import pyaudio
import wave
import json
import base64

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
            return result["access_token"]
        else:
            print(f"获取access_token失败: {result.get('error_msg')}")
            return None

    @staticmethod
    def recognize_audio(audio_file_path):
        access_token = AudioService.get_access_token()  # 修正为正确调用方法
        if access_token is None:
            return  # 如果没有获取到access_token，则退出
        
        url = "https://vop.baidu.com/pro_api"

        # 打开音频文件并读取其二进制内容
        with open(audio_file_path, "rb") as audio_file:
            audio_data = audio_file.read()

        # 将二进制音频数据编码为base64
        audio_base64 = base64.b64encode(audio_data).decode('utf-8')

        # 准备请求的payload，传递音频数据的base64编码
        payload = json.dumps({
            "format": "wav",  # 确保与实际音频格式匹配
            "rate": 16000,
            "channel": 1,
            "cuid": "s2EMNsNdM13pVrKEpc4wUsuGa0cX0NS5",
            "dev_pid": 80001,  # 80001 表示普通话识别
            "token": access_token,
            "len": len(audio_data),  # 音频文件的长度
            "speech": audio_base64  # 直接传递音频数据的base64编码
        })
        
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        
        # 发起请求
        response = requests.post(url, headers=headers, data=payload.encode("utf-8"))
        
        # 输出响应结果
        print(response.text)

'''# 示例：录制并识别音频
file_name = 'test_audio.wav'
AudioService.record_audio(file_name, 5)  # 录制 5 秒音频
AudioService.recognize_audio(file_name)'''
