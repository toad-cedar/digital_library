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
      <div class="max-w-md mx-auto bg-white p-6 rounded-lg shadow-md">
        <h2 class="text-xl font-semibold mb-4 place-self-center">Регистрация</h2>
        <form @submit.prevent="register">
          <div class="mb-4">
            <label for="reg_username" class="block text-sm font-medium text-gray-700">Имя пользователя</label>
            <input
              id="reg_username"
              v-model="username"
              type="text"
              placeholder="Введите ваш логин..."
              required
              class="mt-1 block w-full px-3 py-1 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
            />
          </div>
          <div class="mb-4">
            <label for="reg_email" class="block text-sm font-medium text-gray-700">Электронная почта</label>
            <input
              id="reg_email"
              v-model="email"
              type="email"
              placeholder="Пример: example@gmail.ru"
              required
              class="mt-1 block w-full px-3 py-1 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
            />
          </div>
          <div class="mb-4">
            <label for="reg_password" class="block text-sm font-medium text-gray-700">Пароль</label>
            <input
              id="reg_password"
              v-model="password"
              type="password"
              placeholder="Введите свой пароль..."
              required
              class="mt-1 block w-full px-3 py-1 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
            />
            <p class="mt-1 text-xs font-light text-black-500">Пароль должен быть: >= 8 символов, содержать строчные и заглавные буквы, содержать спецсимволы</p>
          </div>
          <div v-if="error" class="mb-4 text-red-500 text-sm">
            {{ error }}
          </div>
          <button
            type="submit"
            :disabled="loading"
            class="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm 
            text-sm font-medium text-white bg-indigo-500 hover:bg-indigo-600 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50"
          >
            {{ loading ? 'Регистрация...' : 'Зарегистрироваться' }}
          </button>
        </form>
      </div>
    </main>
    <TheFooter/>
  </div>
</template>

<script>
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import { apiRequest } from '../../utils/api.js';
import TheFooter from '../UI/TheFooter.vue';

export default {
  components: { TheFooter },
  name: 'RegisterForm',
  setup() {
    const router = useRouter();

    const username = ref('');
    const email = ref('');
    const password = ref('');
    const loading = ref(false);
    const error = ref('');

    const register = async () => {
      loading.value = true;
      error.value = '';

      try {
        const response = await apiRequest('/api/auth/register', {
          method: 'POST',
          body: JSON.stringify({
            username: username.value,
            email: email.value,
            password: password.value,
          }),
        });

        if (!response.ok) {
          const errorData = await response.json();
          throw new Error(errorData.detail || 'Ошибка регистрации');
        }

        const data = await response.json();
        console.log('Регистрация успешна:', data);

        alert('Регистрация прошла успешно! Вы будете перенаправлены на страницу входа');
        router.push({ name: 'UserLogin' });

      } catch (err) {
        console.error('Register Error:', err);
        error.value = err.message;
      } finally {
        loading.value = false;
      }
    };

    return {
      username,
      email,
      password,
      loading,
      error,
      register,
    };
  },
};
</script>