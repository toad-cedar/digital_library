import './style.css'
import { createApp } from 'vue'
import { createPinia } from 'pinia'
import router from './router.js'
import App from './App.vue'
import components from './components/UI' // Массив всех UI компонентов

const pinia = createPinia();
const app = createApp(App);

components.forEach(component => {
  app.component(component.name, component)
});

app.use(router).use(pinia).mount('#app');
