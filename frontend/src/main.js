import { createApp } from 'vue';
import App from './App.vue';
import router from './router';  // 导入 router 配置
import ElementPlus from 'element-plus';
import 'element-plus/dist/index.css';

createApp(App)
  .use(router)  // 使用 Vue Router
  .use(ElementPlus)
  .mount('#app');
