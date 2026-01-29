<template>
  <div class="skeleton" :class="{ 'skeleton-animated': animated }">
    <div v-if="type === 'text'" class="skeleton-text" :style="{ width, height }"></div>
    <div v-else-if="type === 'avatar'" class="skeleton-avatar" :style="{ width, height }"></div>
    <div v-else-if="type === 'block'" class="skeleton-block" :style="{ width, height }"></div>
    <div v-else-if="type === 'card'" class="skeleton-card">
      <div class="skeleton-card-header">
        <div class="skeleton-title"></div>
      </div>
      <div class="skeleton-card-body">
        <div v-for="i in rows" :key="i" class="skeleton-row"></div>
      </div>
    </div>
    <div v-else-if="type === 'list'" class="skeleton-list">
      <div v-for="i in count" :key="i" class="skeleton-list-item">
        <div class="skeleton-list-avatar"></div>
        <div class="skeleton-list-content">
          <div class="skeleton-list-title"></div>
          <div class="skeleton-list-desc"></div>
        </div>
      </div>
    </div>
    <div v-else-if="type === 'table'" class="skeleton-table">
      <div class="skeleton-table-header">
        <div v-for="i in columns" :key="i" class="skeleton-table-cell"></div>
      </div>
      <div v-for="row in rows" :key="row" class="skeleton-table-row">
        <div v-for="col in columns" :key="col" class="skeleton-table-cell"></div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'Skeleton',
  props: {
    type: {
      type: String,
      default: 'text',
      validator: (value) => ['text', 'avatar', 'block', 'card', 'list', 'table'].includes(value)
    },
    width: {
      type: String,
      default: '100%'
    },
    height: {
      type: String,
      default: '16px'
    },
    animated: {
      type: Boolean,
      default: true
    },
    rows: {
      type: Number,
      default: 3
    },
    count: {
      type: Number,
      default: 5
    },
    columns: {
      type: Number,
      default: 4
    }
  }
}
</script>

<style scoped>
.skeleton {
  background: linear-gradient(
    90deg,
    var(--background-color) 25%,
    var(--background-dark) 37%,
    var(--background-color) 63%
  );
  background-size: 400% 100%;
  border-radius: var(--border-radius);
  display: inline-block;
}

.skeleton-animated {
  animation: skeleton-loading 1.4s ease infinite;
}

@keyframes skeleton-loading {
  0% {
    background-position: 100% 50%;
  }
  100% {
    background-position: 0 50%;
  }
}

.skeleton-text {
  height: 16px;
  border-radius: 2px;
}

.skeleton-avatar {
  border-radius: 50%;
}

.skeleton-block {
  display: block;
}

.skeleton-card {
  background: white;
  border-radius: var(--border-radius-lg);
  padding: var(--spacing-lg);
  box-shadow: var(--shadow-sm);
}

.skeleton-card-header {
  margin-bottom: var(--spacing-lg);
}

.skeleton-title {
  height: 24px;
  width: 60%;
  margin-bottom: var(--spacing-md);
  border-radius: var(--border-radius);
}

.skeleton-card-body {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.skeleton-row {
  height: 16px;
  border-radius: 2px;
}

.skeleton-list {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-lg);
}

.skeleton-list-item {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
  padding: var(--spacing-md);
  background: white;
  border-radius: var(--border-radius);
  box-shadow: var(--shadow-sm);
}

.skeleton-list-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  flex-shrink: 0;
}

.skeleton-list-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

.skeleton-list-title {
  height: 18px;
  width: 70%;
  border-radius: 2px;
}

.skeleton-list-desc {
  height: 14px;
  width: 100%;
  border-radius: 2px;
}

.skeleton-table {
  background: white;
  border-radius: var(--border-radius);
  overflow: hidden;
  box-shadow: var(--shadow-sm);
}

.skeleton-table-header {
  display: flex;
  border-bottom: 1px solid var(--border-color);
  padding: var(--spacing-md);
  gap: var(--spacing-md);
}

.skeleton-table-row {
  display: flex;
  border-bottom: 1px solid var(--border-color);
  padding: var(--spacing-md);
  gap: var(--spacing-md);
}

.skeleton-table-cell {
  height: 16px;
  border-radius: 2px;
  flex: 1;
}

@media (max-width: 768px) {
  .skeleton-card {
    padding: var(--spacing-md);
  }
  
  .skeleton-list-item {
    flex-direction: column;
    align-items: flex-start;
  }
  
  .skeleton-table-header,
  .skeleton-table-row {
    flex-direction: column;
    gap: var(--spacing-sm);
  }
  
  .skeleton-table-cell {
    width: 100%;
  }
}
</style>
