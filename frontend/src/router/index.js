import { createRouter, createWebHistory } from 'vue-router';
import HomePage from '../components/HomePage.vue';
import LearnMode from '../components/LearnMode.vue';
import ReciteMode from '../components/ReciteMode.vue';
import GameMode from '../components/GameMode.vue';
import FeihuaMode from '../components/FeihuaMode.vue';
import LoginPage from '@/components/LoginPage.vue';

const routes = [
    { path: '/', component: HomePage },
    { path: '/learn', component: LearnMode },
    { path: '/recite', component: ReciteMode },
    { path: '/game', component: GameMode },
    { path: '/feihua', component: FeihuaMode },
    {
        path: '/login',
        name: 'Login',
        component: LoginPage
    },
    {
        path: '/home',
        name: 'Home',
        component: HomePage
    },
];

const router = createRouter({
    history: createWebHistory(),
    routes,
});

export default router;
