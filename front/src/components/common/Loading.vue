<template>
  <div v-loading="true" class="loading-container">
    <p v-if="text" class="loading-text">{{ text }}</p>
  </div>
</template>

<script>
export default {
  name: 'Loading',
  props: {
    text: {
      type: String,
      default: '加载中...'
    }
  }
}
</script>

<style scoped>
.loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: var(--spacing-xl);
  min-height: 200px;
}

.loading-text {
  margin-top: var(--spacing-md);
  color: var(--text-secondary);
  font-size: var(--font-size-base);
}
</style>
