<template>
  <div class="max-w-[1150px] mx-auto" :class="extra">
		<slot/>
	</div>
</template>

<script>
export default {
	name: 'PageFrame',
	props: {
		extra: { 
			type: String, 
			default: '' 
		}
  },
	data() {
    
  }
}
</script>

<style>
	
</style>