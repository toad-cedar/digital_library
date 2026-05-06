import UserLogin from '../components/main/UserLogin.vue';
import { useAuthStore } from '../stores/auth'


export async function apiRequest(endpoint, options = {}) {
  const authStore = useAuthStore();
  const token = authStore.getToken;

  const headers = {
    'Content-Type': 'application/json',
    ...options.headers, // Позволяет переопределять/дополнять заголовки
  };

  if (token) {
    headers['Authorization'] = `Bearer ${token}`
  };

  const response = await fetch(endpoint, {
    ...options,
    headers,
  });

  if (response.status === 401) {
    authStore.clearToken();
    router.push({ name: UserLogin });
  }
  return response;
}