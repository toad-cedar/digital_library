<template>
  <PageFrame extra="mt-10">
    <div class="flex items-center justify-center gap-5">
      <input
        :value="modelValue" 
        @input="$emit('update:modelValue', $event.target.value)"
        @keydown.enter="$emit('search')"
        type="text"
        class="w-3/5 md:w-2/5 px-4 py-2 border border-gray-300 rounded"
        :placeholder="placeholder"
      />
      <button
        type="button" 
        @click="$emit('search')" 
        class="bg-indigo-500 hover:bg-orange-300 text-white px-4 py-2 rounded transition-colors duration-200"
      >
        Поиск
      </button>
    </div>
  </PageFrame>
</template>

<script>
import PageFrame from './PageFrame.vue'; // Убедитесь, что путь правильный

export default {
  name: 'SearchBox',
  components: { PageFrame },
  props: {
    modelValue: String,
    placeholder: {
      type: String,
      default: 'Введите запрос',
    },
  },
  emits: ['update:modelValue', 'search']
  
};
</script>
