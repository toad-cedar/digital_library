<template>
  <div class="min-h-screen flex flex-col">
    <header class="flex justify-between items-center p-6">
      <router-link
        class="flex items-center gap-2 text-sky-500 hover:underline hover:text-orange-300"
        :to="{ name: 'HomePage' }" 
      >
        Вернуться на главную
      </router-link>
    </header>
    <main class="row flex grow items-center justify-center">
      <div class="max-w-md w-full bg-white p-6 rounded-lg shadow-lg">
        <h2 class="text-xl font-semibold text-center mb-4">
          Вход в учётную запись
        </h2>

        <form @submit.prevent="login">
          <div class="mb-4">
            <label
              for="username"
              class="block text-sm font-medium text-gray-700"
            >
              Имя пользователя
            </label>
            <input
              id="username"
              v-model="username"
              type="text"
              required
              class="mt-1 block w-full px-3 py-1 border border-gray-300 rounded-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
            />
          </div>

          <div class="mb-4">
            <label
              for="password"
              class="block text-sm font-medium text-gray-700"
            >
              Пароль
            </label>
            <input
              id="password"
              v-model="password"
              type="password"
              required
              class="mt-1 block w-full px-3 py-1 border border-gray-300 rounded-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
            />
          </div>

          <div v-if="error" class="mb-4 text-red-500 text-sm">
            {{ error }}
          </div>
          
          <button
            type="submit"
            :disabled="loading"
            class="w-full py-2 px-4 rounded-md text-white bg-indigo-500 hover:bg-indigo-600 disabled:opacity-50"
          >
            {{ loading ? 'Вход...' : 'Войти' }}
          </button>

          <div class="mt-4 text-center text-sm">
            <p class="text-gray-600">
              Нет аккаунта?
              <router-link
                :to="{ name: 'UserRegister' }"
                class="text-indigo-600 hover:text-indigo-500"
              >
                Зарегистрироваться
              </router-link>
            </p>
          </div>
        </form>
      </div>
    </main>
    <TheFooter/>
  </div>
</template>

<script>
import TheFooter from '../UI/TheFooter.vue';

import { ref } from 'vue';
import { useRouter } from 'vue-router';
import { useAuthStore } from '../../stores/auth'; 
import { apiRequest } from '../../utils/api.js';

export default {
  components: { TheFooter },
  name: 'LoginForm',
  setup() {
    const router = useRouter();
    const authStore = useAuthStore();

    const username = ref('');
    const password = ref('');
    const loading = ref(false);
    const error = ref('');

    const login = async () => {
      loading.value = true;
      error.value = '';

      try {
        const response = await apiRequest('/api/auth/login', {
          method: 'POST',
          body: JSON.stringify({
            username: username.value,
            password: password.value,
          }),
        });

        if (!response.ok) {
          const errorData = await response.json();
          throw new Error(errorData.detail || 'Ошибка входа');
        }

        const data = await response.json();
        
        authStore.setToken(data.access_token); // Сохраняем токен в store

        router.push({ name: 'HomePage' });

      } catch (err) {
        console.error('Login Error:', err);
        error.value = err.message;
      } finally {
        loading.value = false;
      }
    };

    return {
      username,
      password,
      loading,
      error,
      login,
    };
  },
};
</script>