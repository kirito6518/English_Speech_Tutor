<template>
    <div class="login-body">
      <div class="login-container">
        <h2>{{ isRegister ? '注册' : '登录' }}</h2>
        <form @submit.prevent="isRegister ? handleRegister() : handleLogin()">
          <div class="form-group">
            <label for="username">用户名</label>
            <input type="text" v-model="username" id="username" required />
          </div>
          <div class="form-group">
            <label for="password">密码</label>
            <input type="password" v-model="password" id="password" required />
          </div>
          <div v-if="isRegister" class="form-group">
            <label for="confirmPassword">确认密码</label>
            <input type="password" v-model="confirmPassword" id="confirmPassword" required />
          </div>
          <button type="submit" class="login-button">{{ isRegister ? '注册' : '登录' }}</button>
        </form>
        <p class="error-message" v-if="errorMessage">{{ errorMessage }}</p>
        <button class="toggle-button" @click="toggleMode">
          {{ isRegister ? '已有账号？登录' : '没有账号？注册' }}
        </button>
      </div>
    </div>
  </template>
  
  <script>
  export default {
    data() {
      return {
        username: '',
        password: '',
        confirmPassword: '',
        errorMessage: '',
        isRegister: false
      };
    },
    methods: {
      async handleLogin() {
        // 硬编码的登录验证逻辑
        if (this.username === '123' && this.password === '123') {
          this.$router.push('/home'); // 登录成功后跳转到主页
        } else {
          this.errorMessage = '用户名或密码错误';
        }
      },
      async handleRegister() {
        if (this.password !== this.confirmPassword) {
          this.errorMessage = '密码和确认密码不匹配';
          return;
        }

        // 注册逻辑
        this.errorMessage = '注册成功！'; // 示例反馈
        // 这里可以添加实际的注册逻辑，例如发送请求到后端
      },
      toggleMode() {
        this.isRegister = !this.isRegister; // 切换登录和注册模式
        this.errorMessage = ''; // 清空错误信息
        this.username = '';
        this.password = '';
        this.confirmPassword = ''; // 清空确认密码
      }
    }
  };
  </script>
  
  <style scoped>
  .login-body {
    font-family: "Segoe UI", Tahoma, Geneva, Verdana, sans-serif;
    background: url('../assets/image/zhubeijing.gif') no-repeat center center fixed;
    background-size: cover;
    height: 100vh;
    display: flex;
    justify-content: center;
    align-items: center;
  }
  
  .login-container {
    background: rgba(255, 255, 255, 0.9);
    padding: 30px;
    border-radius: 10px;
    box-shadow: 0 6px 15px rgba(0, 0, 0, 0.15);
    width: 380px;
    max-width: 100%;
    text-align: center;
  }
  
  h2 {
    font-size: 24px;
    font-weight: 600;
    margin-bottom: 20px;
    color: #333;
  }
  
  .form-group {
    margin-bottom: 20px;
    display: flex;
    flex-direction: column;
    align-items: flex-start;
    width: 100%;
  }
  
  label {
    display: inline-block;
    margin-right: 20px;
  
    color: #555;
    margin-bottom: 8px;
    text-align: left;
    width: 100%;
  }
  
  input {
    width: 355px;
    padding: 12px;
    border: 1px solid #ccc;
    border-radius: 8px;
    background-color: #f9f9f9;
    font-size: 16px;
    margin-bottom: 15px;
    transition: all 0.3s ease-in-out;
  }
  
  input:focus {
    border-color: #D4AF37;
    outline: none;
    background-color: #fff;
  }
  
  .login-button {
    width: 100%;
    padding: 12px;
    background-color: #D4AF37;
    color: white;
    border: none;
    border-radius: 8px;
    cursor: pointer;
    font-size: 16px;
    transition: all 0.3s ease;
  }
  
  .login-button:hover {
    background-color: #b88e14;
  }
  
  .toggle-button {
    width: 100%;
    padding: 10px;
    background-color: transparent;
    color: #B8860B;
    border: none;
    font-size: 14px;
    cursor: pointer;
    margin-top: 15px;
    transition: color 0.3s ease;
  }
  
  .toggle-button:hover {
    color: #D4AF37;
  }
  
  .error-message {
    color: red;
    margin-top: 10px;
    font-size: 14px;
  }
  </style>
  