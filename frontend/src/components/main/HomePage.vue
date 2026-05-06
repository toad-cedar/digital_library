<template>
  <div class="bg-white text-slate-700 min-h-screen flex flex-col" >
    <!-- Верхняя панель -->
    <header class="flex justify-end p-6 mr-10">
      <a
        href="#"
        class="text-sky-500 hover:underline hover:text-orange-300"
        @click.prevent="handleButtonClick"
      >
        {{ buttonLabel }}
      </a>
      <a
        href="#"
        v-if="authStore.isAuthenticated"
        class="text-red-500 hover:underline hover:text-orange-300 ml-4"
        @click.prevent="handleLogout"
      >
        Выйти
      </a>
    </header>

    <main class="flex grow flex-col items-center mt-24">
      <!-- Логотип -->
      <h1 class="my-10 text-5xl md:text-6xl font-extralight tracking-tight text-amber-800 text-center">
				Библиотека
			</h1>
      <!-- Поисковая строка -->
      <div class="flex w-full max-w-3xl">
        <input
          v-model="searchQuery"
          @keydown.enter="onSearch"
          type="text"
          class="w-3/5 md:w-2/5 px-4 py-2 grow border border-gray-300 rounded-md focus:outline-2  outline-gray-100 "
          placeholder="Введите запрос..."
        />
        
      </div>
      <div class="flex w-full max-w-3xl justify-center mt-5">
        <button
          class="bg-indigo-500 hover:bg-orange-300 text-white px-10 py-1 rounded-md transition-colors duration-200 text-lg font-light"
          @click="onSearch"
        >
          Поиск
        </button>
      </div>
    </main>
    <TheFooter/>
	</div>
</template>

<script>
import PageFrame from '../UI/PageFrame.vue';
import TheFooter from '../UI/TheFooter.vue';
import { ref, computed } from 'vue';
import { useRouter } from 'vue-router';
import { useAuthStore } from '../../stores/auth';

export default {
  name: 'HomePage',
  components: { PageFrame, TheFooter },
  setup() {
    const router = useRouter();
		const authStore = useAuthStore();
    const searchQuery = ref('');

    const onSearch = () => {
      if (searchQuery.value.trim()) {
        // Перенаправляем на страницу поиска с параметром q
        router.push({ name: 'SearchResults', query: { q: searchQuery.value.trim() } });
      }
    };

		const buttonLabel = computed(() => {
      return authStore.isAuthenticated ? 'Личный кабинет' : 'Войти';
    });

		const handleButtonClick = () => {
      if (authStore.isAuthenticated) {
        // Если пользователь вошёл, перенаправляем на /me
        router.push({ name: 'PersonalCabinet' });
      } else {
        router.push({ name: 'UserLogin' });
      }
    };

    const handleLogout = async () => {
      try {
        const response = await apiRequest('/api/auth/logout', {
          method: 'POST',
        });
        if (!response.ok) {
          console.error('Logout API failed, clearing token anyway:', response.status, response.statusText);
          // throw new Error('Logout failed'); // Не всегда нужно выбрасывать ошибку, если токен всё равно удаляется
        } else {
          console.log('Logout API success');
        }

        authStore.clearToken();
        alert('Вы успешно вышли из системы. Вы будете перенаправлены на главную страницу');
        router.push({ name: 'HomePage' });

      } catch (err) {
        console.error('Logout Error:', err);
        alert(`Ошибка при выходе: ${err.message}`);
        authStore.clearToken();
      }
    }

    return {
      searchQuery,
      onSearch,
			buttonLabel,
			handleButtonClick,
      handleLogout,
      authStore
    };
  },
};
</script>

