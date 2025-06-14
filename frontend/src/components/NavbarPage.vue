<template>
  <div class="navbar">
    <button class="home" @click="gobackHome"></button>
    <div class="navbar-item" id="nav-xuexi" @click="XuexiMode">研学探秘</div>
    <div class="navbar-item" id="nav-beisong" @click="BeisongMode">成诵古韵</div>
    <div class="navbar-item" id="nav-chuangguan" @click="ChuanguanMode">闯关夺宝</div>
    <div class="navbar-item" id="nav-feihualing" @click="FeihuaMode">飞花传令</div>
  </div>
</template>

<script>
export default {
  name: 'NavbarPage',
  methods: {
    // 返回主页的功能
    gobackHome() {
      console.log('返回首页');
      this.$router.push('/');  // 使用 Vue Router 进行页面跳转
    },
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
    }
  }
};
</script>

<style scoped>
.navbar {
    display: flex;
    justify-content: center;
    margin-top: 40px;
    background: linear-gradient(to bottom, rgba(255, 255, 255, 0.8), rgba(255, 255, 255, 0)); 
    height: 60px; 
    width: 600px;
    position: relative;  
    border-radius: 15px;
}

.navbar-item {
    padding: 10px 20px;
    cursor: pointer;
    font-size: 20px;
    font-family: "宋体", sans-serif;
    transition: background-color 0.3s ease;

}

.navbar-item.selected {
    background-color: #ab3d1f;
    color: #fff;
    border-radius: 5px;
}

.navbar-item:hover {
    background-color: #ab3d1f;
    /* 选中模式的背景颜色 */
    color: #fff;
    /* 选中模式的文字颜色 */
    border-radius: 5px;
}

.home {
    width: 42px; 
    height: 58px;
    margin-right: 47px;
    background-image: url('../assets/image/home.png'); 
    background-size: cover; 
    background-repeat: no-repeat;
    background-position: center; 
    background-color: rgba(255, 255, 255, 0); /* 设置背景颜色透明 */
    border: none;
}

</style>