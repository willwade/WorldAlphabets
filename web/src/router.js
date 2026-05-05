import { createRouter, createWebHistory } from 'vue-router';
import HomeView from './views/HomeView.vue';
import IndexView from './views/IndexView.vue';
import DetectLanguageView from './views/DetectLanguageView.vue';
import InflectionBrowserView from './views/InflectionBrowserView.vue';

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    { path: '/', name: 'index', component: IndexView },
    { path: '/explore', name: 'explore', component: HomeView },
    { path: '/explore/:langCode', name: 'language', component: HomeView },
    { path: '/detect-language', name: 'detect-language', component: DetectLanguageView },
    { path: '/inflections', name: 'inflections', component: InflectionBrowserView },
    { path: '/inflections/:locale', name: 'inflection-locale', component: InflectionBrowserView },
    { path: '/:langCode', name: 'home', component: HomeView },
  ],
});

export default router;
