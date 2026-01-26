<template>
  <div class="data-table">
    <div v-if="loading" class="data-table-loading">
      <Skeleton type="table" :rows="5" :columns="columns.length"></Skeleton>
    </div>
    
    <div v-else-if="data.length === 0" class="data-table-empty">
      <slot name="empty">
        <div class="empty-state">
          <div class="empty-icon">📭</div>
          <div class="empty-text">暂无数据</div>
        </div>
      </slot>
    </div>
    
    <div v-else class="data-table-wrapper">
      <table>
        <thead>
          <tr>
            <th v-for="column in columns" :key="column.key" :class="getHeaderClass(column)">
              <slot :name="`header-${column.key}`" :column="column">
                {{ column.title }}
              </slot>
            </th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(row, rowIndex) in data" :key="getRowKey(row, rowIndex)" :class="getRowClass(row, rowIndex)">
            <td v-for="column in columns" :key="column.key" :class="getCellClass(column)">
              <slot :name="`cell-${column.key}`" :row="row" :column="column" :rowIndex="rowIndex">
                {{ getCellValue(row, column) }}
              </slot>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
    
    <div v-if="showPagination && pagination" class="data-table-pagination">
      <div class="pagination-info">
        共 {{ pagination.total }} 条记录，第 {{ pagination.page }} / {{ pagination.totalPages }} 页
      </div>
      <div class="pagination-controls">
        <button 
          class="pagination-btn" 
          :disabled="!hasPrevPage" 
          @click="handlePrevPage"
        >
          上一页
        </button>
        <button 
          v-for="page in visiblePages" 
          :key="page" 
          class="pagination-btn"
          :class="{ active: page === pagination.page }"
          @click="handleGoToPage(page)"
        >
          {{ page }}
        </button>
        <button 
          class="pagination-btn" 
          :disabled="!hasNextPage" 
          @click="handleNextPage"
        >
          下一页
        </button>
      </div>
    </div>
  </div>
</template>

<script>
import { computed } from 'vue'
import Skeleton from './Skeleton.vue'

export default {
  name: 'DataTable',
  components: {
    Skeleton
  },
  props: {
    data: {
      type: Array,
      default: () => []
    },
    columns: {
      type: Array,
      required: true,
      validator: (value) => {
        return value.every(col => col.key && col.title)
      }
    },
    loading: {
      type: Boolean,
      default: false
    },
    rowKey: {
      type: [String, Function],
      default: 'id'
    },
    showPagination: {
      type: Boolean,
      default: true
    },
    pagination: {
      type: Object,
      default: null
    },
    stripe: {
      type: Boolean,
      default: true
    },
    border: {
      type: Boolean,
      default: true
    },
    hover: {
      type: Boolean,
      default: true
    },
    size: {
      type: String,
      default: 'medium',
      validator: (value) => ['small', 'medium', 'large'].includes(value)
    }
  },
  emits: ['page-change', 'row-click'],
  setup(props, { emit }) {
    const hasPrevPage = computed(() => {
      return props.pagination && props.pagination.page > 1
    })

    const hasNextPage = computed(() => {
      return props.pagination && props.pagination.page < props.pagination.totalPages
    })

    const visiblePages = computed(() => {
      if (!props.pagination) return []
      
      const { page, totalPages } = props.pagination
      const pages = []
      const maxVisible = 5
      
      let start = Math.max(1, page - Math.floor(maxVisible / 2))
      let end = Math.min(totalPages, start + maxVisible - 1)
      
      if (end - start < maxVisible - 1) {
        start = Math.max(1, end - maxVisible + 1)
      }
      
      for (let i = start; i <= end; i++) {
        pages.push(i)
      }
      
      return pages
    })

    const getRowKey = (row, index) => {
      if (typeof props.rowKey === 'function') {
        return props.rowKey(row, index)
      }
      return row[props.rowKey] || index
    }

    const getCellValue = (row, column) => {
      if (column.render) {
        return column.render(row)
      }
      return row[column.key]
    }

    const getHeaderClass = (column) => {
      const classes = []
      if (column.sortable) classes.push('sortable')
      if (column.align) classes.push(`align-${column.align}`)
      if (column.width) classes.push('has-width')
      return classes
    }

    const getCellClass = (column) => {
      const classes = []
      if (column.align) classes.push(`align-${column.align}`)
      return classes
    }

    const getRowClass = (row, index) => {
      const classes = []
      if (props.stripe && index % 2 === 1) classes.push('stripe')
      if (props.hover) classes.push('hover')
      return classes
    }

    const handlePrevPage = () => {
      if (hasPrevPage.value) {
        emit('page-change', props.pagination.page - 1)
      }
    }

    const handleNextPage = () => {
      if (hasNextPage.value) {
        emit('page-change', props.pagination.page + 1)
      }
    }

    const handleGoToPage = (page) => {
      emit('page-change', page)
    }

    const handleRowClick = (row, index) => {
      emit('row-click', row, index)
    }

    return {
      hasPrevPage,
      hasNextPage,
      visiblePages,
      getRowKey,
      getCellValue,
      getHeaderClass,
      getCellClass,
      getRowClass,
      handlePrevPage,
      handleNextPage,
      handleGoToPage,
      handleRowClick
    }
  }
}
</script>

<style scoped>
.data-table {
  width: 100%;
}

.data-table-wrapper {
  overflow-x: auto;
  border: 1px solid var(--border-color);
  border-radius: var(--border-radius);
}

table {
  width: 100%;
  border-collapse: collapse;
  background: white;
}

thead {
  background-color: var(--background-color);
}

th {
  padding: var(--spacing-md);
  text-align: left;
  font-weight: 600;
  color: var(--text-primary);
  border-bottom: 2px solid var(--border-color);
  white-space: nowrap;
}

th.sortable {
  cursor: pointer;
  user-select: none;
}

th.sortable:hover {
  background-color: var(--background-dark);
}

td {
  padding: var(--spacing-md);
  border-bottom: 1px solid var(--border-color);
  color: var(--text-primary);
}

tr.stripe {
  background-color: var(--background-color);
}

tr.hover:hover {
  background-color: var(--secondary-light);
}

.align-left {
  text-align: left;
}

.align-center {
  text-align: center;
}

.align-right {
  text-align: right;
}

.data-table-empty {
  padding: var(--spacing-xl);
  text-align: center;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--spacing-md);
  color: var(--text-secondary);
}

.empty-icon {
  font-size: 48px;
  opacity: 0.5;
}

.empty-text {
  font-size: 16px;
}

.data-table-pagination {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--spacing-md);
  background-color: var(--background-color);
  border: 1px solid var(--border-color);
  border-top: none;
  border-radius: 0 0 var(--border-radius) var(--border-radius);
  margin-top: -1px;
}

.pagination-info {
  font-size: 14px;
  color: var(--text-secondary);
}

.pagination-controls {
  display: flex;
  gap: var(--spacing-xs);
}

.pagination-btn {
  padding: var(--spacing-xs) var(--spacing-sm);
  border: 1px solid var(--border-color);
  background: white;
  border-radius: var(--border-radius-sm);
  cursor: pointer;
  transition: all var(--transition-base);
  font-size: 14px;
  min-width: 32px;
}

.pagination-btn:hover:not(:disabled) {
  background-color: var(--secondary-light);
  border-color: var(--secondary-color);
}

.pagination-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.pagination-btn.active {
  background-color: var(--secondary-color);
  color: white;
  border-color: var(--secondary-color);
}

@media (max-width: 768px) {
  .data-table-pagination {
    flex-direction: column;
    gap: var(--spacing-md);
  }
  
  .pagination-controls {
    flex-wrap: wrap;
    justify-content: center;
  }
}
</style>
