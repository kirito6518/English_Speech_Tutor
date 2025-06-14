<template>
  <div class="body">
    <NavbarPage />

    <!-- 游戏规则页面 -->
    <transition name="fade">
      <div v-if="!gameStarted" class="rules-container">
        <div class="background-container">
          <p class="title">九宫格游戏</p>
          <p class="game-rule-text">
            游戏规则：每关游戏将给出一个九宫格，九宫格中包含一句五言或七言诗句，你需要找出正确的诗句。
            你可以在下方选择闯关模式。
            语音模式需要在10秒内说出正确的答案，注意：只有一次作答机会；
            点击模式需要在10秒内按顺序点击九宫格内的汉字卡片，如果点错了可以在作答区点击清除。
          </p>
          <p class="subtitle">你准备好接受挑战了吗？让我们开始吧！</p>

          <div class="mode-selection">
            <span :class="{ active: voiceMode }">语音模式</span>
            <button id="modeSelect" class="modeSelect" @click="toggleMode" :class="{ active: voiceMode }"></button>
            <span :class="{ active: !voiceMode }">点击模式</span>
          </div>

          <button class="start-game-btn" @click="startGame">开始游戏</button>
        </div>
      </div>
    </transition>

    <!-- 游戏内容页面 -->
    <transition name="fade">
      <div v-if="gameStarted" class="game-content">
        <div v-if="showError" class="error-message">{{ errorMessage }}</div>
        <div class="game-card-container">
          <div v-for="(question, index) in currentPageQuestions" :key="index" class="game-card">
            <div class="level">第{{ index + 1 + (currentPage - 1) * 10 }}关</div>
            <img :src="require(`@/assets/image/game${(index % 10) + 1}.png`)" style="border-radius: 20px; width: 100%; height: auto; cursor: pointer;"
              @click="showOverlay(index + (currentPage - 1) * 10)">
            <div class="game-item" :style="getStyle(index + (currentPage - 1) * 10)"></div>
          </div>
        </div>

        <div class="page">
          <el-pagination background layout="prev, pager, next" :total="totalOfGame" class="mt-4" :page-size="10"
            :current-page="currentPage" @current-change="handlePageChange"></el-pagination>
        </div>

        <button class="back-to-rules-btn" @click="backToRules">返回规则</button>
      </div>
    </transition>

    <!-- Overlay -->
    <div v-if="isOverlayVisible" class="overlay" @click.self="hideOverlay">
      <div class="overlay-content">
        <!-- 添加倒计时显示 -->
        <div class="countdown-display" v-if="countdown.isActive">
          剩余时间：{{ countdown.time }}秒
        </div>
        
        <!-- 添加时间到显示 -->
        <div v-if="showAnswer && !gameResult.isCorrect" class="timeout-message">
          <div>时间到！</div>
          <div class="correct-answer-text">
            正确答案: {{ gameResult.correctAnswer }}
          </div>
        </div>

        <!-- Game Question -->
        <div class="boardOfNine">
          <button class="close-button" @click="hideOverlay">&times;</button>

          <!-- 点击模式 -->
          <div v-if="!voiceMode">
            <div class="grid-item">
              <div v-for="(row, rowIndex) in gameSession.currentQuestion.title" :key="rowIndex"
                class="grid-row">
                <button v-for="(item, colIndex) in row" :key="colIndex" @click="addToAnswer(item)" class="grid-button"
                  :class="{ 'correct-grid': gameResult.isCorrect, 'wrong-grid': gameResult.userAnswer && !gameResult.isCorrect }">
                  {{ item }}
                </button>
              </div>
            </div>

            <!-- Answer area -->
            <div class="answer">
              <div v-for="(answer, index) in answerArray" :key="index" @click="removeFromAnswer(answer)">
                <button class="answer-button" :class="{ 'correct-answer-btn': gameResult.isCorrect }">{{ answer }}</button>
              </div>
            </div>
            
            <!-- 答案反馈区 -->
            <div v-if="gameResult.isCorrect" class="success-message">
              <div class="success-icon">✓</div>
              <div>恭喜，回答正确!</div>
              <div class="correct-answer-text">
                正确答案: {{ gameResult.correctAnswer }}
              </div>
            </div>
            
            <div v-else-if="gameResult.userAnswer && !gameResult.isCorrect" class="error-feedback">
              <div>再试试看，你可以的!</div>
              <div class="user-answer">您的答案: {{ gameResult.userAnswer }}</div>
            </div>
          </div>

          <!-- 语音模式 -->
          <div v-else>
            <div class="grid-item">
              <div v-for="(row, rowIndex) in gameSession.currentQuestion.title" :key="rowIndex"
                class="grid-row">
                <div v-for="(item, colIndex) in row" :key="colIndex" class="grid-button">
                  {{ item }}
                </div>
              </div>
            </div>

            <!-- Answer area -->
            <div class="answer">
              <div v-for="(answer, index) in answerArray" :key="index">
                <button class="answer-button">{{ answer }}</button>
              </div>
            </div>

            <!-- Start Recording Button -->
            <div v-if="!isRecording">
              <button @click="startRecording" class="start-recording-btn">开始录音</button>
            </div>
            <div v-else>
              <p>正在录音... 10秒倒计时</p>
            </div>
            
            <!-- 答案反馈区 -->
            <div v-if="gameResult.isCorrect" class="success-message">
              <div class="success-icon">✓</div>
              <div>恭喜，回答正确!</div>
              <div class="correct-answer-text">
                正确答案: {{ gameResult.correctAnswer }}
              </div>
            </div>
            
            <div v-else-if="gameResult.userAnswer && !gameResult.isCorrect" class="error-feedback">
              <div>再试试看，你可以的!</div>
              <div class="user-answer">您的答案: {{ gameResult.userAnswer }}</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import NavbarPage from './NavbarPage.vue';
import axios from 'axios';

export default {
  name: 'GamePage',
  data() {
    return {
      gameStarted: false,  // 控制游戏是否开始
      voiceMode: false, // Controls the mode, true for voice mode, false for click mode
      isOverlayVisible: false, // 控制蒙版显示/隐藏
      currentIndex: null, // 记录当前点击的卡片索引
      
      // 游戏状态数据
      gameSession: {
        sessionId: null,
        currentQuestion: null,
        questionNumber: 0,
        totalQuestions: 0,
        score: 0,
        gameCompleted: false,
        allQuestions: [] // 存储所有题目信息
      },
      
      // 保存每个关卡的游戏会话数据
      levelGameSessions: {},
      
      // 页面加载状态
      pagesLoaded: {},
      
      // 页面显示数据
      questionsOfGridData: [],
      totalOfGame: 50,
      currentPage: 1,
      answerArray: [], // Store the answers
      stateOfGrid: Array(50).fill(1), // 初始状态都是未完成
      isRecording: false,
      
      // 错误状态
      errorMessage: '',
      showError: false,
      
      // 游戏结果
      gameResult: {
        isCorrect: false,
        correctAnswer: '',
        message: '',
        userAnswer: ''
      },
      countdown: {
        time: 10,
        timer: null,
        isActive: false
      },
      showAnswer: false
    }
  },
  components: {
    NavbarPage
  },
  mounted() {
    // 加载第一页的九宫格题目
    this.loadQuestionsForPage(1);
    this.pagesLoaded[1] = true;
    console.log('初始化加载第1页数据');
  },
  computed: {
    currentPageQuestions() {
      console.log('计算当前页显示数据，当前页:', this.currentPage, '数据长度:', this.questionsOfGridData.length);
      
      if (this.questionsOfGridData.length === 0) {
        console.log('当前没有题目数据，返回空数组');
        return [];
      }
      
      // 确保每页显示10个问题
      const questionsPerPage = 10;
      const result = [];
      
      for (let i = 0; i < questionsPerPage; i++) {
        if (i < this.questionsOfGridData.length) {
          result.push(this.questionsOfGridData[i]);
        } else {
          // 如果数据不足，添加默认问题
          result.push({
            id: `question_default_${i}`,
            question: [
              ['空', '空', '空'],
              ['空', '空', '空'],
              ['空', '空', '空']
            ],
            answer: '默认题目'
          });
        }
      }
      
      console.log('当前页显示', result.length, '个问题');
      return result;
    }
  },
  methods: {
    startGame() {
      this.gameStarted = true;
    },
    backToRules() {
      this.gameStarted = false;
    },
    // 加载指定页的九宫格题目
    loadQuestionsForPage(page) {
      console.log('加载第', page, '页的九宫格题目');
      
      // 如果该页已经加载过，则不重复生成
      if (this.pagesLoaded[page]) {
        console.log('该页已加载过，使用缓存数据');
        return;
      }
      
      // 生成模拟的九宫格数据，每页10关
      const mockQuestions = [];
      for (let i = 0; i < 10; i++) {
        const index = (page - 1) * 10 + i;
        mockQuestions.push({
          id: `question_${index}`,
          question: [
            ['春', '眠', '不'],
            ['觉', '晓', '处'],
            ['闻', '啼', '鸟']
          ],
          answer: '春眠不觉晓，处处闻啼鸟'
        });
      }
      
      // 更新本页的问题数据
      this.questionsOfGridData = mockQuestions;
      
      // 标记该页已加载
      this.pagesLoaded[page] = true;
      
      console.log('页面数据加载完成，生成了', mockQuestions.length, '个问题');
    },
    
    // 创建新游戏
    async createGame() {
      try {
        // 如果已有会话ID，则重用
        if (this.gameSession.sessionId) {
          console.log('使用现有游戏会话:', this.gameSession.sessionId);
          return true;
        }
        
        console.log('创建新游戏会话');
        // 调用创建游戏API
        const response = await axios.post('/api/ninegrid/create', {}, {
          headers: {
            'Content-Type': 'application/json'
          }
        });
        
        const gameData = response.data;
        console.log('创建游戏响应:', gameData);
        
        // 保存游戏会话信息
        this.gameSession = {
          sessionId: gameData.session_id,
          currentQuestion: gameData.question,
          questionNumber: gameData.question_number,
          totalQuestions: gameData.total_questions,
          score: gameData.score,
          gameCompleted: false,
          allQuestions: [] // 会在提交答案时获取
        };
        
        return true;
      } catch (error) {
        console.error('创建游戏失败:', error);
        this.showErrorMessage('创建游戏失败，请稍后再试');
        return false;
      }
    },
    
    // 提交用户答案
    async submitAnswer(userAnswer) {
      try {
        // 如果已经回答正确，不再提交
        if (this.gameResult.isCorrect) {
          console.log('已经回答正确，不再提交');
          return;
        }
        
        console.log('提交答案:', userAnswer, '当前关卡索引:', this.currentIndex);
        
        // 调用提交答案API
        const response = await axios.post('/api/ninegrid/submit', {
          session_id: this.gameSession.sessionId,
          answer: userAnswer,
          question_index: this.currentIndex // 添加题目索引参数
        }, {
          headers: {
            'Content-Type': 'application/json'
          }
        });
        
        console.log('服务器响应:', response.data);
        
        const result = response.data;
        
        // 更新游戏状态
        this.gameSession.score = result.score;
        this.gameSession.allQuestions = result.all_questions;
        this.gameSession.currentQuestion = result.current_question;
        this.gameSession.questionNumber = result.question_number;
        
        console.log('是否正确:', result.is_correct);
        
        // 明确设置游戏结果状态
        this.gameResult.isCorrect = result.is_correct;
        this.gameResult.correctAnswer = result.correct_answer;
        this.gameResult.userAnswer = result.recognized_text;
        this.gameResult.message = result.is_correct ? 
          '回答正确！' : 
          `回答错误！正确答案是：${result.correct_answer}`;
        
        console.log('更新后的游戏结果状态:', this.gameResult);
        
        // 如果答对了，清除倒计时
        if (result.is_correct) {
          this.clearCountdown();
          this.stateOfGrid[this.currentIndex] = 0;
          this.finalScore(true);
        } else {
          // 显示错误信息
          //this.showErrorMessage(`答案不正确，再试试吧！`);
        }
        
        // 更新关卡的游戏会话数据
        this.levelGameSessions[this.currentIndex] = JSON.parse(JSON.stringify(this.gameSession));
      } catch (error) {
        console.error('提交答案失败:', error);
        this.showErrorMessage('提交答案失败，请稍后再试');
      }
    },
    
    // 显示错误消息
    showErrorMessage(message) {
      this.errorMessage = message;
      this.showError = true;
      setTimeout(() => {
        this.showError = false;
      }, 3000);
    },
    
    // 显示九宫格题目
    async showOverlay(index) {
      console.log('打开关卡:', index, '所在页:', Math.floor(index / 10) + 1);
      this.currentIndex = index; // Set the current question index
      
      // 重置游戏结果状态
      this.gameResult.isCorrect = false;
      this.gameResult.correctAnswer = '';
      this.gameResult.userAnswer = '';
      this.gameResult.message = '';
      
      // 检查该关卡是否已有游戏会话数据
      if (!this.levelGameSessions[index]) {
        // 如果游戏会话不存在，创建新的游戏会话
        if (!this.gameSession.sessionId) {
          // 创建新游戏
          const success = await this.createGame();
          if (!success) return;
        }
        
        console.log('创建关卡数据，关卡索引:', index);
        // 保存当前关卡的游戏会话数据
        this.levelGameSessions[index] = JSON.parse(JSON.stringify(this.gameSession));
      } else {
        console.log('使用已有关卡数据，关卡索引:', index);
        // 使用之前保存的游戏会话数据
        this.gameSession = JSON.parse(JSON.stringify(this.levelGameSessions[index]));
      }
      
      // 获取当前关卡的题目
      try {
        console.log('获取题目，关卡索引:', index, '会话ID:', this.gameSession.sessionId);
        
        // 确保游戏会话ID存在
        if (!this.gameSession.sessionId) {
          console.error('游戏会话ID不存在，无法获取题目');
          this.showErrorMessage('游戏初始化失败，请刷新页面重试');
          return;
        }
        
        // 提交一个空答案来获取当前关卡的题目
        const response = await axios.post('/api/ninegrid/submit', {
          session_id: this.gameSession.sessionId,
          answer: '',  // 空答案，只是为了获取题目
          question_index: index // 明确指定要获取的题目索引
        }, {
          headers: {
            'Content-Type': 'application/json'
          }
        });
        
        console.log('获取题目响应(完整数据):', JSON.stringify(response.data));
        const result = response.data;
        
        // 打印关键数据
        console.log('当前题目原始数据:', result.current_question);
        console.log('题目标题类型:', typeof result.current_question.title);
        if (Array.isArray(result.current_question.title)) {
          console.log('题目是数组, 长度:', result.current_question.title.length);
          if (result.current_question.title.length > 0) {
            console.log('第一个元素类型:', typeof result.current_question.title[0]);
          }
        }
        
        // 确保currentQuestion存在并且有正确结构
        if (!result.current_question) {
          result.current_question = {
            title: [['','',''],['','',''],['','','']],
            answer: ''
          };
        }
        
        // 确保currentQuestion.title是二维数组格式
        if (result.current_question && result.current_question.title) {
          // 检查title是否已经是二维数组
          const title = result.current_question.title;
          
          console.log('原始title数据:', JSON.stringify(title));
          
          // 确保title是二维数组
          let formattedTitle;
          if (Array.isArray(title) && Array.isArray(title[0])) {
            // 已经是二维数组，不需要转换
            formattedTitle = title;
          } else if (Array.isArray(title)) {
            // 一维数组，转为3x3格式
            // 检查数组长度是否为9
            if (title.length === 9) {
              formattedTitle = [
                title.slice(0, 3),
                title.slice(3, 6),
                title.slice(6, 9)
              ];
            } else {
              // 如果长度不是9，尝试取前9个元素或填充
              const normalizedArray = [...title];
              while (normalizedArray.length < 9) {
                normalizedArray.push('');
              }
              formattedTitle = [
                normalizedArray.slice(0, 3),
                normalizedArray.slice(3, 6),
                normalizedArray.slice(6, 9)
              ];
            }
          } else if (typeof title === 'string') {
            // 字符串，转为3x3格式
            const chars = title.split('');
            // 确保长度为9
            while (chars.length < 9) {
              chars.push('');
            }
            formattedTitle = [
              chars.slice(0, 3),
              chars.slice(3, 6),
              chars.slice(6, 9)
            ];
          } else {
            // 未知格式，使用默认空二维数组
            formattedTitle = [['','',''],['','',''],['','','']];
            console.error('未知的title格式:', typeof title, title);
          }
          
          console.log('格式化后的title:', JSON.stringify(formattedTitle));
          
          // 更新题目
          result.current_question.title = formattedTitle;
        }
        
        // 更新当前题目
        this.gameSession.currentQuestion = result.current_question;
        this.gameSession.questionNumber = result.question_number;
        this.gameSession.score = result.score;
        this.gameSession.allQuestions = result.all_questions || [];
        
        // 打印当前题目格式
        console.log('最终题目数据:', JSON.stringify(this.gameSession.currentQuestion));
        
        // 更新关卡的游戏会话数据
        this.levelGameSessions[index] = JSON.parse(JSON.stringify(this.gameSession));
      } catch (error) {
        console.error('获取题目失败:', error);
        this.showErrorMessage('获取题目失败，请稍后再试');
        return;
      }
      
      // 清空答案数组
      this.answerArray = [];
      
      // 在获取题目后启动倒计时
      this.startCountdown();
      
      // 显示九宫格
      this.isOverlayVisible = true;
      
      if (this.voiceMode) {
        this.startRecording();
      }
    },
    
    hideOverlay() {
      this.isOverlayVisible = false;
      this.answerArray = [];
      this.clearCountdown();  // 清理倒计时
    },
    
    // 点击模式：添加字符到答案
    addToAnswer(item) {
      // 如果已经回答正确，不再添加新字符
      if (this.gameResult.isCorrect) {
        return;
      }
      
      this.answerArray.push(item); // 将用户点击的字符添加到答案数组
      
      // 在每次添加字符后检查答案
      if (this.gameSession && this.gameSession.currentQuestion) {
        // 组合用户当前输入的答案
        const userAnswer = this.answerArray.join('');
        
        // 每输入一个字符就尝试检查答案，不管长度
        this.checkAnswerMatching(userAnswer);
      }
    },
    
    // 添加新方法，不调用API而是在前端检查匹配
    checkAnswerMatching(userAnswer) {
      if (!this.gameSession || !this.gameSession.currentQuestion) return;
      
      console.log('检查答案:', userAnswer);
      console.log('答案长度:', userAnswer.length);
      
      // 如果输入的字符足够多（至少5个字符），尝试提交到服务器
      if (userAnswer.length >= 5) {
        console.log('提交答案到服务器');
        this.submitAnswer(userAnswer);
      }
    },
    
    // 点击模式：从答案中移除字符
    removeFromAnswer(item) {
      const index = this.answerArray.indexOf(item);
      if (index > -1) {
        this.answerArray.splice(index, 1); // 从答案中移除选中的按钮
      }
    },
    
    // 检查答案并提交
    checkAndSubmitAnswer() {
      if (this.answerArray.length === 0) {
        this.showErrorMessage('请输入答案');
        return;
      }
      
      // 组合用户输入的答案
      const userAnswer = this.answerArray.join('');
      
      // 提交答案
      this.submitAnswer(userAnswer);
    },
    
    // 显示游戏结果
    finalScore(isWin) {
      console.log('调用finalScore, isWin:', isWin);
      
      if (isWin) {
        // 确保游戏结果状态被设置为正确
        this.gameResult.isCorrect = true;
        console.log('finalScore设置游戏状态为正确:', this.gameResult);
        
        // 直接向界面显示消息
        //this.showSuccessMessage('恭喜，回答正确!');
      } else {
        // 不显示错误信息
        return;
      }
      // 不关闭弹窗，让用户自己关闭
    },
    
    // 设置游戏卡片的样式
    getStyle(index) {
      const state = this.stateOfGrid[index];
      return {
        backgroundImage: state === 1
          ? 'url(/image/before.png)'
          : 'url(/image/win.png)',
        width: '30px',
        height: '30px',
        backgroundSize: 'contain',
        backgroundRepeat: 'no-repeat',
        backgroundPosition: 'center',
        padding: '5px'
      };
    },
    
    // 更新页面
    handlePageChange(newPage) {
      console.log('切换到第', newPage, '页');
      this.currentPage = newPage;  // 更新当前页
      
      // 确保当前页有数据
      this.loadQuestionsForPage(newPage);
      
      // 如果缓存中没有该页数据，重新生成
      if (!this.questionsOfGridData || this.questionsOfGridData.length === 0) {
        console.log('当前页数据为空，重新生成数据');
        // 生成模拟的九宫格数据，每页10关
        const mockQuestions = [];
        for (let i = 0; i < 10; i++) {
          const index = (newPage - 1) * 10 + i;
          mockQuestions.push({
            id: `question_${index}`,
            question: [
              ['春', '眠', '不'],
              ['觉', '晓', '处'],
              ['闻', '啼', '鸟']
            ],
            answer: '春眠不觉晓，处处闻啼鸟'
          });
        }
        
        // 更新本页的问题数据
        this.questionsOfGridData = mockQuestions;
        
        console.log('页面切换：已重新生成数据，长度为', mockQuestions.length);
      }
    },
    
    // 切换游戏模式
    toggleMode() {
      this.voiceMode = !this.voiceMode;
    },
    
    // 录音功能
    startRecording() {
      this.isRecording = true;  // Set recording status to true
      this.timer = setTimeout(() => {
        this.stopRecording();  // Automatically stop recording after 10 seconds
      }, 10000);  // 10 seconds

      // Use axios to send POST request
      axios.post('/api/audio/record', { duration: 10 })
        .then(response => {
          if (response.data.file_name) {
            console.log("Recording completed. File saved as: " + response.data.file_name);
            // Perform further actions with the recorded file name
            this.startRecognition(response.data.file_name);
          } else {
            console.log("Error recording audio:", response.data);
          }
        })
        .catch(error => {
          console.error("Error starting recording:", error);
        });
    },

    stopRecording() {
      this.isRecording = false;  // Stop recording
      console.log('Recording stopped automatically after 10 seconds.');
    },

    startRecognition(fileName) {
      fetch('/api/audio/recognize', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ file_name: fileName })
      })
        .then(response => response.json())
        .then(data => {
          if (data.result) {
            console.log("Recognition result:", data.result);
            // 去掉标点符号并更新 data.result
            const cleanResult = data.result.replace(/[，。？！；：""''【】()（）《》、，。、。]/g, '');

            // 将去掉标点后的每个字符添加到 answerArray 中
            for (const char of cleanResult) {
              this.answerArray.push(char);
            }

            // 提交语音识别的答案
            this.submitAnswer(cleanResult);

          } else {
            console.log("Error during recognition:", data);
          }
        })
        .catch(error => {
          console.error("Error starting recognition:", error);
        });
    },

    // 添加一个显示成功消息的方法
    showSuccessMessage(message) {
      // 使用轻量级的提示，不影响游戏界面
      this.errorMessage = message;
      this.showError = true;
      setTimeout(() => {
        this.showError = false;
      }, 3000);
    },
    
    // 开始倒计时
    startCountdown() {
      this.countdown.time = 10;
      this.countdown.isActive = true;
      this.showAnswer = false;
      
      // 清除可能存在的旧定时器
      if (this.countdown.timer) {
        clearInterval(this.countdown.timer);
      }
      
      this.countdown.timer = setInterval(() => {
        if (this.countdown.time > 0) {
          this.countdown.time--;
        } else {
          this.timeUp();
        }
      }, 1000);
    },
    
    // 时间到处理
    timeUp() {
      clearInterval(this.countdown.timer);
      this.countdown.isActive = false;
      this.showAnswer = true;
      
      // 如果还没答对，显示正确答案
      if (!this.gameResult.isCorrect) {
        this.gameResult.correctAnswer = this.gameSession.currentQuestion.answer;
      }
    },
    
    // 清理倒计时
    clearCountdown() {
      if (this.countdown.timer) {
        clearInterval(this.countdown.timer);
        this.countdown.timer = null;
      }
      this.countdown.isActive = false;
      this.showAnswer = false;
    }
  },
  watch: {
    currentPage(newPage, oldPage) {
      console.log('页面从', oldPage, '变为', newPage);
      // 确保新页面数据加载
      this.loadQuestionsForPage(newPage);
    }
  },
  beforeUnmount() {
    if (this.countdown.timer) {
      clearInterval(this.countdown.timer);
      this.countdown.timer = null;
    }
    this.countdown.isActive = false;
    this.showAnswer = false;
  }
}
</script>

<style scoped>
.body {
  font-family: "宋体", sans-serif;
  background-color: #f8f4e9;
  margin: 0;
  padding: 0;
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  align-items: center;
  background-image: url('../assets/image/he.gif');
  background-size: cover;
  background-position: center;
  color: #333;
  background-repeat: repeat;
}

.rules-container {
  min-height: 90vh;
  display: flex;
  align-items: flex-start;
  justify-content: center;
  width: 100%;
  padding-top: 40px;
}

.background-container {
  background: linear-gradient(135deg, rgba(238, 226, 203, 0.95) 0%, rgba(245, 236, 220, 0.93) 100%);
  background-image: 
    linear-gradient(135deg, rgba(238, 226, 203, 0.95) 0%, rgba(245, 236, 220, 0.93) 100%),
    url("data:image/svg+xml,%3Csvg width='20' height='20' viewBox='0 0 20 20' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='%23614124' fill-opacity='0.08' fill-rule='evenodd'%3E%3Ccircle cx='3' cy='3' r='3'/%3E%3Ccircle cx='13' cy='13' r='3'/%3E%3C/g%3E%3C/svg%3E");
  padding: 40px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  box-sizing: border-box;
  width: 60vw;
  min-height: 60vh;
  position: relative;
  border-radius: 20px;
  box-shadow: 0 4px 25px rgba(139, 69, 19, 0.12);
  border: 2px solid rgba(139, 69, 19, 0.25);
  margin: 0 auto;
}

.background-container p {
  margin: 15px auto;
  font-family: "楷体", "STKaiti", serif;
  font-size: 1.2em;
  color: #614124;
  text-shadow: 1px 1px 2px rgba(255, 255, 255, 0.5);
  text-align: center;
}

.title {
  font-size: 2em !important;
  margin-bottom: 15px !important;
  font-weight: bold;
}

.subtitle {
  font-size: 1.2em !important;
  margin-top: 20px !important;
}

.game-rule-text {
  width: 80%;
  margin: 20px auto;
  text-align: left;
  white-space: normal;
  word-wrap: break-word;
  word-break: break-all;
  font-family: "楷体", "STKaiti", serif;
  font-size: 1.1em;
  line-height: 1.8;
  color: #614124;
  text-shadow: 1px 1px 2px rgba(255, 255, 255, 0.3);
  background: linear-gradient(135deg, rgba(238, 226, 203, 0.8) 0%, rgba(245, 236, 220, 0.85) 100%);
  padding: 20px 30px;
  border-radius: 12px;
  box-shadow: 0 2px 10px rgba(139, 69, 19, 0.1);
  border: 1px solid rgba(139, 69, 19, 0.2);
}

.game-content {
  padding: 20px;
  min-height: 100vh;
  width: 100%;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.game-card-container {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 20px;
  width: 90%;
  margin: 2vh auto;
  padding: 15px;
}

.game-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  width: 100%;
  box-sizing: border-box;
  background-color: transparent;
  border-radius: 10px;
  padding: 15px;
  box-shadow: none;
  transition: transform 0.3s ease;
  position: relative;
}

.level {
  font-family: "楷体", "STKaiti", serif;
  font-size: 1.2em;
  color: #614124;
  text-shadow: 1px 1px 2px rgba(255, 255, 255, 0.5);
  background: linear-gradient(135deg, rgba(248, 244, 233, 0.85) 0%, rgba(248, 244, 233, 0.95) 100%);
  padding: 8px 20px;
  border-radius: 15px;
  margin-bottom: 15px;
  position: relative;
  backdrop-filter: blur(3px);
  border: 1px solid rgba(139, 69, 19, 0.1);
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
  width: fit-content;
  margin: 0 auto 15px;
}

.page {
  margin: 2vh auto;
  width: 100%;
  display: flex;
  justify-content: center;
  align-items: center;
}

.error-message {
  background-color: #f8d7da;
  color: #721c24;
  padding: 10px 15px;
  border-radius: 5px;
  margin: 10px auto;
  max-width: 80%;
  text-align: center;
  display: flex;
  justify-content: center;
  align-items: center;
  width: fit-content;
}

.success-message, .error-feedback {
  margin: 10px auto;
  padding: 10px;
  width: 85%;
  background: linear-gradient(135deg, rgba(248, 244, 233, 0.95) 0%, rgba(248, 244, 233, 0.98) 100%);
  border-radius: 8px;
  color: #8B4513;
  text-align: center;
  font-weight: bold;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.05);
  animation: fadeIn 0.5s;
  border: 1px solid rgba(139, 69, 19, 0.2);
}

.correct-answer-text {
  margin-top: 10px;
  font-size: 18px;
  color: #8B4513;
  font-family: "楷体", "STKaiti", serif;
  text-align: center;
  width: 100%;
}

.user-answer {
  margin-top: 8px;
  font-size: 16px;
  color: #8B4513;
  font-family: "楷体", "STKaiti", serif;
  text-align: center;
  width: 100%;
}

.fade-enter-active, .fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from, .fade-leave-to {
  opacity: 0;
}

.start-game-btn {
  margin: 30px auto 0;
  padding: 12px 40px;
  font-size: 1.2em;
  font-family: "楷体", "STKaiti", serif;
  color: #614124;
  background: linear-gradient(135deg, rgba(248, 244, 233, 0.95) 0%, rgba(248, 244, 233, 0.98) 100%);
  border: 1px solid rgba(139, 69, 19, 0.2);
  border-radius: 20px;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
}

.back-to-rules-btn {
  position: fixed;
  bottom: 20px;
  right: 20px;
  padding: 8px 20px;
  font-family: "楷体", "STKaiti", serif;
  color: #614124;
  background: linear-gradient(135deg, rgba(248, 244, 233, 0.95) 0%, rgba(248, 244, 233, 0.98) 100%);
  border: 1px solid rgba(139, 69, 19, 0.2);
  border-radius: 15px;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
  z-index: 100;
}

.mode-selection {
    margin: 20px auto;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 15px;
    font-family: "楷体", "STKaiti", serif;
    font-size: 1.2em;
}

.mode-selection span {
    transition: all 0.3s ease;
    color: #8B4513;
    opacity: 0.6;
    position: relative;
    cursor: pointer;
    text-shadow: 1px 1px 2px rgba(255, 255, 255, 0.5);
}

.mode-selection span.active {
    color: #8B4513;
    opacity: 1;
    font-weight: bold;
}

.mode-selection span.active::after {
    content: '';
    position: absolute;
    bottom: -3px;
    left: 0;
    width: 100%;
    height: 2px;
    background: linear-gradient(90deg, transparent, #8B4513, transparent);
    animation: fadeIn 0.3s ease;
}

.modeSelect {
    width: 20px;
    height: 50px;
    background-image: url('../assets/image/modeButton.png');
    background-size: cover;
    background-repeat: no-repeat;
    cursor: pointer;
    border: none;
    transition: transform 0.6s;
    transform-style: preserve-3d;
    background-color: transparent;
    opacity: 0.8;
}

.modeSelect:hover {
    opacity: 1;
}

.modeSelect.active {
    transform: rotateY(180deg);
    transition: transform 0.6s;
    transform-style: preserve-3d;
}

.close-button {
  position: absolute;
  top: 10px;
  right: 10px;
  background: none;
  border: none;
  font-size: 24px;
  cursor: pointer;
  z-index: 10;
  color: #333;
  padding: 5px 10px;
  border-radius: 50%;
  transition: all 0.3s ease;
}

.overlay {
  position: fixed;
  /* 设置为 fixed 定位，使蒙版固定在页面上 */
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  /* 半透明黑色背景，遮挡周围区域 */
  display: flex;
  /* 使用 flexbox 来居中内容 */
  justify-content: center;
  /* 水平居中 */
  align-items: center;
  /* 垂直居中 */
  z-index: 1000;
  /* 确保蒙版显示在最上层 */
  flex-direction: column;
  background-size: cover;
  /* 确保背景图片填满容器 */
  width: 100%;
  height: 100%;
  box-sizing: border-box;
}

.overlay-content {
  width: 500px;
  height: 500px;
  padding: 20px;
  box-sizing: border-box;
  background: linear-gradient(135deg, rgba(238, 226, 203, 0.97) 0%, rgba(245, 236, 220, 0.95) 100%);
  background-image: 
    linear-gradient(135deg, rgba(238, 226, 203, 0.97) 0%, rgba(245, 236, 220, 0.95) 100%),
    url("data:image/svg+xml,%3Csvg width='20' height='20' viewBox='0 0 20 20' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='%23614124' fill-opacity='0.08' fill-rule='evenodd'%3E%3Ccircle cx='3' cy='3' r='3'/%3E%3Ccircle cx='13' cy='13' r='3'/%3E%3C/g%3E%3C/svg%3E");
  border: 2px solid rgba(139, 69, 19, 0.25);
  border-radius: 15px;
  opacity: 1;
  position: relative;
  box-shadow: 0 4px 20px rgba(139, 69, 19, 0.15);
}

.boardOfNine {
    position: relative;
    width: 100%;
    height: 100%;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    padding: 20px;
    box-sizing: border-box;
}

.grid-item {
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    margin: 20px auto 10px;
    width: 85%;
}

.answer {
    margin: 10px auto;
    display: flex;
    justify-content: center;
    align-items: center;
    flex-wrap: wrap;
    gap: 5px;
    min-height: 40px;
    padding: 10px;
    background: linear-gradient(135deg, rgba(248, 244, 233, 0.4) 0%, rgba(248, 244, 233, 0.6) 100%);
    border: 1px solid rgba(139, 69, 19, 0.15);
    border-radius: 8px;
    width: 85%;
    backdrop-filter: blur(3px);
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.03);
}

.success-icon {
    font-size: 32px;
    margin-bottom: 10px;
    color: #8B4513;
}

.start-recording-btn {
    margin: 10px auto;
    display: block;
    background-color: #2196F3;
    color: white;
    padding: 10px 20px;
    font-size: 16px;
    border: none;
    border-radius: 5px;
    cursor: pointer;
    font-weight: bold;
    transition: background-color 0.3s;
}

.grid-row {
    display: flex;
    justify-content: center;
    width: 100%;
    margin-bottom: 5px;
}

.grid-button {
  width: 70px;
  height: 70px;
  font-size: 24px;
  font-weight: bold;
  cursor: pointer;
  background: linear-gradient(135deg, rgba(238, 226, 203, 0.95) 0%, rgba(245, 236, 220, 0.9) 100%);
  border: 2px solid rgba(139, 69, 19, 0.4);
  border-radius: 8px;
  margin: 0 5px;
  display: flex;
  justify-content: center;
  align-items: center;
  box-shadow: 0 2px 8px rgba(139, 69, 19, 0.15);
  transition: all 0.3s ease;
  color: #614124;
  text-shadow: 1px 1px 2px rgba(255, 255, 255, 0.3);
}

.grid-button:hover {
  background: linear-gradient(135deg, rgba(245, 236, 220, 0.98) 0%, rgba(238, 226, 203, 0.93) 100%);
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(139, 69, 19, 0.2);
  border-color: rgba(139, 69, 19, 0.6);
}

.answer-button {
  width: 40px;
  height: 40px;
  font-size: 16px;
  cursor: pointer;
  background: linear-gradient(135deg, rgba(248, 244, 233, 0.8) 0%, rgba(248, 244, 233, 0.9) 100%);
  border: 2px solid rgba(139, 69, 19, 0.3);
  display: flex;
  justify-content: center;
  align-items: center;
  margin: 0 2px;
  border-radius: 4px;
  transition: all 0.3s ease;
  color: #614124;
  text-shadow: 1px 1px 2px rgba(255, 255, 255, 0.5);
}

.answer-button:hover {
  transform: translateY(-2px);
  box-shadow: 0 2px 8px rgba(139, 69, 19, 0.1);
  border-color: rgba(139, 69, 19, 0.5);
}

/* 覆盖分页的按钮背景色 */
.el-pagination .el-pager li {
  background-image: linear-gradient(to top, #fddb92 0%, #d1fdff 100%);
  border-radius: 5px;
  /* 设置圆角 */
}

.el-pagination .el-icon-arrow-left,
.el-pagination .el-icon-arrow-right {
  font-size: 20px;
  /* 改变箭头图标的大小 */
  background-image: linear-gradient(to top, #fddb92 0%, #d1fdff 100%);
}

.game-info {
  display: flex;
  justify-content: space-between;
  margin-bottom: 10px;
  padding: 5px 10px;
  background-color: rgba(255, 255, 255, 0.7);
  border-radius: 5px;
  font-weight: bold;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

.countdown-display {
  position: absolute;
  top: 15px;
  left: 15px;
  background: linear-gradient(135deg, rgba(238, 226, 203, 0.95) 0%, rgba(245, 236, 220, 0.9) 100%);
  padding: 8px 15px;
  border-radius: 8px;
  font-family: "楷体", "STKaiti", serif;
  color: #614124;
  font-size: 1.1em;
  border: 1px solid rgba(139, 69, 19, 0.3);
  box-shadow: 0 2px 8px rgba(139, 69, 19, 0.1);
}

.timeout-message {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  background: linear-gradient(135deg, rgba(238, 226, 203, 0.98) 0%, rgba(245, 236, 220, 0.95) 100%);
  padding: 20px 30px;
  border-radius: 12px;
  text-align: center;
  border: 2px solid rgba(139, 69, 19, 0.3);
  box-shadow: 0 4px 15px rgba(139, 69, 19, 0.15);
  z-index: 1000;
}

.timeout-message div {
  margin: 10px 0;
  color: #614124;
  font-family: "楷体", "STKaiti", serif;
  font-size: 1.2em;
}
</style>