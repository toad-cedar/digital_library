<template>
  <input 
    :value="modelValue" 
    @input="updateInput" 
    class="w-24 border-solid border-gray-300" 
    type="text"
  />
</template>

<script>
export default {
  name: 'TheInput',
  props: {
    modelValue: [ String, Number ]
  },
  methods: {
    updateInput(event) {
      this.$emit('update:modelValue', event.target.value)
    }
  }
}
</script>