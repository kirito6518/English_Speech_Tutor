<template>
  <div class="body">
    <!-- Header Section -->
    <div class="header">
      <p>
        你好，<br />
        欢迎来到诗词中心！<br />
        <span class="highlight">我是你的好朋友，诗小语。</span>
      </p>
      <button class="logout-button" @click="confirmLogout">退出登录</button>
    </div>

    <!-- Card Container -->
    <div class="card-container">
      <div class="card card1">
        <button class="myButton" @click="XuexiMode">
          <div class="card-content">研学探秘</div>
        </button>
      </div>

      <div class="card card2">
        <button class="myButton" @click="BeisongMode">
          <div class="card-content">成诵古韵</div>
        </button>
      </div>

      <div class="card card3">
        <button class="myButton" @click="ChuanguanMode">
          <div class="card-content">闯关夺宝</div>
        </button>
      </div>

      <div class="card card4">
        <button class="myButton" @click="FeihuaMode">
          <div class="card-content">飞花传令</div>
        </button>
      </div>
    </div>

    <!-- Below Section -->
    <div class="below">
      <p class="random-content">{{ randomContent }}</p>
    </div>
  </div>
</template>

<script>


export default {
  name: 'HomePage',
  data() {
    return {
      randomContent: ''
    }
  },
  mounted() {
    this.loadRandomContent();
  },
  methods: {
    XuexiMode() {
      // 跳转到 LearnMode 页面
      this.$router.push('/learn');
      // 你可以在这里设置内容，也可以根据需要跳转
      this.randomContent = '你选择了研学探秘模式';
    },
    BeisongMode() {
      // 跳转到 LearnMode 页面
      this.$router.push('/recite');
      // 你可以在这里设置内容，也可以根据需要跳转
      this.randomContent = '你选择了研学探秘模式';
    },
    ChuanguanMode() {
      this.$router.push('/game');
      this.randomContent = '你选择了闯关夺宝模式';
    },
    FeihuaMode() {
      this.$router.push('/feihua');
      this.randomContent = '你选择了飞花传令模式';
    },
    async loadRandomContent() {
      try {
        const response = await fetch('/word/daily.txt');
        const data = await response.text();
        
        // Split the content by newline to get each line
        const contentLines = data.split('\n');
        
        // Pick a random line from the content
        const randomIndex = Math.floor(Math.random() * contentLines.length);
        this.randomContent = contentLines[randomIndex].trim();  // Assign random content
        console.log(this.randomContent)
      } catch (error) {
        console.error("Error fetching random content:", error);
      }
    },
    confirmLogout() {
      if (confirm('你确定要退出登录吗？')) {
        // 清除用户状态（如果有的话）
        this.$router.push('/login');
      }
    }
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
      height: 100vh;      
      perspective: 1000px;
      /* 透视 */
      background-image:  url('../assets/image/zhubeijing.gif');
      background-size: cover;
      background-position: center;
      color: #333;
  }

.header {
  text-align: center;
  padding: 20px;
}

.highlight {
  color: #ff6347; /* 修改高亮颜色 */
}

.card-container {
  display: flex;
  justify-content: space-around;
  width: 80%;
  margin-top: 20px;
}
.logout-button {
  padding: 10px 20px;
  background-color: #B8860B; /* 古风按钮颜色 */
  color: white;
  border: none;
  border-radius: 5px;
  cursor: pointer;
  margin-top: 20px;
}

.logout-button:hover {
  background-color: #D4AF37; /* 悬停效果 */
}


.card {
  flex-basis: 23%;
    /* 卡牌的基本宽度 */
    height: 200px;
    /* 卡牌的高度 */
    width: 100px;
  
    /*background: url('/static/image/ju.jpg') ;
    background-size: cover;
    /* 卡牌的背景颜色 */
    border-radius: 15px;
    /* 边框圆角 */
    cursor: pointer;
    /* 鼠标样式 */
    transition: all 0.3s ease;
    /* 过渡动画 */
  
    transition: all 0.3s ease;
    border: 1px solid #ddd; /* 更柔和的边框颜色 */
    box-shadow: 0px 4px 8px rgba(0, 0, 0, 0.1);
}

.card1 {  background: url('../assets/image/lan.jpg') ; 
    background-size: cover;}
  .card2 {  background: url('../assets/image/mei.jpg') ; 
    background-size: cover; }
  .card3 { background: url('../assets/image/ju.jpg') ; 
    background-size: cover; }
  .card4 {  background: url('../assets/image/zhu.jpg') ; 
    background-size: cover; }
  
    .card-content {
        display: flex;
        justify-content: center;  
        align-items: center;      
        height: 100%;            
        text-align: center;      
        font-weight: 900;
        font-family: 'Noto Sans SC', sans-serif; 
        color: #333; 
    }

    .card:hover {
    transform: scale(1.05);
    /* 鼠标悬停放大效果 */
    background-color: #d2b48c;
    /* 深黄色背景 */
    box-shadow: 0 0 15px rgba(0, 0, 0, 0.3);
}


.myButton {
  
  background-color: transparent;
  /* 调整字体样式和大小 */
  font-family: 'Noto Sans SC', serif; /* 使用古风字体 */
  font-size: 20px; 

 height:100px;
 width:100px;

  border: none; /* 移除边框 */

  color: #333; /* 深灰色文字 */

  padding: 10px; 
  margin: 50px;
}


.below {
    z-index: 10;
    /* 确保标题在顶层显示 */
    position: relative;
    /* 定位相关性 */
    background-color: rgba(255, 255, 255, 0.3);
    /* 半透明白色背景 */
    padding: 20px;
    margin-top: 20px;
    /* 顶部间距 */
    border-radius: 10px;
    box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
    width: 200;
    /* 控制标题宽度 */
    text-align: center;
  }

  .random-content{
    font-size: 90%; 
  }

</style>
