<template>
  <div class="bg-white text-slate-700 min-h-screen flex flex-col">
    <header class="flex justify-between items-center p-6">
      <router-link
        class="flex items-center gap-2 text-sky-500 hover:underline hover:text-orange-300"
        :to="{ name: 'HomePage' }" 
      >
        Вернуться на главную
      </router-link>
      <a
        href="#"
        class="text-sky-500 hover:underline hover:text-orange-300"
        @click.prevent="handleButtonClick"
      >
        {{ buttonLabel }}
      </a>
    </header>
    <main class="max-w-6xl mx-auto px-6 gap-8 grow flex-col">
      <!-- Статус загрузки -->
      <div v-if="loading" class="text-center py-10">
        <p>Загрузка информации о документе...</p>
      </div>

      <!-- Ошибка -->
      <div v-else-if="error" class="text-center py-10">
        <p class="text-red-500">Ошибка: {{ error }}</p>
        <router-link :to="{ name: 'HomePage' }" class="text-blue-500 hover:underline">Вернуться на главную</router-link>
      </div>

      <!-- Информация о документе -->
      <div v-else-if="document" class="max-w-6xl mx-auto grid grid-cols-1 md:grid-cols-[280px_1fr] gap-8 mt-10">
        <!-- Обложка -->
        <div class="flex justify-center md:justify-start">
          <img
            v-if="document.cover_url"
            :src="`${minioEndpoint}/${document.cover_bucket || 'uploads'}/${document.cover_url}`"
            :alt="`Обложка для ${document.title}`"
            class="w-full max-w-sm shadow-lg"
          />
          <div
            v-else  
            class="w-[260px] h-[400px] bg-gray-100 flex items-center justify-center text-gray-400 text-sm font-light shadow-md"
          >
            Обложка отсутствует
          </div>
        </div>
        

        <div>
          <!-- Заголовок -->
          <h1 class="text-3xl mb-2 font-bold text-gray-800">
            {{ document.title }}
          </h1>
          <!-- Автор -->
          <p class="text-sky-600 italic">{{ document.author }}</p>

          <!-- Описание -->
          <p class="mt-4 text-sm leading-relaxed text-gray-700">
            {{ document.description || 'Описание отсутствует' }}
          </p>

          <!-- Метаданные -->
          <div class="grid grid-cols-2 gap-x-8 gap-y-2 text-sm mt-6">
            <div><span class="font-medium text-gray-500">Автор:</span> {{ document.author || 'Не указан' }}</div>
            <div><span class="font-medium text-gray-500">Загрузил:</span> {{ document.uploader.username }}</div>
            <div><span class="font-medium text-gray-500">Формат:</span> {{ document.format.name }}</div>
            <div><span class="font-medium text-gray-500">Дата публикации:</span> {{ new Date(document.publish_date).toLocaleDateString() }}</div>
            <div><span class="font-medium text-gray-500">Дата загрузки:</span> {{ new Date(document.upload_date).toLocaleDateString() }}</div>
            <div><span class="font-medium text-gray-500">Размер файла:</span> {{ formatFileSize(document.file_size) }}</div>
            <div class="md:col-span-2"><span class="font-medium">Теги:</span> {{ document.tags.join(', ') }}</div>
            <!-- Отображение статуса -->
            <div class="md:col-span-2"><span class="font-medium">Статус:</span> {{ document.status_name?.name || 'Неизвестен' }}</div>
          </div>
          <!-- Действия, кнопки-->
          <div class="flex flex-wrap gap-3 mt-8">
            <button
              class="border px-6 py-1 rounded hover:bg-gray-100"
              @click="addToLibrary"
            >
              Добавить в избранное
            </button>
            <button
              @click="getPreviewUrl"
              :disabled="!isDocumentApproved"
              class="bg-teal-500 text-white px-6 py-1 rounded-md hover:bg-teal-600 transition-colors disabled:opacity-40"
            >
              Просмотреть документ
            </button>
            <button
              @click="getDownloadUrl"
              :disabled="!isDocumentApproved"
              class="bg-teal-500 hover:bg-teal-600 text-white px-6 py-1 rounded-md transition-colors disabled:opacity-40"
            >
              Скачать документ: {{ document.format.name }}, {{ formatFileSize(document.file_size) }}
            </button>
          </div>
          <!-- сломалось
          <div v-if="document && document.format.name === 'txt'">
            <pre>{{ textContent || 'Загрузка...' }}</pre>
          </div>
          <PdfViewer v-else-if="document && document.format.name === 'pdf'" :url="previewUrl" /> -->
        </div>
          <!-- Временные URL (для отладки, можно скрыть)
          <div v-if="previewUrl" class="mt-4 p-2 bg-gray-100 rounded">
            <p class="text-xs text-gray-500">Предпросмотр URL: <a :href="previewUrl.url" target="_blank" class="text-blue-500">{{ previewUrl.url }}</a></p>
            <p class="text-xs text-gray-500">Истекает: {{ new Date(previewUrl.expires_at).toLocaleString() }}</p>
          </div>
          <div v-if="downloadUrl" class="mt-4 p-2 bg-gray-100 rounded">
            <p class="text-xs text-gray-500">Скачать URL: <a :href="downloadUrl.url" target="_blank" class="text-blue-500">{{ downloadUrl.url }}</a></p>
            <p class="text-xs text-gray-500">Истекает: {{ new Date(downloadUrl.expires_at).toLocaleString() }}</p>
          </div> -->
      </div>

      <!-- Если документ не найден (и нет ошибки от fetch) -->
      <div v-else class="text-center py-10">
        <p>Документ не найден.</p>
        <router-link :to="{ name: 'HomePage' }" class="text-blue-500 hover:underline">Вернуться на главную</router-link>
      </div>
    </main>
    <TheFooter/>
  </div>
</template>

<script>
import { ref, computed, onMounted } from 'vue';
import { useRoute } from 'vue-router';
import { apiRequest } from '../../utils/api';
import { useAuthStore } from '../../stores/auth';
import { useRouter } from 'vue-router';
import TheFooter from '../UI/TheFooter.vue';
// import PdfViewer from '../UI/PdfViewer.vue';

const MINIO_ENDPOINT = 'http://localhost:9000';

export default {
  components: { TheFooter },
  name: 'FileInfo',
  setup() {
    const route = useRoute();
    const document = ref(null);
    const loading = ref(false);
    const error = ref(null);
    const previewUrl = ref(null);
    const downloadUrl = ref(null);
    const authStore = useAuthStore();
    const router = useRouter();
    // const textContent = ref(null); // Для хранения содержимого txt

    const minioEndpoint = computed(() => MINIO_ENDPOINT);

    // Вычисляемое свойство для проверки статуса
    const isDocumentApproved = computed(() => {
      // Проверяем, что document и document.status_name существуют, и что имя статуса 'approved'
      return document.value && document.value.status_name && document.value.status_name.name === 'approved';
    });

    const fetchDocument = async () => {
      const id = route.params.id;
      if (!id) {
        error.value = 'ID документа отсутствует.';
        return;
      }

      loading.value = true;
      error.value = null;
      document.value = null;

      try {
        const response = await apiRequest(`/api/documents/${id}`);

        if (!response.ok) {
          let errorMessage = 'Неизвестная ошибка';
          try {
            const errorData = await response.json();
            errorMessage = errorData.detail || errorMessage;
          } catch (e) {
            errorMessage = response.statusText;
          }
          throw new Error(errorMessage);
        }

        const data = await response.json();
        document.value = data;

      } catch (err) {
        console.error('Fetch Document API Error:', err);
        error.value = err.message || 'Ошибка при загрузке информации о документе';
        document.value = null;
      } finally {
        loading.value = false;
      }
    };

    const getPreviewUrl = async () => {
      if (!document.value) return;

      try {
        const response = await apiRequest(`/api/documents/${document.value.id}/preview-url`);

        if (!response.ok) {
          let errorMessage = 'Неизвестная ошибка';
          try {
            const errorData = await response.json();
            errorMessage = errorData.detail || errorMessage;
          } catch (e) {
            errorMessage = response.statusText;
          }
          throw new Error(errorMessage);
        }

        const data = await response.json();
        previewUrl.value = data;

        window.open(data.url, '_blank'); // Открываем URL в новой вкладке (для PDF.js или браузера)

      } catch (err) {
        console.error('Fetch Preview URL API Error:', err);
        alert(`Ошибка получения URL предпросмотра: ${err.message}`);
      }
    };

    const getDownloadUrl = async () => {
      if (!document.value) return;

      try {
        const response = await apiRequest(`/api/documents/${document.value.id}/download-url`);

        if (!response.ok) {
          let errorMessage = 'Неизвестная ошибка';
          try {
            const errorData = await response.json();
            errorMessage = errorData.detail || errorMessage;
          } catch (e) {
            errorMessage = response.statusText;
          }
          throw new Error(errorMessage);
        }

        const data = await response.json();
        downloadUrl.value = data;

        window.open(data.url, '_blank'); // Открываем URL для скачивания

      } catch (err) {
        console.error('Fetch Download URL API Error:', err);
        alert(`Ошибка получения URL для скачивания: ${err.message}`);
      }
    };

    const formatFileSize = (bytes) => {
      if (bytes === 0) return '0 Bytes';
      const k = 1024;
      const sizes = ['Bytes', 'KB', 'MB', 'GB'];
      const i = Math.floor(Math.log(bytes) / Math.log(k));
      return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    };

    const buttonLabel = computed(() => {
      return authStore.isAuthenticated ? 'Личный кабинет' : 'Войти';
    });

		const handleButtonClick = () => {
      if (authStore.isAuthenticated) {
        router.push({ name: 'PersonalCabinet' });
      } else {
        router.push({ name: 'UserLogin' });
      }
    };

    const fetchTextContent = async (previewUrl) => {
      try {
        // fetch к URL текстового файла
        const response = await fetch(previewUrl);
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        textContent.value = await response.text();
      } catch (err) {
        console.error('Fetch Text Content Error:', err);
        textContent.value = 'Ошибка загрузки содержимого файла.';
      }
    };
    
    onMounted(() => {
      fetchDocument();
    });

    return {
      document,
      loading,
      error,
      minioEndpoint,    
      previewUrl,
      downloadUrl,
      getPreviewUrl,
      getDownloadUrl,
      formatFileSize,
      isDocumentApproved,
      buttonLabel,
      handleButtonClick,
      fetchTextContent
    };
  },
  methods: {
    addToLibrary() {
      alert("Нажата кнопка \"Добавить в библиотеку\". \nЭта функция ещё не работает так как нет даже её фундамента")
      console.warn("Нажата кнопка \"Добавить в библиотеку\"")
    }
  }
};
</script>
