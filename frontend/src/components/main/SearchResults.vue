<template>
  <div class="bg-white text-slate-700 min-h-screen flex flex-col">
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
    <div class="grow">
      <main class="max-w-5xl mx-auto px-6">
        <h1 class="text-5xl md:text-6xl font-extralight tracking-tight text-amber-800 text-center my-8">
          Библиотека
        </h1>
        <div class="flex mb-4 gap-2.5">
          <!-- Поисковая строка -->
          <input
              v-model="searchQuery"
              @keydown.enter="onSearch"
              type="text"
              class="w-3/5 md:w-2/5 px-4 py-2 grow border border-gray-300 rounded-md focus:outline-2  outline-gray-100 "
              placeholder="Введите запрос..."
          />
          <button
            class="bg-indigo-500 hover:bg-orange-300 text-white flex px-10 py-1 rounded-md transition-colors duration-200 text-lg font-light"
            @click="onSearch"
          >
            Поиск
          </button>
        </div>

        <p class="text-sm text-gray-600 mb-4 " v-if="!loading && !error && total != 0">
          Найдено результатов: {{ total || 0 }}
        </p>

        <div class="space-y-4">
          <!-- Статус загрузки -->
          <div class="mt-6 justify-center" v-if="loading">
            <p>Поиск...</p>
          </div>

          <!-- Ошибка -->
          <div class="mt-6" v-else-if="error" >
            <p class="text-red-500">Ошибка: {{ error }}</p>
          </div>

          <!-- Результаты поиска -->
          <div v-else-if="!loading && !error">
            <div class="space-y-4">
              <SearchResultsItem
                v-for="doc in documents"
                :key="doc.id"
                :id="doc.id"
                :title="doc.title"
                :description="doc.description"
                :tags="doc.tags"
                :uploader="doc.uploader.username" 
                :format="doc.format.name"        
                :cover-url="doc.cover_url"
                :cover-bucket="doc.cover_bucket || 'uploads'" 
              />
            </div>

            <!-- Пагинация -->
            <div class="mt-4 flex justify-center">
              <TheButton
                v-if="hasMore"
                @click="loadMore"
                :disabled="loading"
                class="bg-indigo-500 hover:bg-orange-300 text-white flex px-10 py-1 my-5 ounded-md transition-colors duration-200 text-lg font-light "
              >
                Загрузить ещё
              </TheButton>

              <!-- Если результатов нет или больше нет -->
              <p v-else-if="documents.length > 0" class="text-center text-gray-500"></p>
              <p v-else class="text-xl text-center text-gray-500 my-10">
                Ничего не найдено
              </p>
            </div>
          </div>
        </div>
      </main>
    </div>
    <TheFooter/>
  </div>
</template>

<script>
import PageFrame from '../UI/PageFrame.vue';
import SearchBox from '../UI/SearchBox.vue';
import SearchResultsItem from '../UI/SearchResultsItem.vue';
import TheButton from '../UI/TheButton.vue';
import TheFooter from '../UI/TheFooter.vue';
import { ref, computed, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useAuthStore } from '../../stores/auth';


export default {
  name: 'SearchResults',
  components: { PageFrame, SearchBox, SearchResultsItem, TheButton, TheFooter },
  setup() {
    const route = useRoute();
    const router = useRouter();
    const authStore = useAuthStore();

    const searchQuery = ref(route.query.q || '');
    const documents = ref([]);
    const offset = ref(0);
    const limit = ref(10);
    const total = ref(0);
    const loading = ref(false);
    const error = ref(null);

    const hasMore = computed(() => documents.value.length < total.value);

    const fetchResults = async () => {
      if (loading.value || !searchQuery.value.trim()) {
        // Если уже грузим или запрос пустой, выходим
        return;
      }

      loading.value = true;
      error.value = null;

      try {
        const params = new URLSearchParams({
          query: searchQuery.value.trim(),
          offset: String(offset.value),
          limit: String(limit.value),
        });

        const response = await fetch(`/api/search?${params.toString()}`);

        if (!response.ok) {
          // Проверяем, есть ли тело ошибки
          let errorMessage = 'Неизвестная ошибка';
          try {
            const errorData = await response.json();
            errorMessage = errorData.detail || errorMessage;
          } catch (e) {
            // Если тело не JSON, используем статус
            errorMessage = response.statusText;
          }
          throw new Error(errorMessage);
        }

        const data = await response.json();
        documents.value = [...documents.value, ...data.documents]; // Добавляем к существующим
        total.value = data.total;
        offset.value = data.offset + data.documents.length; // Увеличиваем offset для следующего запроса

      } catch (err) {
        console.error('Search API Error:', err);
        error.value = err.message || 'Ошибка при поиске';
      } finally {
        loading.value = false;
      }
    };

    const buttonLabel = computed(() => {
      return authStore.isAuthenticated ? 'Личный кабинет' : 'Войти';
    });

		const handleButtonClick = async () => {
      if (authStore.isAuthenticated) {
        // Если пользователь вошёл, перенаправляем на /me
        router.push({ name: 'PersonalCabinet' });
      } else {
        router.push({ name: 'UserLogin' });
      }
    };

    const onSearch = () => {
      // Сброс состояния поиска
      documents.value = [];
      offset.value = 0;
      total.value = 0;
      // Обновляем URL и запускаем новый поиск
      router.push({ name: 'SearchResults', query: { q: searchQuery.value } });
    };

    const loadMore = () => {
      fetchResults();
    };

		const redirectToLogin = () => {
			router.push({ name: 'UserLogin' });
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

    watch(
      () => route.query.q,
      (newQ) => {
        searchQuery.value = newQ || '';
        // Если запрос изменился (и не пустой), сбрасываем и ищем заново
        if (newQ && newQ !== searchQuery.value) {
          documents.value = [];
          offset.value = 0;
          total.value = 0;
        }
        // Если запрос пустой, очищаем результаты
        if (!newQ) {
          documents.value = [];
          offset.value = 0;
          total.value = 0;
        }
        // Запускаем поиск, если есть новый запрос
        if (newQ) {
          fetchResults();
        }
      },
      { immediate: true } // immediate: true запустит callback при первом рендере
    );

    return {
      searchQuery,
      documents,
      hasMore,
      loading,
      error,
      buttonLabel,
      onSearch,
      loadMore,
			redirectToLogin,
      handleButtonClick,
      handleLogout,
      total,
      authStore
    };
  },
};
</script>