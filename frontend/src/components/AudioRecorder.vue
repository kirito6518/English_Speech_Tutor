<template>
  <div class="audio-recorder">
    <button 
      class="icon-button" 
      :class="{ recording: isRecording }"
      @click="toggleRecording"
    >
      <img 
        :src="require('@/assets/image/mic-icon.png')" 
        alt="录音" 
        class="button-icon"
      >
    </button>
  </div>
</template>

<script>
export default {
  name: 'AudioRecorder',
  emits: ['recognition-complete'],  // 显式声明组件发出的事件
  data() {
    return {
      isRecording: false,
      mediaRecorder: null,
      audioChunks: [],
      audioContext: null,
    }
  },
  methods: {
    async toggleRecording() {
      if (this.isRecording) {
        console.log('停止录音...');
        this.stopRecording2();
      } else {
        console.log('开始录音...');
        await this.startRecording2();
      }
    },

    async startRecording() {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ 
          audio: {
            channelCount: 1,
            sampleRate: 16000,
            sampleSize: 16,
            echoCancellation: false,  // 关闭回声消除
            noiseSuppression: false,  // 关闭噪声抑制
            autoGainControl: false    // 关闭自动增益
          } 
        });
        
        // 使用更兼容的格式
        const mimeType = 'audio/webm';
        this.mediaRecorder = new MediaRecorder(stream, {
          mimeType: mimeType,
          audioBitsPerSecond: 256000  // 提高比特率
        });
        
        this.audioChunks = [];

        this.mediaRecorder.ondataavailable = (event) => {
          this.audioChunks.push(event.data);
        };

        this.mediaRecorder.onstop = async () => {
          try {
            const audioBlob = new Blob(this.audioChunks, { type: mimeType });
            console.log('原始音频大小:', audioBlob.size);
            
            // 转换为WAV格式
            const wavBlob = await this.convertToWav(audioBlob);
            console.log('WAV音频大小:', wavBlob.size);
            
            await this.sendAudioToServer(wavBlob);
          } catch (error) {
            console.error('音频处理失败:', error);
            this.$emit('recognition-complete', '音频处理失败，请重试');
          }
        };

        // 设置更频繁的数据收集
        this.mediaRecorder.start(100);  // 每100ms收集一次数据
        this.isRecording = true;
      } catch (error) {
        console.error('录音失败:', error);
        alert('无法访问麦克风，请确保已授予麦克风访问权限。');
      }
    },

    // 将音频数据转换为WAV格式
    async convertToWav(audioBlob) {
      try {
        const arrayBuffer = await audioBlob.arrayBuffer();
        const audioContext = new (window.AudioContext || window.webkitAudioContext)({
          sampleRate: 16000  // 确保采样率为16000Hz
        });
        
        const audioBuffer = await audioContext.decodeAudioData(arrayBuffer);
        console.log('音频信息:', {
          sampleRate: audioBuffer.sampleRate,
          numberOfChannels: audioBuffer.numberOfChannels,
          duration: audioBuffer.duration
        });
        
        // 创建WAV文件
        const wavBuffer = this.audioBufferToWav(audioBuffer);
        return new Blob([wavBuffer], { type: 'audio/wav' });
      } catch (error) {
        console.error('音频转换失败:', error);
        throw error;
      }
    },

    // 将AudioBuffer转换为WAV格式
    audioBufferToWav(buffer) {
      const numOfChan = buffer.numberOfChannels;
      const length = buffer.length * numOfChan * 2;
      const buffer2 = new ArrayBuffer(44 + length);
      const view = new DataView(buffer2);
      const channels = [];
      let offset = 0;
      let pos = 0;

      // 写入WAV文件头
      this.writeString(view, 0, 'RIFF');
      view.setUint32(4, 36 + length, true);
      this.writeString(view, 8, 'WAVE');
      this.writeString(view, 12, 'fmt ');
      view.setUint32(16, 16, true);
      view.setUint16(20, 1, true);  // PCM格式
      view.setUint16(22, numOfChan, true);
      view.setUint32(24, 16000, true);  // 采样率固定为16000Hz
      view.setUint32(28, 16000 * 2 * numOfChan, true);  // 字节率
      view.setUint16(32, numOfChan * 2, true);  // 块对齐
      view.setUint16(34, 16, true);  // 位深度
      this.writeString(view, 36, 'data');
      view.setUint32(40, length, true);

      // 写入音频数据
      for (let i = 0; i < buffer.numberOfChannels; i++) {
        channels.push(buffer.getChannelData(i));
      }

      while (pos < buffer.length) {
        for (let i = 0; i < numOfChan; i++) {
          let sample = Math.max(-1, Math.min(1, channels[i][pos]));
          sample = (0.5 + sample < 0 ? sample * 32768 : sample * 32767) | 0;
          view.setInt16(44 + offset, sample, true);
          offset += 2;
        }
        pos++;
      }

      return buffer2;
    },

    writeString(view, offset, string) {
      for (let i = 0; i < string.length; i++) {
        view.setUint8(offset + i, string.charCodeAt(i));
      }
    },

    stopRecording() {
      if (this.mediaRecorder && this.isRecording) {
        this.mediaRecorder.stop();
        this.isRecording = false;
        this.mediaRecorder.stream.getTracks().forEach(track => track.stop());
      }
    },

    async sendAudioToServer(audioBlob) {
      try {
        const formData = new FormData();
        formData.append('audio', audioBlob, 'recording.wav');

        console.log('正在发送音频到服务器...');
        const response = await fetch('/api/audio/recognize', {
          method: 'POST',
          body: formData
        });

        const result = await response.json();
        console.log('服务器返回结果:', result);
        
        if (!response.ok) {
          throw new Error(result.error || '服务器错误2');
        }

        if (result.success) {
          // 发出识别完成事件，将识别结果发送给父组件
          console.log('[AudioRecorder] 发送识别结果到父组件:', result.text);
          
          // 尝试多种方式触发事件
          this.$emit('recognition-complete', result.text);
          console.log('[AudioRecorder] 事件已发出');
          
          // 延迟100ms后再次发送事件，确保Vue更新周期捕获它
          setTimeout(() => {
            console.log('[AudioRecorder] 延迟发送事件');
            this.$emit('recognition-complete', result.text);
          }, 100);
        } else {
          console.error('语音识别失败:', result.error);
          this.$emit('recognition-complete', '识别失败，请重试');
        }
      } catch (error) {
        console.error('发送音频文件失败:', error);
        this.$emit('recognition-complete', '识别失败，请重试');
      }
    },

    async stopRecording2() {
      try {
        console.log('正在发送音频到服务器2...');
        const response = await fetch('/api/audio/stop_and_recognize', {
          method: 'POST',
        });

        const result = await response.json();
        console.log('服务器返回结果:', result);
        
        if (!response.ok) {
          throw new Error(result.error || '服务器错误3');
        }
        this.isRecording = false;

        if (result.success) {
          // 发出识别完成事件，将识别结果发送给父组件
          console.log('[AudioRecorder] 发送识别结果到父组件:', result.text);
          
          // 尝试多种方式触发事件
          this.$emit('recognition-complete', result.text);
          console.log('[AudioRecorder] 事件已发出');
          
          // 延迟100ms后再次发送事件，确保Vue更新周期捕获它
          setTimeout(() => {
            console.log('[AudioRecorder] 延迟发送事件');
            this.$emit('recognition-complete', result.text);
          }, 100);
        } else {
          console.error('语音识别失败:', result.error);
          this.$emit('recognition-complete', '识别失败，请重试');
        }
      } catch (error) {
        console.error('发送音频文件失败:', error);
        this.$emit('recognition-complete', '识别失败，请重试');
      }
    },
    async startRecording2() {
      try {
        console.log('正在开始录音2...');
        const response = await fetch('/api/audio/start', {
          method: 'POST',
        });

        const result = await response.json();
        console.log('服务器返回结果:', result);
        
        if (!response.ok) {
          throw new Error(result.error || '服务器错误4');
        }
        this.isRecording = true;
      } catch (error) {
        console.error('发送音频文件失败:', error);
        this.$emit('recognition-complete', '识别失败，请重试');
      }
    },
  },
}
</script>

<style scoped>
.audio-recorder {
  display: inline-block;
}

.icon-button {
  width: 40px;
  height: 40px;
  cursor: pointer;
  background: none;
  border: none;
  padding: 8px;
  transition: transform 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  z-index: 1;
}

.button-icon {
  width: 24px;
  height: 24px;
  object-fit: contain;
}

.icon-button:hover {
  transform: scale(1.1);
}

.icon-button.recording {
  animation: pulse 1.5s infinite;
  filter: invert(48%) sepia(79%) saturate(2476%) hue-rotate(330deg) !important;
}

@keyframes pulse {
  0% {
    transform: scale(1);
  }
  50% {
    transform: scale(1.05);
  }
  100% {
    transform: scale(1);
  }
}
</style> 