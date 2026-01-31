<template>
  <div class="data-table">
    <el-skeleton v-if="loading" :rows="5" :loading="true" animated />

    <el-empty v-else-if="data.length === 0" description="暂无数据" />

    <el-table
      v-else
      :data="data"
      :stripe="stripe"
      :border="border"
      :row-key="rowKey"
      :height="tableHeight"
      @row-click="handleRowClick"
      style="width: 100%"
    >
      <el-table-column
        v-for="column in columns"
        :key="column.key"
        :prop="column.key"
        :label="column.title"
        :width="column.width"
        :align="column.align || 'left'"
        :sortable="column.sortable"
      >
        <template #default="scope">
          <slot :name="`cell-${column.key}`" :row="scope.row" :column="column" :rowIndex="scope.$index">
            {{ getCellValue(scope.row, column) }}
          </slot>
        </template>
      </el-table-column>
    </el-table>

    <el-pagination
      v-if="showPagination && pagination"
      v-model:current-page="currentPage"
      v-model:page-size="pageSize"
      :page-sizes="[10, 20, 50, 100]"
      :total="pagination.total"
      layout="total, sizes, prev, pager, next, jumper"
      @current-change="handlePageChange"
      @size-change="handleSizeChange"
      class="pagination"
    />
  </div>
</template>

<script>
import { ref, computed } from 'vue'

export default {
  name: 'DataTable',
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
    const currentPage = ref(1)
    const pageSize = ref(10)

    const tableHeight = computed(() => {
      return props.data.length > 10 ? '600px' : null
    })

    const getCellValue = (row, column) => {
      if (column.render) {
        return column.render(row)
      }
      return row[column.key]
    }

    const handleRowClick = (row) => {
      emit('row-click', row)
    }

    const handlePageChange = (page) => {
      currentPage.value = page
      emit('page-change', page)
    }

    const handleSizeChange = (size) => {
      pageSize.value = size
      emit('page-change', 1)
    }

    return {
      currentPage,
      pageSize,
      tableHeight,
      getCellValue,
      handleRowClick,
      handlePageChange,
      handleSizeChange
    }
  }
}
</script>

<style scoped>
.data-table {
  width: 100%;
}

.pagination {
  margin-top: var(--spacing-lg);
  display: flex;
  justify-content: flex-end;
}

@media (max-width: 768px) {
  .pagination {
    justify-content: center;
  }
  
  .pagination :deep(.el-pagination) {
    flex-wrap: wrap;
    justify-content: center;
  }
}
</style>
