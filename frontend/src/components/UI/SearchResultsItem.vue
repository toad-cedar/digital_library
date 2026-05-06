<template>
  <div
    class="border-s-4 border-amber-700 rounded-lg p-4
            bg-gray-50 border shadow hover:shadow-md
            transition-shadow duration-100
            flex gap-4"
  >
    <!-- Левая часть -->
    <router-link 
      :to="{ name: 'FileInfo', params: { id } }"
      class="flex gap-4 min-w-0"
    >
      <!-- Обложка -->
      <img
        v-if="coverUrl"
        :src="`${minioEndpoint}/${coverBucket}/${coverUrl}`"
        :alt="`Обложка для ${title}`"
        class="w-28 h-36 object-cover rounded shrink-0 shadow-xs"
        loading="lazy"
      />
      <!-- Заголовок -->
      <div class="min-w-0">
        <h3
          class="text-lg font-semibold text-sky-600 hover:underline truncate"
        >
          {{ title }}
        </h3>
      </div>
      <!-- Описание -->
      <!-- <p class="mt-2 text-sm text-slate-700 line-clamp-3">{{ truncatedDescription }}</p> -->
    </router-link>

    <!-- Правая часть -->
    <div class="ml-auto text-xs text-gray-500 space-y-1 text-right shrink-0 self-end">
      <!-- <p v-if="author">
        <span class="font-medium">Автор: </span> {{ author }}
      </p> -->
      <p v-if="format">
        <span class="font-medium">Формат: </span> {{ format }}
      </p>
      <p v-if="tags">
        <span class="font-medium">Теги: </span>{{ tags.join(', ') }}
      </p>
    </div>
  </div>
</template>


<script>
const MINIO_ENDPOINT = 'http://localhost:9000';
export default {
  name: 'SearchResultsItem',
  props: {
    id: {
      type: Number,
      required: true,
    },
    title: {
      type: String,
      required: true,
    },
    description: { 
      type: String,
      required: true,
      default: null
    },
    tags: {
      type: Array,
      required: true,
      validator: (value) => value.every(tag => typeof tag === 'string'),
    },
    format: {
      type: String,
      required: true,
    },
    coverUrl: {
      type: String,
      default: null,
    },
    coverBucket: {
      type: String,
      default: 'uploads'
    },
    author: {
      type: String,
      default: null,
    },
    maxDescriptionLength: {
      type: Number,
      default: 80, // Обрезать до 100 символов
    },
  },
  computed: {
    truncatedDescription() {
      if (this.description && this.description.length > this.maxDescriptionLength) {
        return this.description.substring(0, this.maxDescriptionLength) + '...';
      }
      return this.description;
    },
    minioEndpoint() {
      return MINIO_ENDPOINT;
    }
  },
};
</script>

<style scoped>
.line-clamp-2 {    
  display: -webkit-box; 
  -webkit-line-clamp: 2; 
  -webkit-box-orient: vertical; 
  overflow: hidden; 
  line-clamp: line-clamp-2;
}
</style>