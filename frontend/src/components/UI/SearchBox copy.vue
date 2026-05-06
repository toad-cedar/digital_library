<template>
  <PageFrame extra="mt-10">
    <div class="flex items-center justify-center gap-5">
      <SearchInput
        :value="modelValue"
        @input="this.$emit('update:modelValue', $event.target.value)"
        class="w-3/5 md:w-2/5 px-4"
        :placeholder="placeholder"
      />
      <button class="bg-indigo-500 hover:bg-orange-300 px-6 py-1.5 text-white rounded shadow select-none"
        type="button"
      >
        Поиск
      </button>
    </div>
  </PageFrame>
</template>

<script>
import PageFrame from '../UI/PageFrame.vue';
import SearchInput from '../UI/SearchInput.vue';

export default {
  name: 'SearchBox',
  components: {
    PageFrame, SearchInput
  },
	props: {
		modelValue: String,
    placeholder: {
      type: String,
      default: 'Введите запрос',
    },
	},
  emits: ['update:modelValue', 'submit'],
	data() {
    
  }
}
</script>

<style scoped>
	
</style>