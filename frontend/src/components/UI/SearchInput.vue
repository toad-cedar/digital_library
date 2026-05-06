<template>
	<TheInput
		v-bind="$attrs"
		class="py-1.5 shadow-2xl borderpx-4 rounded-sm 
					focus:outline-none focus:ring-2 focus:ring-brandBlue
					shadow-gray-400"
		placeholder="Введите текст"
	/>
</template>

<script>
import TheInput from './TheInput.vue';

export default {
	name: 'SearchInput',
	components: { TheInput },
	data() {
    
  }
}
</script>

<style>
	
</style>