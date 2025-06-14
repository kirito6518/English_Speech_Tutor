<template>
  <div class="body">
    <NavbarPage />

    <div class="welcome-banner">
       欢迎向诗小语提问诗词相关的内容吧！
    </div>

    <div id="digital-human-container">
      <iframe
        id="digitalHuman"
        :src="digitalHumanSrc"
        frameborder="0"
        allow="autoplay">
      </iframe>
      <div class="digital-human-controls">
        <button class="icon-button" @click="togglePlay">
          <img :src="isPlaying ? require('@/assets/image/stop-icon.png') : require('@/assets/image/play_icon.png')" alt="播放/停止">
        </button>
        <button class="icon-button" @click="toggleSettings">
          <img :src="require('@/assets/image/setting-icon.png')" alt="设置">
        </button>
      </div>
    </div>

    <div id="app" class="container">
      <div class="chat-container">
        <div class="learncard" id="chatHistory">
          <div v-for="(message, index) in messages" :key="index" :class="['message', message.type]">
            <div v-if="message.type === 'ai'" class="message-ai-container">
              <div 
                class="ai-content" 
                :class="{ collapsed: !message.expanded }"
                @click="toggleMessageExpand(message)"
              >
                <div v-if="!message.expanded" class="expand-prompt">
                  点击查看回复
                </div>
                <div v-else v-html="message.content"></div>
              </div>
              <button class="play-button" @click.stop="playMessage(message)">
                <img :src="require('@/assets/image/play_icon.png')" alt="播放">
              </button>
            </div>
            <div v-else class="message user">
              <div class="message-container">
                <div class="message-content">{{ message.content }}</div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="form-container">
        <input type="text" v-model="userInput" class="form-control" 
               placeholder="向诗小语提问吧！" @keyup.enter="sendMessage">
        <button class="icon-button" @click="sendMessage">
          <img :src="require('@/assets/image/send-icon.png')" alt="发送" class="button-icon">
        </button>
        <AudioRecorder @recognition-complete="handleRecognitionResult" />
      </div>
    </div>

    <!-- 设置面板 -->
    <div class="settings-panel" :class="{ hidden: !showSettings }">
      <button @click="toggleSettings" class="close-button">×</button>
      <h3>基础设置</h3>
      <div class="setting-item">
        <label>音量</label>
        <input type="range" v-model="settings.volume" min="0" max="100"
               @input="updateSettings('volume', $event.target.value)">
        <span>{{ settings.volume }}%</span>
      </div>
      <div class="setting-item">
        <label>语速</label>
        <input type="range" v-model="settings.speed" min="0" max="100"
               @input="updateSettings('speed', $event.target.value)">
        <span>{{ settings.speed }}%</span>
      </div>
      <div class="setting-item">
        <label>音调</label>
        <input type="range" v-model="settings.pitch" min="0" max="100"
               @input="updateSettings('pitch', $event.target.value)">
        <span>{{ settings.pitch }}%</span>
      </div>
      
      <h3>角色选择</h3>
      <div class="setting-item">
        <label>角色</label>
        <select v-model="settings.voice" @change="updateSettings('voice', $event.target.value)">
          <option value="aixia">爱夏-默认</option>
          <option value="chengcheng-neutral-plus">橙橙-知性</option>
          <option value="shasha-neutral-plus">莎莎-亲和</option>
          <option value="xiaodi-plus">晓迪-温柔</option>
        </select>
      </div>

      <h3>表情设置</h3>
      <div class="setting-item">
        <label>情绪</label>
        <select v-model="settings.faceEmotion" @change="updateSettings('faceEmotion', $event.target.value)">
          <option value="0">综合</option>
          <option value="1">高兴</option>
          <option value="2">悲伤</option>
          <option value="3">生气</option>
          <option value="4">惊讶</option>
          <option value="5">中立</option>
        </select>
      </div>

      <h3>动作设置</h3>
      <div class="setting-item">
        <label>风格</label>
        <select v-model="settings.motionStyle" @change="updateSettings('motionStyle', $event.target.value)">
          <option value="1">自然闲聊</option>
          <option value="2">通用演讲</option>
          <option value="3">通用讲解</option>
          <option value="4">丰富演讲</option>
          <option value="5">金姐演讲</option>
          <option value="6">可爱女生</option>
          <option value="7">站立直播</option>
          <option value="8">标准客服</option>
          <option value="10">主持人风格</option>
        </select>
      </div>

      <h3>形象设置</h3>
      <div class="setting-item">
        <label>形象</label>
        <select v-model="settings.character" @change="updateSettings('character', $event.target.value)">
          <option value="default">默认数字人</option>
          <option value="tiger">小老虎</option>
        </select>
      </div>

      <div class="control-buttons">
        <button @click="resetSettings" class="control-btn">重置设置</button>
      </div>
    </div>

    <!-- 加载提示 -->
    <div class="loading-overlay" :class="{ hidden: !loading }">
      <div class="loading-spinner"></div>
      <div class="loading-text">角色加载中...</div>
    </div>
  </div>
</template>
  
<script>
import NavbarPage from './NavbarPage.vue';
import AudioRecorder from './AudioRecorder.vue';
import { ref, reactive } from 'vue';
  
export default {
  name: 'LearnMode',
  components: {
    NavbarPage,
    AudioRecorder
  },
  setup() {
    const digitalHumanSrc = ref('https://avatar.deepscience.cn/v3/index.html?code=3lOGvbgeuL+PZWN0scNgwr2UpPyK+x0p0eLEJercNR+BbaJK7blPeGkpSbftayNSjQHrT3IvZsBmwUkz2xMSEAnW/46fo1pbt4QQX6su5UMEvCy/SqlWtL/dWrnSFM8W');
    const showSettings = ref(false);
    const loading = ref(false);
    const isRecording = ref(false);
    const userInput = ref('');
    const messages = ref([]);  // 不再初始化一个空的 AI 消息对象

    const streamMessages = ref([]);
    const settings = reactive({
      volume: 100,
      speed: 50,
      pitch: 50,
      voice: 'aixia',
      faceEmotion: '0',
      motionStyle: '1',
      character: 'default'
    });

    const isPlaying = ref(false);

    const toggleSettings = () => {
      showSettings.value = !showSettings.value;
    };

    const stopSpeaking = () => {
      // 实现停止说话的逻辑
      console.log('停止说话');
    };

    // 切换消息展开状态的方法
    const toggleMessageExpand = (message) => {
      message.expanded = !message.expanded;
    };

    const resetSettings = () => {
      Object.assign(settings, {
        volume: 100,
        speed: 50,
        pitch: 50,
        voice: 'aixia',
        faceEmotion: '0',
        motionStyle: '1',
        character: 'default'
      });
      // 实现重置设置的逻辑
      console.log('重置设置');
    };

    const sendMessage = () => {
  if (!userInput.value.trim()) {
    console.log('输入不能为空');
    return;  // 不发送请求
  }

  messages.value.push({
    type: 'user',
    content: userInput.value
  });

  // 调用 DeepSeek API
  startStream(userInput.value);
  userInput.value = '';  // 清空输入框
};

const startStream = (message) => {
  if (!message.trim()) return;

  const eventSource = new EventSource(`/api/chat/get_and_return?user_input=${encodeURIComponent(message)}`);

  eventSource.onmessage = (event) => {
    const jsonData = event.data.replace(/^data:\s*/, '');  // 去掉 "data: " 前缀
    try {
      const data = JSON.parse(jsonData);  // 解析去除前缀后的 JSON 数据
      const newContent = data.choices[0].delta.content;  // 提取 content 字段
      console.log(data);
      if (newContent) {
        // 如果没有消息，初始化一条消息
        if (messages.value.length === 0 || messages.value[messages.value.length - 1].type !== 'ai') {
          messages.value.push({
            type: 'ai',
            content: newContent, // 设置新消息的内容
            expanded: false // 添加展开状态标志
          });
        } else {
          // 否则，更新最后一条消息的内容
          messages.value[messages.value.length - 1].content += newContent;
        }
      }

      // 检查流是否结束
      if (data.choices[0].finish_reason === "stop") {
        speak(messages.value[messages.value.length - 1].content);
        console.log("流式数据传输已结束");
        eventSource.close();  // 结束流连接
      }
      
      // 强制更新视图
      messages.value = [...messages.value];  // 通过重新赋值数组引用来触发更新
    } catch (error) {
      console.error('JSON 解析错误:', error);
    }
  };

  eventSource.onerror = (error) => {
    console.error('Error in EventSource:', error);
    eventSource.close();  // 错误时关闭连接
  };
};



   
    const playMessage = (message) => {
      // 实现播放消息的逻辑
      console.log('播放消息:', message);
    };

    const togglePlay = () => {
      isPlaying.value = !isPlaying.value;
      if (isPlaying.value) {
        // 实现播放逻辑
        console.log('播放消息');
      } else {
        // 实现停止逻辑
        console.log('停止说话');
      }
    };

    const handleRecognitionResult = (text) => {
      console.log('[LearnMode] 收到识别结果:', text);
      if (text) {
        // 方法1: 使用ref直接设置
        userInput.value = text;
        console.log('[LearnMode] 已设置输入框值:', userInput.value);
        
        // 方法2: 尝试直接操作DOM
        setTimeout(() => {
          const input = document.querySelector('.form-container .form-control');
          if (input) {
            input.value = text;
            // 触发input事件以更新v-model
            input.dispatchEvent(new Event('input'));
            console.log('[LearnMode] 已通过DOM设置输入框值');
          }
        }, 10);
      }
    };
     // 在digitalHuman对象中添加角色配置
const characterConfigs = {
  default: {
    abName: 'default',
    voiceName: 'aixia',
    bodyMotion: 1,
    styleTag: 'Kefu',
    bsRatio: 1.5,
    head_x_rot: -10
  },
  yunxi: {
    abName: 'Assets/ABResources/KeFu02/NvKeFu02.prefab',
    voiceName: 'aixia',
    bodyMotion: 4,
    styleTag: 'Kefu',
    bsRatio: 1.5,
    head_x_rot: -10
  },
  majia: {
    abName: 'Assets/ABResources/Female/Female.prefab',
    voiceName: 'aixia',
    bodyMotion: 4,
    styleTag: 'Kefu',
    bsRatio: 1.5,
    head_x_rot: -10
  },
  xiaomeng: {
    abName: 'Assets/ABResources/XM01/Prefab/xiaomeng.prefab',
    voiceName: 'aixia',
    bodyMotion: 1,
    styleTag: 'CakeGirlJQJSA',
    bsRatio: 1.5,
    head_x_rot: -10
  },
  tiger: {
    abName: 'Assets/ABResources/Tiger/Prefab/laohu0113.prefab',
    voiceName: 'jielidou',
    bodyMotion: 1,
    styleTag: 'Kefu',
    bsRatio: 3,
    head_x_rot: -10
  },
  chuchu: {
    abName: 'Assets/ABResources/KeFu01/KeFu.prefab',
    voiceName: 'aixia',
    bodyMotion: 1,
    styleTag: 'Kefu',
    bsRatio: 3,
    head_x_rot: -10
  },
  nvqingnian: {
    abName: 'Assets/ABResources/girl_metaCloth_rig/girl_metaCloth_rig.prefab',
    voiceName: 'aixia',
    bodyMotion: 1,
    styleTag: 'Kefu',
    bsRatio: 3,
    head_x_rot: -10
  },
  xiaoke1: {
    abName: 'Assets/ABResources/KeFu04/Prefab/KeFu-4.prefab',
    voiceName: 'aixia',
    bodyMotion: 1,
    styleTag: 'Kefu',
    bsRatio: 1.5,
    head_x_rot: -10
  },
  xiaoke2: {
    abName: 'Assets/ABResources/NewTV/WeiLaiShaoNV/wlds.prefab',
    voiceName: 'aixia',
    bodyMotion: 1,
    styleTag: 'Kefu',
    bsRatio: 1.5,
    head_x_rot: -10
  },
  yisheng: {
    abName: 'Assets/ABResources/yisheng/yisheng.prefab',
    voiceName: 'aixia',
    bodyMotion: 1,
    styleTag: 'Kefu',
    bsRatio: 1.5,
    head_x_rot: -10
  }
};
    const updateSettings = (setting, value) => {
  // 假设 iframe 的 id 是 'digitalHuman'
  const iframe = document.getElementById('digitalHuman');
  if (!iframe || !iframe.contentWindow) return;

  switch (setting) {
    case 'volume':
      iframe.contentWindow.postMessage({ 
        type: 'AudioVolume', 
        data: value / 100 
      }, '*');
      break;
    case 'speed':
      iframe.contentWindow.postMessage({ 
        type: 'VoiceSpeed', 
        data: value 
      }, '*');
      break;
    case 'pitch':
      iframe.contentWindow.postMessage({ 
        type: 'VoiceFM', 
        data: value 
      }, '*');
      break;
    case 'voice':
      iframe.contentWindow.postMessage({
        type: 'VoiceName',
        data: value
      }, '*');
      break;
    case 'faceEmotion':
      iframe.contentWindow.postMessage({
        type: 'FaceEmotion',
        data: value
      }, '*');
      break;
    case 'motionStyle':
      iframe.contentWindow.postMessage({
        type: 'MotionStyle',
        data: value
      }, '*');
      break;
    case 'character':{
    const config = characterConfigs[value];
    console.log(config,value);
      iframe.contentWindow.postMessage({
        type: 'ChangeCharacter',
        data:  config.abName
      }, '*');
      break;
    }
    case 'body_fixed_hips':
      iframe.contentWindow.postMessage({
        type: 'BodyFixedHips',
        data: value
      }, '*');
      break;
    case 'faceType':
      iframe.contentWindow.postMessage({
        type: 'FaceType',
        data: value
      }, '*');
      break;
    // 可以根据需要添加更多设置项
  }
};


const speak = (text) => {
  const iframe = document.getElementById('digitalHuman');
  if (!iframe || !iframe.contentWindow) return;
console.log("开始说话");
  // 假设需要将文本发送到数字人
  iframe.contentWindow.postMessage({
    type: 'TextBroadcast',
    data: text,
    body_motion: settings.motionStyle,
      face_type: 1,
      face_tag: settings.faceEmotion,
      voice_name: settings.voice,
      is_first: false
    // 其他可能的参数，如声音设置
  }, '*');
};


    return {
      digitalHumanSrc,
      showSettings,
      loading,
      isRecording,
      userInput,
      messages,
      streamMessages,
      settings,
      toggleSettings,
      stopSpeaking,
      updateSettings,
      resetSettings,
      sendMessage,
      playMessage,
      isPlaying,
      togglePlay,
      toggleMessageExpand,
            handleRecognitionResult
    };
  }
};
</script>

<style scoped>
.body {
  font-family: "宋体", sans-serif;
  background-color: #f8f4e9;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  background-image: url('../assets/image/he.gif');
  background-size: cover;
  background-position: center;
  color: #333;
  background-repeat: repeat;
  min-height: 100vh;
  width: 100%;
}

.markdown-body {
  font-family: "Microsoft YaHei", "微软雅黑", sans-serif;
  padding: 15px;
  line-height: 1.6;
  border: 1px solid #ddd;
  border-radius: 8px;
  margin-bottom: 20px;
  background-color: #f9f9f9;
}

#digital-human-container {
  width: 30%;
  height: calc(100vh - 60px);
  position: fixed;
  left: 0;
  top: 60px;
  background: transparent;
  display: flex;
  flex-direction: column;
  margin-right: 5%;
}

#digitalHuman {
  width: 100%;
  height: calc(100% - 80px);
  background: transparent;
}

#app {
  width: 65%;
  height: calc(100vh - 60px);
  position: fixed;
  right: 0;
  top: 60px;
  padding: 20px;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
  align-items: center;
  overflow-x: hidden;
}

.chat-container {
  position: fixed;
  top: 20vh;  /* 从300px改为120px，更靠近顶部 */
  left: 50%;
  transform: translateX(-50%);
  width: 90%;
  max-width: 900px;
  height: 60vh;  /* 动态计算高度，留出顶部和底部空间 */
  padding: 20px;
  background: rgba(255, 255, 255, 0.8);
  border-radius: 15px;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.05);
  margin: 0;
  overflow-y: hidden;
  overflow-x: hidden;
}

.learncard {
  height: 100%;
  overflow-y:auto;  /* 改为auto，允许滚动 */
  padding: 10px;
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: flex-start;
  width: 100%;
  margin-bottom: 60px;  /* 添加底部边距，防止最后的消息被输入框遮挡 */
}

.learncard::-webkit-scrollbar {
  width: 8px;
}

.learncard::-webkit-scrollbar-track {
  background: rgba(241, 241, 241, 0.5);
  border-radius: 4px;
}

.learncard::-webkit-scrollbar-thumb {
  background: linear-gradient(to bottom, #D4AF37, #B8960C);
  border-radius: 4px;
  border: 2px solid transparent;
  background-clip: padding-box;
}

.learncard::-webkit-scrollbar-thumb:hover {
  background: linear-gradient(to bottom, #B8960C, #9A7B0A);
  border: 2px solid transparent;
  background-clip: padding-box;
}

.form-container {
  position: fixed;
  bottom: 30px;
  left: 50%;
  transform: translateX(-50%);
  width: 90%;
  max-width: 800px;
  background-color: #fff;
  border-radius: 30px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
  padding: 15px 25px;
  display: flex;
  gap: 15px;
  align-items: center;
  z-index: 100;
}

.form-control {
  flex: 1;
  height: 40px;
  padding: 0 20px;
  border: 1px solid rgba(0, 0, 0, 0.08);
  border-radius: 20px;
  font-size: 15px;
  outline: none;
  background-color: rgba(255, 255, 255, 0.9);
  transition: all 0.3s ease;
}

.form-control:focus {
  border-color: #D4AF37;
  background-color: #fff;
  box-shadow: 0 0 0 2px rgba(212, 175, 55, 0.1);
}

.icon-button {
  width: 40px;
  height: 40px;
  cursor: pointer;
  background: none;
  border: none;
  padding: 8px;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
}

.icon-button:hover {
  transform: scale(1.1);
  background: rgba(212, 175, 55, 0.1);
}

.icon-button img {
  width: 24px;
  height: 24px;
  object-fit: contain;
}

.play-button {
  display: none;
}

.digital-human-controls {
  position: relative;
  bottom: auto;
  right: auto;
  margin: 10px auto;
  display: flex;
  gap: 12px;
  padding: 8px 15px;
  background: rgba(255, 255, 255, 0.9);
  border-radius: 25px;
  backdrop-filter: blur(5px);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  z-index: 100;
}

.digital-human-controls .icon-button {
  width: 42px;
  height: 42px;
  background: rgba(255, 255, 255, 0.95);
  border-radius: 50%;
  transition: all 0.3s ease;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.05);
}

.digital-human-controls .icon-button:hover {
  background: rgba(212, 175, 55, 0.1);
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
}

.digital-human-controls .icon-button img {
  width: 22px;
  height: 22px;
}

.message {
  display: flex;
  max-width: 100%;
  margin: 8px 0;
  animation: messageFloat 0.5s ease-out;
  /* 添加浮动效果 */
}

@keyframes messageFloat {
  0% {
    opacity: 0;
    transform: translateY(20px);
  }

  100% {
    opacity: 1;
    transform: translateY(0);
  }
}

.message-container {
  display: flex;
  justify-content: center;
  /* 水平居中 */
  align-items: center;
  /* 垂直居中 */
  width: 100%;
  /* 容器宽度 */
  margin: 10px 0;
  /* 上下间距 */
}

.message-content {
  padding: 12px 20px;
  border-radius: 15px;
  font-size: 18px;
  line-height: 1.5;
  word-break: break-word;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  background: linear-gradient(135deg, #D4AF37 0%, #B8960C 100%);
  /* 用户消息背景 */
  color: white;
  /* 字体颜色 */
}

.ai-content {
  padding: 12px 20px;
  border-radius: 15px;
  font-size: 18px;
  line-height: 1.5;
  word-break: break-word;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  background: linear-gradient(135deg, #ffffff 0%, #f8f8f8 100%);
  color: #614124;
  border: 1px solid rgba(139, 69, 19, 0.2);
  border-bottom-left-radius: 5px;
  font-family: "楷体", "KaiTi", serif;
  position: relative;
  padding-left: 35px;
}

.ai-content::before {
  content: '诗';
  position: absolute;
  left: 10px;
  top: 50%;
  transform: translateY(-50%);
  color: #8B4513;
  font-size: 20px;
  font-weight: bold;
  opacity: 0.6;
}

/* 移除扭动动画 */
@keyframes aiWave {
  0%, 100% {
    transform: translateY(0);
  }
}

.message.ai {
  margin-right: auto;
  justify-content: flex-start;
}

.message.ai .ai-content:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  transform: translateY(-2px);
  transition: all 0.3s ease;
}

.message.user {
  margin-left: auto;
  justify-content: flex-end;
}

.message.user .message-content {
  background: linear-gradient(135deg, #D4AF37 0%, #B8960C 100%);
  color: white;
  border-bottom-right-radius: 5px;
  font-family: "宋体", sans-serif;
  transform-origin: right bottom;
  animation: userFloat 0.3s ease-out;
}

@keyframes userFloat {
  0% {
    opacity: 0;
    transform: translateY(10px);
  }
  100% {
    opacity: 1;
    transform: translateY(0);
  }
}

.message.user .message-content:hover {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

.settings-panel {
  position: absolute;
  left: 20px;
  bottom: 100px;
  width: 320px;
  background: rgba(255, 255, 255, 0.98);
  border-radius: 16px;
  padding: 20px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
  z-index: 1000;
  backdrop-filter: blur(10px);
  border: 1px solid rgba(212, 175, 55, 0.15);
}

.settings-panel h3 {
  color: #333;
  font-size: 16px;
  margin: 15px 0 10px;
  padding-bottom: 8px;
  border-bottom: 1px solid rgba(212, 175, 55, 0.2);
  position: relative;
}

.settings-panel h3:first-child {
  margin-top: 0;
}

.settings-panel h3::after {
  content: '';
  position: absolute;
  bottom: -1px;
  left: 0;
  width: 50px;
  height: 2px;
  background: linear-gradient(90deg, #D4AF37, transparent);
}

.setting-item {
  margin: 12px 0;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px;
  border-radius: 8px;
  transition: background-color 0.3s;
}

.setting-item:hover {
  background: rgba(212, 175, 55, 0.05);
}

.setting-item label {
  width: 45px;
  font-size: 14px;
  color: #666;
}

.setting-item input[type="range"] {
  flex: 1;
  height: 4px;
  background: #e0e0e0;
  border-radius: 2px;
  -webkit-appearance: none;
  cursor: pointer;
}

.setting-item input[type="range"]::-webkit-slider-thumb {
  -webkit-appearance: none;
  width: 12px;
  height: 12px;
  background: #D4AF37;
  border-radius: 50%;
  cursor: pointer;
  transition: all 0.3s;
}

.setting-item input[type="range"]::-webkit-slider-thumb:hover {
  transform: scale(1.2);
}

.setting-item input[type="range"]::-webkit-slider-thumb:focus {
  outline: none;
  border-color: #D4AF37;
  box-shadow: 0 0 0 2px rgba(212, 175, 55, 0.1);
}

.setting-item select {
  flex: 1;
  padding: 6px 10px;
  border-radius: 6px;
  border: 1px solid rgba(0, 0, 0, 0.1);
  font-size: 14px;
  color: #333;
  background: #fff;
  cursor: pointer;
  transition: all 0.3s;
}

.setting-item select:hover {
  border-color: #D4AF37;
}

.setting-item select:focus {
  outline: none;
  border-color: #D4AF37;
  box-shadow: 0 0 0 2px rgba(212, 175, 55, 0.1);
}

.setting-item span {
  min-width: 40px;
  text-align: right;
  font-size: 13px;
  color: #666;
}

.control-buttons {
  margin-top: 20px;
  padding-top: 15px;
  border-top: 1px solid rgba(212, 175, 55, 0.1);
  display: flex;
  gap: 10px;
}

.control-btn {
  flex: 1;
  padding: 8px 15px;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.3s;
  background: linear-gradient(135deg, #D4AF37 0%, #B8960C 100%);
  color: white;
  box-shadow: 0 2px 6px rgba(212, 175, 55, 0.2);
}

.control-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 8px rgba(212, 175, 55, 0.3);
}

.message-ai-container {
  width: 100%;
  margin-right: 0;
  display: flex;
  justify-content: center;
  align-items: center;
  position: relative;
}

.close-button {
  position: absolute;
  top: 10px;
  right: 10px;
  background: none;
  border: none;
  font-size: 20px;
  cursor: pointer;
  color: #333;
  transition: color 0.3s ease;
}

.close-button:hover {
  color: #D4AF37;
}

@import url('https://fonts.googleapis.com/css2?family=Noto+Serif+SC:wght@500&display=swap');

.welcome-banner {
  background: linear-gradient(to bottom, #fdf6e3, #f4e9d8);
  /* 仿古纸渐变背景 */
  color: #5b3a29;
  /* 深棕色字体 */
  font-size: 20px;
  font-family: 'Noto Serif SC', serif;
  /* 采用宋体或楷书风格 */
  font-weight: bold;
  text-align: center;
  padding: 15px 30px;
  margin: 20px auto;
  max-width: 600px;
  border: 4px solid #c4a484;
  /* 仿竹简边框 */
  border-radius: 10px;
  box-shadow: 5px 5px 15px rgba(0, 0, 0, 0.15);
  /* 轻微阴影 */
  position: relative;
}

.welcome-banner::before,
.welcome-banner::after {
  content: "";
  position: absolute;
  width: 40px;
  height: 40px;
  background-color: #c4a484;
  border-radius: 50%;
  top: 50%;
  transform: translateY(-50%);
}

.welcome-banner::before {
  left: -20px;
}

.welcome-banner::after {
  right: -20px;
}

.loading-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(255, 255, 255, 0.8);
  backdrop-filter: blur(5px);
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  z-index: 9999;
}

.loading-spinner {
  width: 50px;
  height: 50px;
  border: 5px solid #f3f3f3;
  border-top: 5px solid #D4AF37;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% {
    transform: rotate(0deg);
  }

  100% {
    transform: rotate(360deg);
  }
}

.hidden {
  display: none !important;
}

@keyframes recording-pulse {
  0% {
    transform: scale(1);
  }

  50% {
    transform: scale(1.2);
  }

  100% {
    transform: scale(1);
  }
}

.recording {
  animation: recording-pulse 1s infinite;
  filter: invert(48%) sepia(79%) saturate(2476%) hue-rotate(330deg) !important;
}

:deep(.welcome-message) {
  margin: 60px auto;
  width: 90%;
  max-width: 900px;
  display: flex;
  justify-content: center;
  align-items: center;
  position: relative;
  left: 50%;
  transform: translateX(-50%);
}

:deep(.welcome-inner) {
  background: linear-gradient(135deg, rgba(255, 250, 240, 0.98), rgba(252, 248, 240, 0.95));
  border-radius: 16px;
  padding: 40px 50px;
  text-align: center;
  width: 100%;
  box-shadow: 0 15px 35px rgba(0, 0, 0, 0.1);
  border: 1px solid rgba(212, 175, 55, 0.25);
  position: relative;
  overflow: auto;
}

:deep(.welcome-inner::before) {
  content: "";
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 4px;
  background: linear-gradient(90deg, transparent, rgba(212, 175, 55, 0.8), transparent);
}

:deep(.welcome-title) {
  font-size: 46px;
  color: #B8860B;
  font-family: "楷体", "KaiTi", serif;
  font-weight: bold;
  letter-spacing: 8px;
  margin-bottom: 20px;
  text-shadow: 1px 1px 3px rgba(0, 0, 0, 0.12);
  animation: fadeInDown 1.2s ease-out;
  text-align: center;
}

:deep(.welcome-subtitle) {
  font-size: 24px;
  color: #D4AF37;
  font-family: "楷体", "KaiTi", serif;
  letter-spacing: 5px;
  margin-bottom: 30px;
  opacity: 0.9;
  animation: fadeInUp 1.2s ease-out 0.3s both;
  text-align: center;
}

:deep(.welcome-content) {
  font-size: 28px;
  color: #8B4513;
  line-height: 1.6;
  margin: 30px 0;
  font-family: "楷体", "KaiTi", serif;
  animation: fadeIn 1.2s ease-out 0.6s both;
  text-align: center;
  display: block;
  width: 100%;
}

:deep(.quote-left),
:deep(.quote-right) {
  color: #D4AF37;
  font-size: 24px;
  vertical-align: middle;
  margin: 0 4px;
  opacity: 0.8;
}

:deep(.welcome-decoration) {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 12px;
  margin-top: 20px;
  color: #D4AF37;
  animation: fadeIn 1.2s ease-out 0.9s both;
}

:deep(.welcome-decoration .line) {
  font-size: 12px;
  opacity: 0.5;
}

:deep(.welcome-decoration .flower) {
  font-size: 18px;
  opacity: 0.9;
  animation: float 3s ease-in-out infinite;
}

@keyframes fadeInDown {
  from {
    opacity: 0;
    transform: translateY(-20px);
  }

  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }

  to {
    opacity: 0.9;
    transform: translateY(0);
  }
}

@keyframes fadeIn {
  from {
    opacity: 0;
  }

  to {
    opacity: 1;
  }
}

@keyframes float {

  0%,
  100% {
    transform: translateY(0);
  }

  50% {
    transform: translateY(-6px);
  }
}

/* 滚动条样式优化 */
.chat-container::-webkit-scrollbar {
  width: 8px;
}

.chat-container::-webkit-scrollbar-track {
  background: rgba(241, 241, 241, 0.5);
  border-radius: 4px;
}

.chat-container::-webkit-scrollbar-thumb {
  background: linear-gradient(to bottom, #D4AF37, #B8960C);
  border-radius: 4px;
  border: 2px solid transparent;
  background-clip: padding-box;
}

.chat-container::-webkit-scrollbar-thumb:hover {
  background: linear-gradient(to bottom, #B8960C, #9A7B0A);
  border: 2px solid transparent;
  background-clip: padding-box;
}

/* 折叠状态样式 */
.ai-content.collapsed {
  cursor: pointer;
  background: linear-gradient(135deg, #f0f0f0, #e0e0e0) !important;
  color: #666 !important;
  min-height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
}

/* 展开提示文字 */
.expand-prompt {
  font-size: 16px;
  font-weight: bold;
  color: #8B4513;
  text-align: center;
  padding: 10px;
}

/* 播放按钮位置调整 */
.play-button {
  position: absolute;
  right: 10px;
  bottom: 10px;
  z-index: 2;
}

/* 确保消息容器相对定位 */
.message-ai-container {
  position: relative;
}
</style>