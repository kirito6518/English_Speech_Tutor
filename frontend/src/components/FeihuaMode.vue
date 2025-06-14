<template>
    <div class="body">
     <NavbarPage />
 

    <!-- 飞花令游戏 -->
    <div id="fly">
      

      <!-- 聊天区域 -->
      <div class="chat-container">
        <div class="game-status-scroll" v-show="showGameStatus || showKeyword">
          <div class="scroll-content">
            <div class="scroll-item" v-show="showKeyword">
              <span class="scroll-label">关键字</span>
              <span class="scroll-value">{{ currentKeyword }}</span>
            </div>
            <div class="scroll-divider">•</div>
            <div class="scroll-item" v-show="showGameStatus">
              <span class="scroll-label">当前关卡</span>
              <span class="scroll-value">{{ currentLevel }}</span>
            </div>
            <div class="scroll-divider">•</div>
            <div class="scroll-item" v-show="showGameStatus">
              <span class="scroll-label">目标</span>
              <span class="scroll-value">{{ levelTarget }}</span>
            </div>
            <div class="scroll-divider">•</div>
            <div class="scroll-item" v-show="showGameStatus">
              <span class="scroll-label">正确回答</span>
              <span class="scroll-value">{{ correctAnswers }}</span>
            </div>
          </div>
        </div>
        
        <div class="chat-content" id="chat-container">
          <div v-for="(message, index) in messages" :key="index" :class="['message', message.type]">
            <div class="message-content">{{ message.text }}</div>
          </div>
        </div>
      </div>

      <!-- 开始游戏按钮 -->
      <div class="start-game-container" v-if="!gameStarted">
        <button class="start-game" @click="startGame">开始游戏</button>
      </div>

      <!-- 输入区域 -->
      <div class="form-container" v-show="showInput">
        <input type="text" v-model="userInput" class="form-control" placeholder="输入你的回答"
               @keyup.enter="submitResponse">
        <button class="icon-button" @click="submitResponse">
          <img :src="require('@/assets/image/send-icon.png')" alt="发送" class="button-icon">
        </button>
        <AudioRecorder @recognition-complete="handleRecognitionResult" />
      </div>
    </div>

    <!-- 过关提示 -->
    <div class="overlay" v-show="showOverlay">
      <div class="gongxi">恭喜你通过了第 {{ currentLevel }} 关!</div>
      <button class="nextbutton" @click="nextLevel">进入下一关</button>
    </div>
  </div>


</template>

<script>
import { ref } from "vue";
import NavbarPage from './NavbarPage.vue';
import AudioRecorder from './AudioRecorder.vue';
import axios from 'axios';

export default {
  name: 'FeihuaMode',
  components: {
    NavbarPage,
    AudioRecorder
  },
  setup() {
    // 游戏数据
    const showKeyword = ref(false);
    const showGameStatus = ref(false);
    const showInput = ref(false);
    const showOverlay = ref(false);
    const gameStarted = ref(false);
    const messages = ref([]);
    const userInput = ref("");
    
    const currentKeyword = ref("");
    const currentLevel = ref(1);
    const levelTarget = ref("成功对答包含关键字的诗句");
    const correctAnswers = ref(0);
    const judgeResult = ref("");
    const sessionId = ref(""); // 保存会话ID
    const errorMessage = ref("");

    // 创建axios实例
    const api = axios.create({
      baseURL: '', // 使用相对路径，vue.config.js中已配置代理
      headers: {
        'Content-Type': 'application/json'
      }
    });

    // 开始游戏，创建新游戏
    const startGame = async () => {
      try {
        // 调用飞花令创建游戏接口
        const response = await api.post('/api/feihualing/create', {}, {
          headers: {
            'Content-Type': 'application/json'
          }
        });
        const gameData = response.data;
        
        // 保存会话ID和关键字
        sessionId.value = gameData.session_id;
        currentKeyword.value = gameData.keyword;
        
        // 显示游戏初始消息
        messages.value.push({
          type: 'ai',
          text: `欢迎参加飞花令游戏！本次关键字是"${currentKeyword.value}"，请说出一句包含"${currentKeyword.value}"字的诗句。`
        });
        
        // 更新游戏状态
        gameStarted.value = true;
        showGameStatus.value = true;
        showInput.value = true;
        showKeyword.value = true;
        correctAnswers.value = 0;
        errorMessage.value = "";
      } catch (error) {
        console.error("开始游戏失败:", error);
        messages.value.push({
          type: 'system',
          text: '开始游戏失败，请稍后再试。'
        });
        errorMessage.value = error.response?.data?.error || "服务器连接失败";
      }
    };

    // 提交用户回答
    const submitResponse = async () => {
      if (!userInput.value.trim()) return;
      
      // 添加用户回答到消息列表
      messages.value.push({
        type: 'user',
        text: userInput.value
      });
      
      const userResponseText = userInput.value;
      userInput.value = ''; // 清空输入框
      
      try {
        // 提交用户回答到后端
        const response = await api.post('/api/feihualing/submit', {
          session_id: sessionId.value,
          user_response: userResponseText
        }, {
          headers: {
            'Content-Type': 'application/json'
          }
        });
        
        const result = response.data;
        
        // 处理不同状态的响应
        if (result.status === 'success') {
          // AI成功回答
          messages.value.push({
            type: 'ai',
            text: result.ai_response
          });
          
          // 更新正确回答数
          correctAnswers.value++;
          errorMessage.value = "";
          
        } else if (result.status === 'failed') {
          // 用户回答不包含关键字
          messages.value.push({
            type: 'system',
            text: result.message
          });
          errorMessage.value = result.message;
          
        } else if (result.status === 'ai_failed') {
          // AI无法回答，更新关键字
          messages.value.push({
            type: 'ai',
            text: result.ai_response
          });
          
          // 更新关键字
          currentKeyword.value = result.new_keyword;
          messages.value.push({
            type: 'system',
            text: `关键字已更新为"${result.new_keyword}"`
          });
          console.log("更换了");
          errorMessage.value = "";
          
          // 完成一个关卡
          showOverlay.value = true;
        }
        
        // 检查是否过关（此处根据实际游戏逻辑可调整）
        if (correctAnswers.value >= 5 && !showOverlay.value) {
          showOverlay.value = true;
        }
      } catch (error) {
        console.error("提交回答失败:", error);
        messages.value.push({
          type: 'system',
          text: '提交回答失败，请稍后再试。'
        });
        errorMessage.value = error.response?.data?.error || "服务器连接失败";
      }
    };

    // 处理语音识别结果
    const handleRecognitionResult = (text) => {
      if (text) {
        userInput.value = text;
      }
    };

    // 进入下一关
    const nextLevel = () => {
      currentLevel.value++;
      showOverlay.value = false;
      
      // 更新关卡信息
      messages.value.push({
        type: 'system',
        text: `已进入第${currentLevel.value}关！继续使用关键字"${currentKeyword.value}"。`
      });
    };

    return {
      showKeyword,
      showGameStatus,
      showInput,
      showOverlay,
      gameStarted,
      messages,
      userInput,
      currentKeyword,
      currentLevel,
      levelTarget,
      correctAnswers,
      judgeResult,
      errorMessage,
      startGame,
      submitResponse,
      nextLevel,
      handleRecognitionResult
    };
  },
};
</script>

<style scoped>
.body {
  font-family: "宋体", sans-serif;
  background-color: #f8f4e9;
  margin: 0;
  padding: 0;
  min-height: 100vh;
  width: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  background-image: url('../assets/image/he.gif');
  background-size: cover;
  background-position: center;
  color: #333;
  background-repeat: repeat;
}

.container {
  width: 80%;
  margin: 20px auto;
  padding: 20px;
  background: linear-gradient(135deg, rgba(238, 226, 203, 0.95) 0%, rgba(245, 236, 220, 0.93) 100%);
  background-image: 
    linear-gradient(135deg, rgba(238, 226, 203, 0.95) 0%, rgba(245, 236, 220, 0.93) 100%),
    url("data:image/svg+xml,%3Csvg width='20' height='20' viewBox='0 0 20 20' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='%23614124' fill-opacity='0.08' fill-rule='evenodd'%3E%3Ccircle cx='3' cy='3' r='3'/%3E%3Ccircle cx='13' cy='13' r='3'/%3E%3C/g%3E%3C/svg%3E");
  border-radius: 20px;
  box-shadow: 0 4px 25px rgba(139, 69, 19, 0.12);
  border: 2px solid rgba(139, 69, 19, 0.25);
  position: relative;
  z-index: 1;
}

.chat-container {
  position: fixed;
  top: 120px;
  left: 50%;
  transform: translateX(-50%);
  width: 90%;
  max-width: 900px;
  height: calc(100vh - 280px);
  padding: 20px;
  background: rgba(255, 255, 255, 0.8);
  border-radius: 15px;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.05);
  margin: 0;
  overflow-y: auto;
}

.game-status-scroll {
  background: linear-gradient(to right, rgba(248, 244, 229, 0.2), rgba(248, 244, 229, 0.95), rgba(248, 244, 229, 0.2));
  padding: 15px 30px;
  margin: 0 auto 25px;
  border-radius: 12px;
  position: relative;
  overflow: hidden;
  border: 1px solid rgba(212, 175, 55, 0.3);
  max-width: 90%;
}

.game-status-scroll::before,
.game-status-scroll::after {
  content: '❖';
  position: absolute;
  top: 50%;
  transform: translateY(-50%);
  font-size: 20px;
  color: #D4AF37;
  opacity: 0.6;
}

.game-status-scroll::before {
  left: 10px;
}

.game-status-scroll::after {
  right: 10px;
}

.scroll-content {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 30px;
  font-family: "楷体", "KaiTi", serif;
}

.scroll-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  padding: 5px 15px;
  position: relative;
}

.scroll-item::after {
  content: '';
  position: absolute;
  bottom: -2px;
  left: 50%;
  transform: translateX(-50%);
  width: 80%;
  height: 1px;
  background: linear-gradient(90deg, transparent, #D4AF37, transparent);
  opacity: 0.3;
}

.scroll-label {
  font-size: 20px;
  color: #8B7355;
  letter-spacing: 1px;
}

.scroll-value {
  font-size: 20px;
  color: #B8860B;
  font-weight: bold;
  text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.1);
}

.scroll-divider {
  color: #D4AF37;
  opacity: 0.5;
  font-size: 16px;
  margin-top: 8px;
}

.chat-content {
  display: flex;
  flex-direction: column;
  gap: 15px;
  width: 100%;
  padding-bottom: 20px;
}
.message {
  display: flex;
  max-width: 80%;
  margin: 8px 0;
  animation: messageFloat 0.5s ease-out;
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
.message:hover {
  transform: none;
}
.message-content {
  padding: 12px 20px;
  border-radius: 15px;
  font-size: 18px;
  line-height: 1.5;
  word-break: break-word;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
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
.message.ai {
  margin-right: auto;
  justify-content: flex-start;
}
.message.ai .message-content {
  background: linear-gradient(135deg, #f5efe6 0%, #f8f4e9 100%);
  color: #614124;
  border: 1px solid rgba(139, 69, 19, 0.2);
  border-bottom-left-radius: 5px;
  font-family: "楷体", "KaiTi", serif;
  position: relative;
  padding-left: 35px;
}
.message.ai .message-content::before {
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
.message.system .message-content {
  background: linear-gradient(135deg, #f8d7da 0%, #f5c6cb 100%);
  color: #721c24;
  border: 1px solid rgba(114, 28, 36, 0.2);
  font-size: 16px;
  margin: 10px auto;
  text-align: center;
  max-width: 60%;
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
  box-shadow: 0 2px 10px rgba(0,0,0,0.1);
  padding: 15px 25px;
  display: flex;
  gap: 15px;
  align-items: center;
  z-index: 100;
}
.form-control {
  flex: 1;
  height: 45px !important;
  padding: 0 20px;
  border: none;
  border-radius: 30px;
  font-size: 16px;
  outline: none;
  background-color: #f5f5f5;
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
.start-game-container {
  position: absolute;
  left: 50%;
  top: 50%;
  transform: translate(-50%, -50%);
  width: 100%;
  text-align: center;
}
.start-game {
  padding: 15px 40px;
  background-color: #D4AF37;
  color: white;
  border: none;
  border-radius: 25px;
  cursor: pointer;
  font-size: 18px;
  transition: all 0.3s ease;
  box-shadow: 0 2px 10px rgba(0,0,0,0.1);
}
.start-game:hover {
  background-color: #B8960C;
  transform: scale(1.05);
}
.header-container {
  text-align: center;
  margin-bottom: 20px;
  padding-top: 20px;
  position: relative;
}

.fei-container {
  display: inline-block;
  position: relative;
  padding: 15px 30px;
  background: linear-gradient(135deg, rgba(255,255,255,0.8) 0%, rgba(255,255,255,0.9) 100%);
  border-radius: 20px;
  box-shadow: 0 4px 15px rgba(212, 175, 55, 0.15);
  border: 1px solid rgba(212, 175, 55, 0.2);
}

.fei {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
}

.fei-text {
  font-size: 46px;
  font-weight: bold;
  background: linear-gradient(120deg, #D4AF37 0%, #B8960C 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  font-family: "楷体", "KaiTi", serif;
}

.game-text {
  font-size: 32px;
  color: #666;
  font-weight: normal;
  margin-left: 5px;
}

.fei-decoration {
  position: absolute;
  bottom: -2px;
  left: 50%;
  transform: translateX(-50%);
  width: 60%;
  height: 2px;
  background: linear-gradient(90deg, transparent, #D4AF37, transparent);
}

.overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  z-index: 2000;
}
.gongxi {
  color: white;
  font-size: 24px;
  margin-bottom: 20px;
}
.nextbutton {
  padding: 10px 20px;
  background-color: #D4AF37;
  color: white;
  border: none;
  border-radius: 5px;
  cursor: pointer;
  font-size: 16px;
}
@keyframes recording-pulse {
  0% { transform: scale(1); }
  50% { transform: scale(1.2); }
  100% { transform: scale(1); }
}
.recording {
  animation: recording-pulse 1s infinite;
  filter: invert(48%) sepia(79%) saturate(2476%) hue-rotate(330deg) !important;
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
</style>

