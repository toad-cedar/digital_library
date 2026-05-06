<template>
	<div 
		class="flex fixed top-0 bottom-0 right-0 left-0 bg-gray-100/75" 
		v-if="show == true" 
		@click="hideDialog"
	> 
		<div 
			class="min-h-14 min-w-75 px-5 border rounded-sm bg-white m-auto"
			@click.stop
		>
			<slot/>
		</div>
		
	</div>
</template>

<script>
export default {
	name: 'TheDialog',
	props: {
    show: {
			type: Boolean,
			default: false
		}
  },
	methods: {
		hideDialog() {
			this.$emit('update:show', false)
		}
	}
}
</script>
