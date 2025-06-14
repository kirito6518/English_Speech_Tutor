<template>
    <div class="body">
        <NavbarPage />

        <!-- 错误提示 -->
        <div v-if="showError" class="error-message">{{ errorMessage }}</div>

        <!-- Game Area -->
        <div class="poem-card-container">
            <!-- 使用 v-for 遍历当前页的诗词 -->
            <div v-for="(poem, index) in displayedPoems" :key="index" class="poem-card">
                <img :src="require(`@/assets/image/recite${index + 1 + (currentPage - 1) * 8}.jpg`)" style="border-radius: 20px;" width="200vw"
                    class="shadow-image" @click="showOverlay(index + (currentPage - 1) * 8)">
                <!-- 星星图标，基于评分动态渲染 -->
                <div class="stars">
                    <el-icon v-for="starIndex in 5" :key="starIndex">
                        <StarFilled :style="getPoemScore(index + (currentPage - 1) * 8) >= starIndex ? { color: 'gold' } : { color: 'white' }" />
                    </el-icon>
                </div>
            </div>
        </div>
        <div class="page-poem">
            <el-pagination background layout="prev, pager, next" :total="totalPoems" class="mt-4" :page-size="8"
                :current-page="currentPage" @current-change="handlePageChange"></el-pagination>
        </div>

        <!-- Overlay -->
        <div v-if="isOverlayVisible" class="overlay" @click.self="hideOverlay">
            <div class="overlay-poem">
                <!-- Poem -->
                <div class="content-of-poem-overlay">
                    <button class="close-button" @click="hideOverlay">&times;</button>

                    <!-- Display poem -->
                    <div v-if="currentPoem" class="poem-container">
                        <div class="poem-content">
                            <div class="title">
                                {{ currentPoem.title }}
                            </div>
                            <div class="author">
                                {{ currentPoem.author }}
                            </div>
                            <div v-for="(line, lineIndex) in currentPoem.content" :key="lineIndex" class="content">
                                <div>{{ line }}</div>
                            </div>
                        </div>
                        <div v-if="isRecitingMode" class="poem-mask"></div>
                        <div class="countdown-display" v-if="countdown.isActive">
                            剩余时间：{{ Math.floor(countdown.time / 60) }}分{{ countdown.time % 60 }}秒
                        </div>
                        <div v-if="showTimeoutMessage" class="timeout-message">
                            <div>时间到！</div>
                        </div>
                    </div>
                </div>
                
                <!-- 背诵区 -->
                <div v-if="isRecitingMode" class="recitation-area">
                    <div v-if="recitationResult" class="recitation-result">
                        <div :class="['result-status', recitationResult.score >= 4 ? 'success' : 'warning']">
                            <div class="result-icon">{{ recitationResult.score >= 4 ? '✓' : '!' }}</div>
                            <h3>{{ recitationResult.feedback }}</h3>
                            <div class="accuracy">准确率: {{ recitationResult.accuracy }}%</div>
                            <div class="score-display">得分: {{ recitationResult.score }}/5</div>
                            <div class="recognized-text">识别文本: {{ recitationResult.recitation_text }}</div>
                            <div class="correct-text">正确文本: {{ recitationResult.correct_text }}</div>
                        </div>
                        <button class="btn-grad" @click="closeRecitation">返回</button>
                    </div>
                    <div v-else>
                        <div v-if="isRecording" class="recording-status">
                            <div class="pulse-icon"></div>
                            <p>正在录音... {{ recordingTimeLeft }}秒后自动停止</p>
                        </div>
                        <div v-else class="recitation-prompt">
                            <p>请朗读整首诗词，包括标题和作者</p>
                            <div class="recitation-buttons">
                                <button class="btn-grad" @click="startVoiceRecitation">开始语音背诵</button>
                                <button class="btn-grad" @click="showTextInput = !showTextInput">
                                    {{ showTextInput ? '取消文本输入' : '文本输入' }}
                                </button>
                            </div>
                            <div v-if="showTextInput" class="text-input-area">
                                <textarea 
                                    v-model="textRecitation" 
                                    placeholder="请输入背诵内容..." 
                                    rows="5" 
                                    class="recitation-textarea"
                                ></textarea>
                                <button class="btn-grad submit-text" @click="submitTextRecitation">提交</button>
                            </div>
                        </div>
                    </div>
                </div>
                <div v-else class="recite-button-container">
                    <button class="btn-grad" @click="beginRecite">开始背诵</button>
                </div>
            </div>
        </div>

    </div>

</template>

<script>
import NavbarPage from './NavbarPage.vue';
import { ElIcon } from 'element-plus';
import { StarFilled } from '@element-plus/icons-vue';  // 引入 Star 图标
import axios from 'axios';

export default {
    name: 'RecitePage',
    data() {
        return {
            // 会话数据
            sessionId: null,
            allPoems: [], // 从后端获取的所有诗词
            
            // 页面状态
            currentPage: 1,
            totalPoems: 50,
            poemsPerPage: 8,
            isOverlayVisible: false,
            currentPoemIndex: null,
            isRecitingMode: false,
            isRecording: false,
            recordingTimeLeft: 0,
            recordingTimer: null,
            recitationResult: null,
            textRecitation: '',
            showTextInput: false,

            // 错误处理
            showError: false,
            errorMessage: '',

            // 倒计时相关数据
            countdown: {
                time: 60,
                timer: null,
                isActive: false
            },
            showTimeoutMessage: false,
        }
    },
    components: {
        NavbarPage,
        ElIcon,
        StarFilled
    },
    computed: {
        // 当前页显示的诗词
        displayedPoems() {
            if (!this.allPoems || this.allPoems.length === 0) {
                console.log('displayedPoems: 诗词数据尚未加载');
                return Array(this.poemsPerPage).fill({
                    title: '加载中...',
                    author: '',
                    content: [''],
                    is_completed: false,
                    score: 0
                });
            }
            
            const start = (this.currentPage - 1) * this.poemsPerPage;
            const end = Math.min(start + this.poemsPerPage, this.allPoems.length);
            console.log(`displayedPoems: 显示诗词范围 ${start} - ${end}, 总长度: ${this.allPoems.length}`);
            return this.allPoems.slice(start, end);
        },
        // 当前选中的诗词
        currentPoem() {
            if (this.currentPoemIndex === null || !this.allPoems || this.allPoems.length === 0) {
                return {
                    title: '加载中...',
                    author: '',
                    content: [''],
                    is_completed: false,
                    score: 0
                };
            }
            
            if (this.currentPoemIndex >= this.allPoems.length) {
                console.error('访问了不存在的诗词索引:', this.currentPoemIndex);
                return {
                    title: '数据错误',
                    author: '',
                    content: ['无法加载该诗词'],
                    is_completed: false,
                    score: 0
                };
            }
            
            return this.allPoems[this.currentPoemIndex] || {
                title: '加载中...',
                author: '',
                content: [''],
                is_completed: false,
                score: 0
            };
        }
    },
    mounted() {
        // 初始化时创建背诵会话
        this.createRecitationSession();
    },
    methods: {
        // 创建背诵会话
        async createRecitationSession() {
            try {
                console.log('开始创建背诵会话...');
                // 初始化诗词数组，即使API未返回也有内容显示
                this.allPoems = Array(this.totalPoems).fill().map((_, index) => ({
                    title: `诗词 ${index + 1}`,
                    author: '加载中...',
                    content: ['点击加载详情'],
                    is_completed: false,
                    score: 0
                }));

                const response = await axios.post('/api/recitation/create');
                console.log('创建背诵会话响应:', response.data);
                
                this.sessionId = response.data.session_id;
                
                // 初始化诗词数据
                const firstPoem = response.data.poem;
                this.totalPoems = response.data.total_poems;
                
                // 固定的6首经典诗词
                const fixedPoems = [
                    { 
                        title: '江南', 
                        author: '《汉乐府》', 
                        content: ['江南可采莲，莲叶何田田。鱼戏莲叶间。', '鱼戏莲叶东，鱼戏莲叶西，鱼戏莲叶南，鱼戏莲叶北。'],
                        is_completed: false,
                        score: 0 
                    },
                    { 
                        title: '咏鹅', 
                        author: '（唐）骆宾王', 
                        content: ['鹅鹅鹅，曲项向天歌。', '白毛浮绿水，红掌拨清波。'],
                        is_completed: false,
                        score: 0 
                    },
                    { 
                        title: '画', 
                        author: '（唐）王维', 
                        content: ['远看山有色，近听水无声。', '春去花还在，人来鸟不惊。'],
                        is_completed: false,
                        score: 0 
                    },
                    { 
                        title: '悯农', 
                        author: '（唐）李绅', 
                        content: ['锄禾日当午，汗滴禾下土。', '谁知盘中餐，粒粒皆辛苦。'],
                        is_completed: false,
                        score: 0 
                    },
                    { 
                        title: '古朗月行', 
                        author: '（唐）李白', 
                        content: ['小时不识月，呼作白玉盘。', '又疑瑶台镜，飞在青云端。'],
                        is_completed: false,
                        score: 0 
                    },
                    { 
                        title: '风', 
                        author: '（唐）李峤', 
                        content: ['解落三秋叶，能开二月花。', '过江千尺浪，入竹万竿斜。'],
                        is_completed: false,
                        score: 0 
                    }
                ];
                
                // 创建新的诗词列表，前6首是固定诗词
                const newAllPoems = [...fixedPoems];
                
                // 从API获取的诗词数据
                const apiPoems = response.data.poems || [];
                
                // 如果后端返回了诗词列表，使用后端返回的诗词
                if (apiPoems.length > 0) {
                    // 将API返回的诗词添加到固定诗词之后
                    apiPoems.forEach(poem => {
                        newAllPoems.push({
                            poem_id: poem.poem_id,
                            title: poem.title,
                            author: poem.author,
                            poem_name: poem.poem_name,
                            content: poem.content,
                            is_completed: false,
                            score: 0
                        });
                    });
                } 
                // 如果只返回了第一首诗
                else if (firstPoem) {
                    newAllPoems.push({
                        poem_id: firstPoem.poem_id,
                        title: firstPoem.title,
                        author: firstPoem.author,
                        poem_name: firstPoem.poem_name,
                        content: firstPoem.content,
                        is_completed: false,
                        score: 0
                    });
                }
                
                // 如果诗词总数不足，添加占位诗词
                while (newAllPoems.length < this.totalPoems) {
                    newAllPoems.push({
                        title: `诗词 ${newAllPoems.length + 1}`,
                        author: '加载中...',
                        content: ['点击加载详情'],
                        is_completed: false,
                        score: 0
                    });
                }
                
                // 确保总数量正确
                if (newAllPoems.length > this.totalPoems) {
                    this.allPoems = newAllPoems.slice(0, this.totalPoems);
                } else {
                    this.allPoems = newAllPoems;
                }
                
                console.log(`背诵会话创建完成，诗词数量: ${this.allPoems.length}`);
            } catch (error) {
                console.error('创建背诵会话失败:', error);
                this.showErrorMessage('创建背诵会话失败，请稍后再试');
            }
        },
        
        // 显示诗词详情
        async showOverlay(index) {
            console.log('点击的索引:', index, '当前allPoems长度:', this.allPoems ? this.allPoems.length : 0);
            
            // 确保allPoems已经初始化
            if (!this.allPoems) {
                console.error('诗词数组未初始化');
                this.showErrorMessage('诗词数据正在加载中，请稍后再试');
                return;
            }

            // 检查索引是否有效
            if (index < 0 || index >= this.totalPoems) {
                console.error('无效的诗词索引:', index);
                this.showErrorMessage('无效的诗词索引');
                return;
            }

            // 确保allPoems数组有足够的元素
            if (this.allPoems.length <= index) {
                console.error('诗词数据未加载完全，当前长度:', this.allPoems.length, '请求索引:', index);
                this.showErrorMessage('诗词数据正在加载中，请稍后再试');
                return;
            }

            // 获取当前诗词，必须存在
            const poemData = this.allPoems[index];
            if (!poemData) {
                console.error('该索引处没有诗词数据:', index);
                this.showErrorMessage('找不到该诗词数据');
                return;
            }

            console.log('当前诗词数据:', poemData);
            
            // 设置当前状态
            this.currentPoemIndex = index;
            this.isOverlayVisible = true;
            this.isRecitingMode = false;
            this.recitationResult = null;
            
            // 如果还没有加载过这首诗的详细内容，则加载
            if (!poemData.content || (Array.isArray(poemData.content) && poemData.content.length === 1 && poemData.content[0] === '点击加载详情')) {
                try {
                    await this.loadPoemDetails(index);
                } catch (error) {
                    console.error('加载诗词详情失败:', error);
                    this.showErrorMessage('加载诗词详情失败，请稍后再试');
                    // 避免加载失败时闪退
                    this.hideOverlay();
                }
            }
        },
        
        // 加载诗词详情
        async loadPoemDetails(index) {
            try {
                // 发送空背诵请求以获取诗词详情
                const response = await axios.post('/api/recitation/submit_text', {
                    session_id: this.sessionId,
                    recitation_text: '',
                    poem_index: index
                });
                
                console.log('加载诗词详情响应:', response.data);
                
                // 更新当前诗词信息
                if (response.data.current_poem) {
                    this.allPoems[index] = {
                        poem_id: response.data.current_poem.poem_id,
                        title: response.data.current_poem.title,
                        author: response.data.current_poem.author,
                        poem_name: response.data.current_poem.poem_name,
                        content: response.data.current_poem.content,
                        is_completed: false,
                        score: 0
                    };
                }
                
                // 更新所有诗词的状态
                if (response.data.all_poems) {
                    response.data.all_poems.forEach((poem, i) => {
                        if (this.allPoems[i]) {
                            this.allPoems[i].is_completed = poem.is_completed;
                            this.allPoems[i].score = poem.score;
                        }
                    });
                }
            } catch (error) {
                console.error('加载诗词详情失败:', error);
                this.showErrorMessage('加载诗词详情失败，请稍后再试');
            }
        },
        
        // 关闭诗词详情
        hideOverlay() {
            this.isOverlayVisible = false;
            this.isRecitingMode = false;
            this.recitationResult = null;
        },
        
        // 获取诗词评分
        getPoemScore(index) {
            if (!this.allPoems || index < 0 || index >= this.allPoems.length) {
                return 0;
            }
            return this.allPoems[index] && this.allPoems[index].score ? this.allPoems[index].score : 0;
        },
        
        // 切换页面
        handlePageChange(newPage) {
            this.currentPage = newPage;
        },
        
        // 开始背诵模式
        beginRecite() {
            this.isRecitingMode = true;
            this.recitationResult = null;
            this.showTextInput = false;
            this.textRecitation = '';
        },
        
        // 关闭背诵结果
        closeRecitation() {
            this.isRecitingMode = false;
            this.recitationResult = null;
        },
        
        // 开始语音背诵
        startVoiceRecitation() {
            this.isRecording = true;
            this.recordingTimeLeft = 15; // 15秒录音
            
            // 请求后端开始录音
            axios.post('/api/recitation/record', {
                session_id: this.sessionId,
                poem_index: this.currentPoemIndex,
                duration: 15
            })
            .then(response => {
                console.log('语音背诵响应:', response.data);
                this.handleRecitationResult(response.data);
            })
            .catch(error => {
                console.error('语音背诵失败:', error);
                this.showErrorMessage('语音背诵失败，请稍后再试');
                this.isRecording = false;
            });
            
            // 倒计时显示
            this.recordingTimer = setInterval(() => {
                this.recordingTimeLeft--;
                if (this.recordingTimeLeft <= 0) {
                    clearInterval(this.recordingTimer);
                    this.isRecording = false;
                }
            }, 1000);
        },
        
        // 提交文本背诵
        async submitTextRecitation() {
            if (!this.textRecitation.trim()) {
                this.showErrorMessage('请输入背诵内容');
                return;
            }
            
            try {
                const response = await axios.post('/api/recitation/submit_text', {
                    session_id: this.sessionId,
                    recitation_text: this.textRecitation,
                    poem_index: this.currentPoemIndex
                });
                
                console.log('文本背诵响应:', response.data);
                this.handleRecitationResult(response.data);
            } catch (error) {
                console.error('文本背诵提交失败:', error);
                this.showErrorMessage('文本背诵提交失败，请稍后再试');
            }
        },
        
        // 处理背诵结果
        handleRecitationResult(result) {
            this.isRecording = false;
            if (this.recordingTimer) {
                clearInterval(this.recordingTimer);
            }
            
            if (result.error) {
                this.showErrorMessage(result.error);
                return;
            }

            // 构建完整的正确文本（标题 + 作者 + 内容）
            const fullCorrectText = `${this.currentPoem.title}${this.currentPoem.author}${this.currentPoem.content.join('')}`;
            
            // 去除所有标点符号并计算差异
            const cleanInput = result.recitation_text.replace(/[，。？！；：""''【】()（）《》、，。、。\s]/g, '');
            const cleanCorrect = fullCorrectText.replace(/[，。？！；：""''【】()（）《》、，。、。\s]/g, '');
            
            // 计算编辑距离
            const diffCount = this.calculateDifference(cleanInput, cleanCorrect);
            
            // 根据差异字数评分
            let score;
            if (diffCount === 0) {
                score = 5;  // 完全正确
            } else if (diffCount <= 3) {
                score = 4;  // 错1-3个字
            } else if (diffCount <= 5) {
                score = 3;  // 错3-5个字
            } else if (diffCount <= 8) {
                score = 2;  // 错5-8个字
            } else if (diffCount <= 10) {
                score = 1;  // 错8-10个字
            } else {
                score = 0;  // 错误超过10个字
            }
            
            // 更新结果对象，保存完整的正确文本以供显示
            this.recitationResult = {
                ...result,
                score: score,
                accuracy: Math.max(0, Math.round((1 - diffCount / cleanCorrect.length) * 100)),
                feedback: this.getFeedback(score),
                recitation_text: result.recitation_text,
                correct_text: fullCorrectText  // 使用完整的正确文本
            };
            
            this.showMask = false;  // 提交答案后取消遮罩
            this.clearCountdown();  // 清除倒计时
            
            // 更新当前诗词的完成状态和评分
            if (this.currentPoemIndex !== null && this.allPoems[this.currentPoemIndex]) {
                this.allPoems[this.currentPoemIndex].is_completed = true;
                this.allPoems[this.currentPoemIndex].score = score;
            }
        },
        
        // 计算两个字符串的差异字数
        calculateDifference(str1, str2) {
            const len1 = str1.length;
            const len2 = str2.length;
            const dp = Array(len1 + 1).fill(null).map(() => Array(len2 + 1).fill(0));

            // 初始化第一行和第一列
            for (let i = 0; i <= len1; i++) dp[i][0] = i;
            for (let j = 0; j <= len2; j++) dp[0][j] = j;

            // 填充dp数组
            for (let i = 1; i <= len1; i++) {
                for (let j = 1; j <= len2; j++) {
                    if (str1[i - 1] === str2[j - 1]) {
                        dp[i][j] = dp[i - 1][j - 1];
                    } else {
                        dp[i][j] = Math.min(
                            dp[i - 1][j] + 1,    // 删除
                            dp[i][j - 1] + 1,    // 插入
                            dp[i - 1][j - 1] + 1 // 替换
                        );
                    }
                }
            }

            return dp[len1][len2];
        },
        
        // 根据分数获取反馈信息
        getFeedback(score) {
            switch (score) {
                case 5:
                    return "太棒了！完全正确！";
                case 4:
                    return "非常好！只有少许错误";
                case 3:
                    return "不错！继续努力";
                case 2:
                    return "还需要多加练习";
                case 1:
                    return "要加油哦";
                default:
                    return "需要更多练习";
            }
        },
        
        // 显示错误信息
        showErrorMessage(message) {
            this.errorMessage = message;
            this.showError = true;
            setTimeout(() => {
                this.showError = false;
            }, 3000);
        },

        // 开始倒计时
        startCountdown() {
            this.countdown.time = 60;
            this.countdown.isActive = true;
            this.showTimeoutMessage = false;
            
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
            this.showTimeoutMessage = true;
            this.showMask = false;  // 时间到时显示内容
        },
        
        // 清理倒计时
        clearCountdown() {
            if (this.countdown.timer) {
                clearInterval(this.countdown.timer);
                this.countdown.timer = null;
            }
            this.countdown.isActive = false;
            this.showTimeoutMessage = false;
        },
        
        // 修改 toggleMask 方法
        toggleMask() {
            this.showMask = !this.showMask;
            if (this.showMask) {
                this.startCountdown();  // 遮罩开启时开始倒计时
            } else {
                this.clearCountdown();  // 遮罩关闭时清除倒计时
            }
        },
    },
    beforeUnmount() {
        this.clearCountdown();
    }
}
</script>

<style scoped>
.body {
    font-family: "宋体", sans-serif;
    background-color: #f8f4e9;
    /* 页面背景颜色 */
    margin: 0;
    padding: 0;
    display: flex;
    flex-direction: column;
    align-items: center;
    /* 透视 */
    background-image: url('../assets/image/he.gif');
    background-size: cover;
    background-position: center;
    color: #333;
    background-repeat: repeat;
    min-height: 100vh;
    width: 100%;
}

.poem-card-container {
    flex-direction: column;
    align-items: center;
    justify-content: center;
    justify-content: center;
    text-align: center;
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 15px;
    width: 80%;
    margin-top: 5vh;
}

.poem-card {
    display: flex;
    flex-direction: column;
    align-items: center;
    /* 水平居中卡片内容 */
    justify-content: center;
    /* 垂直居中卡片内容 */
    text-align: center;
    width: 100%;
    /* 卡片占满容器宽度 */
    height: auto;
    box-sizing: border-box;
    margin-bottom: 20%;
    margin-top: 10%;
}

.shadow-image {
    border-radius: 20px;
    box-shadow: 4px 4px 8px rgba(0, 0, 0, 0.5);
    transition: box-shadow 0.3s ease, transform 0.3s ease;
    cursor: pointer;
}

.shadow-image:hover {
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
    transform: translateY(4px);
}

.stars {
    margin-top: 10px;
    display: flex;
    justify-content: center;
    gap: 5px;
}

.stars i {
    font-size: 2em;
}

.fas.fa-star {
    color: gold;
    /* 黄色 */
}

.far.fa-star {
    color: grey;
    /* 灰色 */
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

.overlay-poem {
    width: 500px;
    /* 设置固定的宽度 */
    min-height: 550px;
    /* 设置最小高度 */
    padding: 20px;
    box-sizing: border-box;
    background-image: url('../assets/image/background.jpg');
    /* 可选的背景图像 */
    border-radius: 10px;
    /* 可选，设置圆角 */
    opacity: 1;
    /* 保证内容区域不透明 */
    display: flex;
    flex-direction: column;
}

.title {
    font-size: 2em;
    font-family: "Arial", sans-serif;
    font-weight: bold;
    text-align: center;
    margin-bottom: 10px;
    color: #333;
}

/* Author Style */
.author {
    font-size: 1.5em;
    font-family: "Georgia", serif;
    font-style: italic;
    text-align: center;
    margin-bottom: 20px;
    color: #555;
}

/* Content Style */
.content {
    font-size: 1.2em;
    font-family: "Times New Roman", serif;
    text-align: center;
    margin-bottom: 10px;
    white-space: pre-line;
    /* Ensures the sentence is displayed in multiple lines */
    line-height: 1.5;
    color: #333;
}

.content-of-poem-overlay {
    min-height: 250px;
    max-height: 300px;
    overflow-y: auto;
    position: relative;
    margin-bottom: 20px;
}

.btn-grad {
    background-image: linear-gradient(to right, #649173 0%, #DBD5A4 51%, #649173 100%);
    margin: 5px;
    padding: 10px 25px;
    text-align: center;
    text-transform: uppercase;
    transition: 0.5s;
    background-size: 200% auto;
    color: white;
    box-shadow: 0 0 20px #eee;
    border-radius: 10px;
    display: inline-block;
    border: none;
    cursor: pointer;
}

.btn-grad:hover {
    background-position: right center;
    /* change the direction of the change here */
    color: #fff;
    text-decoration: none;
}

.recite-button-container {
    display: flex;
    justify-content: center;
    gap: 20px;
    margin-top: 20px;
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

.close-button:hover {
    background-color: rgba(0, 0, 0, 0.1);
}

.error-message {
    background-color: #f8d7da;
    color: #721c24;
    padding: 10px 15px;
    border-radius: 5px;
    margin: 10px 0;
    position: fixed;
    top: 80px;
    left: 50%;
    transform: translateX(-50%);
    z-index: 1100;
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
}

/* 背诵相关样式 */
.recitation-area {
    flex: 1;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
}

.recitation-prompt {
    text-align: center;
    margin-bottom: 20px;
}

.recitation-buttons {
    display: flex;
    justify-content: center;
    gap: 10px;
    margin: 15px 0;
}

.recording-status {
    text-align: center;
    margin: 20px 0;
    font-size: 1.2em;
    color: #721c24;
    display: flex;
    flex-direction: column;
    align-items: center;
}

.pulse-icon {
    width: 20px;
    height: 20px;
    background-color: #dc3545;
    border-radius: 50%;
    margin-bottom: 10px;
    animation: pulse 1s infinite;
}

@keyframes pulse {
    0% {
        transform: scale(0.95);
        box-shadow: 0 0 0 0 rgba(220, 53, 69, 0.7);
    }
    
    70% {
        transform: scale(1);
        box-shadow: 0 0 0 10px rgba(220, 53, 69, 0);
    }
    
    100% {
        transform: scale(0.95);
        box-shadow: 0 0 0 0 rgba(220, 53, 69, 0);
    }
}

.text-input-area {
    margin-top: 15px;
    width: 100%;
}

.recitation-textarea {
    width: 100%;
    padding: 10px;
    border-radius: 5px;
    border: 1px solid #ccc;
    font-size: 1em;
    resize: vertical;
    margin-bottom: 10px;
}

.submit-text {
    margin-top: 10px;
}

.recitation-result {
    padding: 15px;
    width: 100%;
    text-align: center;
}

.result-status {
    border-radius: 8px;
    padding: 15px;
    margin-bottom: 20px;
    color: white;
}

.success {
    background-color: rgba(40, 167, 69, 0.8);
}

.warning {
    background-color: rgba(255, 152, 0, 0.8);
}

.result-icon {
    font-size: 2em;
    margin-bottom: 10px;
}

.accuracy, .score-display, .recognized-text, .correct-text {
    margin: 8px 0;
}

.recognized-text, .correct-text {
    font-size: 0.9em;
    text-align: left;
    background: rgba(255, 255, 255, 0.2);
    padding: 5px;
    border-radius: 5px;
    word-break: break-all;
}

.page-poem {
    margin: 20px 0 40px 0;
}

.content-masked {
    background-color: #f8f4e9;
    color: transparent;
    user-select: none;
    position: relative;
    transition: all 0.3s ease;
}

.content-masked:hover {
    background-color: #e8e4d9;
}

.poem-container {
    position: relative;
    width: 100%;
    min-height: 250px;
}

.poem-content {
    position: relative;
    z-index: 1;
}

.poem-mask {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: linear-gradient(135deg, rgba(248, 244, 233, 0.95) 0%, rgba(248, 244, 233, 0.98) 100%);
    backdrop-filter: blur(2px);
    border-radius: 8px;
    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.05);
    z-index: 2;
    transition: all 0.3s ease;
    pointer-events: none;
}

.poem-mask::before {
    content: '';
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    width: 80%;
    height: 2px;
    background: linear-gradient(90deg, transparent, rgba(100, 145, 115, 0.3), transparent);
}

.poem-mask::after {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background-image: url("data:image/svg+xml,%3Csvg width='100' height='100' viewBox='0 0 100 100' xmlns='http://www.w3.org/2000/svg'%3E%3Cpath d='M11 18c3.866 0 7-3.134 7-7s-3.134-7-7-7-7 3.134-7 7 3.134 7 7 7zm48 25c3.866 0 7-3.134 7-7s-3.134-7-7-7-7 3.134-7 7 3.134 7 7 7zm-43-7c1.657 0 3-1.343 3-3s-1.343-3-3-3-3 1.343-3 3 1.343 3 3 3zm63 31c1.657 0 3-1.343 3-3s-1.343-3-3-3-3 1.343-3 3 1.343 3 3 3zM34 90c1.657 0 3-1.343 3-3s-1.343-3-3-3-3 1.343-3 3 1.343 3 3 3zm56-76c1.657 0 3-1.343 3-3s-1.343-3-3-3-3 1.343-3 3 1.343 3 3 3zM12 86c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm28-65c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm23-11c2.76 0 5-2.24 5-5s-2.24-5-5-5-5 2.24-5 5 2.24 5 5 5zm-6 60c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm29 22c2.76 0 5-2.24 5-5s-2.24-5-5-5-5 2.24-5 5 2.24 5 5 5zM32 63c2.76 0 5-2.24 5-5s-2.24-5-5-5-5 2.24-5 5 2.24 5 5 5zm57-13c2.76 0 5-2.24 5-5s-2.24-5-5-5-5 2.24-5 5 2.24 5 5 5zm-9-21c1.105 0 2-.895 2-2s-.895-2-2-2-2 .895-2 2 .895 2 2 2zM60 91c1.105 0 2-.895 2-2s-.895-2-2-2-2 .895-2 2 .895 2 2 2zM35 41c1.105 0 2-.895 2-2s-.895-2-2-2-2 .895-2 2 .895 2 2 2zM12 60c1.105 0 2-.895 2-2s-.895-2-2-2-2 .895-2 2 .895 2 2 2z' fill='%23649173' fill-opacity='0.03' fill-rule='evenodd'/%3E%3C/svg%3E");
    opacity: 0.5;
}

.countdown-display {
    position: absolute;
    top: 15px;
    right: 15px;
    background: linear-gradient(135deg, rgba(238, 226, 203, 0.95) 0%, rgba(245, 236, 220, 0.9) 100%);
    padding: 8px 15px;
    border-radius: 8px;
    font-family: "楷体", "STKaiti", serif;
    color: #614124;
    font-size: 1.1em;
    border: 1px solid rgba(139, 69, 19, 0.3);
    box-shadow: 0 2px 8px rgba(139, 69, 19, 0.1);
    z-index: 1000;
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
    animation: fadeIn 0.5s ease;
}

.timeout-message div {
    margin: 10px 0;
    color: #614124;
    font-family: "楷体", "STKaiti", serif;
    font-size: 1.2em;
}

@keyframes fadeIn {
    from { opacity: 0; }
    to { opacity: 1; }
}
</style>