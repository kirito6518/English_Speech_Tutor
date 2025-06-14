import { createRouter, createWebHistory } from 'vue-router';
import LearnMode from '../components/LearnMode.vue';
import LoginPage from '@/components/LoginPage.vue';

const routes = [
    { 
        path: '/', 
        redirect: '/learn' // 根路径直接重定向到研学探秘
    },
    { 
        path: '/learn', 
        component: LearnMode 
    },
    {
        path: '/login',
        name: 'Login',
        component: LoginPage
    }
];

const router = createRouter({
    history: createWebHistory(),
    routes,
});

export default router;