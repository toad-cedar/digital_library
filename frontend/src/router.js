import { createRouter, createWebHistory } from 'vue-router'
import HomePage from './components/main/HomePage.vue'
import SearchResults from './components/main/SearchResults.vue'
import FileInfo from './components/main/FileInfo.vue'
import UserLogin from './components/main/UserLogin.vue'
import UserRegister from './components/main/UserRegister.vue'
import PersonalCabinet from './components/main/PersonalCabinet.vue'

const routes = [
  { path: '/', name: "HomePage", component: HomePage },
  { path: '/search', name: "SearchResults", component: SearchResults },
  { path: '/file/:id', name: "FileInfo", component: FileInfo },
  { path: '/login', name: "UserLogin", component: UserLogin },
  { path: '/register', name: "UserRegister", component: UserRegister },
  { path: '/me', name: "PersonalCabinet", component: PersonalCabinet }
]

const router = createRouter({
  history: createWebHistory(),
  routes
});

export default router;
