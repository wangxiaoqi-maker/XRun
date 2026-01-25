<template>
  <div class="cases-view">
    <div class="page-header">
      <h1>测试用例</h1>
      <div class="header-actions">
        <el-button type="primary" @click="$router.push('/cases/new')">
          <el-icon><Plus /></el-icon> 新建用例
        </el-button>
      </div>
    </div>
    
    <!-- 筛选 -->
    <div class="filter-bar">
      <el-input 
        v-model="searchText" 
        placeholder="搜索用例名称" 
        style="width: 240px;"
        clearable
        @input="onSearch"
      >
        <template #prefix>
          <el-icon><Search /></el-icon>
        </template>
      </el-input>
      
      <el-select v-model="filterPlatform" placeholder="平台" clearable style="width: 120px;" @change="loadCases">
        <el-option value="android" label="Android" />
        <el-option value="ios" label="iOS" />
      </el-select>
    </div>
    
    <!-- 用例列表 -->
    <el-table 
      :data="cases" 
      v-loading="loading"
      stripe
      style="width: 100%"
    >
      <el-table-column prop="name" label="用例名称" min-width="200">
        <template #default="{ row }">
          <router-link :to="`/cases/${row.id}`" class="case-link">
            {{ row.name }}
          </router-link>
        </template>
      </el-table-column>
      
      <el-table-column prop="platform" label="平台" width="100">
        <template #default="{ row }">
          <el-tag size="small" :type="row.platform === 'android' ? 'success' : ''">
            {{ row.platform === 'android' ? 'Android' : 'iOS' }}
          </el-tag>
        </template>
      </el-table-column>
      
      <el-table-column prop="description" label="描述" min-width="200">
        <template #default="{ row }">
          <span class="description">{{ row.description || '-' }}</span>
        </template>
      </el-table-column>
      
      <el-table-column prop="updated_at" label="更新时间" width="180">
        <template #default="{ row }">
          {{ formatDate(row.updated_at) }}
        </template>
      </el-table-column>
      
      <el-table-column label="操作" width="260" fixed="right">
        <template #default="{ row }">
          <el-button size="small" type="primary" @click="showRunDialog(row)">
            <el-icon><VideoPlay /></el-icon> 执行
          </el-button>
          <el-button size="small" @click="$router.push(`/cases/${row.id}`)">
            编辑
          </el-button>
          <el-button size="small" type="danger" @click="deleteCase(row)">
            删除
          </el-button>
        </template>
      </el-table-column>
    </el-table>
    
    <!-- 分页 -->
    <div class="pagination">
      <el-pagination
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :total="total"
        :page-sizes="[20, 50, 100]"
        layout="total, sizes, prev, pager, next"
        @size-change="loadCases"
        @current-change="loadCases"
      />
    </div>
    
    <!-- 执行对话框 -->
    <el-dialog v-model="runDialogVisible" title="执行用例" width="500px">
      <div v-if="selectedCase" class="run-dialog-content">
        <p class="run-case-name">{{ selectedCase.name }}</p>
        
        <el-form label-width="80px">
          <el-form-item label="选择设备">
            <el-select 
              v-model="selectedDevice" 
              placeholder="请选择设备"
              style="width: 100%;"
              :loading="loadingDevices"
            >
              <el-option-group 
                v-if="selectedCase.platform === 'android' || !selectedCase.platform"
                label="Android 设备"
              >
                <el-option
                  v-for="device in devices.android"
                  :key="device.id"
                  :label="`${device.name} (${device.id})`"
                  :value="device.id"
                />
              </el-option-group>
              <el-option-group 
                v-if="selectedCase.platform === 'ios' || !selectedCase.platform"
                label="iOS 设备"
              >
                <el-option
                  v-for="device in devices.ios"
                  :key="device.id"
                  :label="`${device.name} (${device.id})`"
                  :value="device.id"
                />
              </el-option-group>
            </el-select>
          </el-form-item>
          
          <el-form-item v-if="devices.android.length === 0 && devices.ios.length === 0">
            <el-alert type="warning" :closable="false">
              未检测到设备，请连接设备后重试
            </el-alert>
          </el-form-item>
        </el-form>
      </div>
      
      <template #footer>
        <el-button @click="runDialogVisible = false">取消</el-button>
        <el-button 
          type="primary" 
          @click="runCase" 
          :loading="running"
          :disabled="!selectedDevice"
        >
          开始执行
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Search, VideoPlay } from '@element-plus/icons-vue'
import { caseApi, deviceApi, executionApi } from '../api'

const router = useRouter()

const loading = ref(false)
const cases = ref([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(20)
const searchText = ref('')
const filterPlatform = ref('')

const runDialogVisible = ref(false)
const selectedCase = ref(null)
const selectedDevice = ref('')
const devices = ref({ android: [], ios: [] })
const loadingDevices = ref(false)
const running = ref(false)

let searchTimer = null

onMounted(() => {
  loadCases()
})

async function loadCases() {
  loading.value = true
  try {
    const params = {
      skip: (currentPage.value - 1) * pageSize.value,
      limit: pageSize.value
    }
    if (searchText.value) {
      params.search = searchText.value
    }
    if (filterPlatform.value) {
      params.platform = filterPlatform.value
    }
    
    const res = await caseApi.list(params)
    cases.value = res.data.items
    total.value = res.data.total
  } catch (e) {
    ElMessage.error('加载失败')
    console.error(e)
  } finally {
    loading.value = false
  }
}

function onSearch() {
  clearTimeout(searchTimer)
  searchTimer = setTimeout(() => {
    currentPage.value = 1
    loadCases()
  }, 300)
}

function formatDate(dateStr) {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN')
}

async function showRunDialog(row) {
  selectedCase.value = row
  selectedDevice.value = ''
  runDialogVisible.value = true
  
  loadingDevices.value = true
  try {
    const res = await deviceApi.list()
    devices.value = res.data
  } catch (e) {
    console.error(e)
  } finally {
    loadingDevices.value = false
  }
}

async function runCase() {
  if (!selectedDevice.value) {
    ElMessage.warning('请选择设备')
    return
  }
  
  running.value = true
  try {
    const res = await executionApi.run(selectedCase.value.id, selectedDevice.value)
    ElMessage.success('执行已启动')
    runDialogVisible.value = false
    
    // 跳转到执行记录页面
    router.push('/executions')
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '执行失败')
    console.error(e)
  } finally {
    running.value = false
  }
}

async function deleteCase(row) {
  try {
    await ElMessageBox.confirm(
      `确定删除用例「${row.name}」吗？`,
      '确认删除',
      { type: 'warning' }
    )
    
    await caseApi.delete(row.id)
    ElMessage.success('删除成功')
    loadCases()
  } catch (e) {
    if (e !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}
</script>

<style lang="scss" scoped>
.cases-view {
  padding: 24px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  
  h1 {
    font-size: 24px;
    margin: 0;
    color: #fff;
  }
}

.filter-bar {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
}

.case-link {
  color: #409eff;
  text-decoration: none;
  
  &:hover {
    text-decoration: underline;
  }
}

.description {
  color: rgba(255, 255, 255, 0.6);
  font-size: 13px;
}

.pagination {
  margin-top: 24px;
  display: flex;
  justify-content: flex-end;
}

.run-dialog-content {
  .run-case-name {
    font-size: 16px;
    font-weight: 500;
    margin-bottom: 20px;
    padding-bottom: 12px;
    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  }
}
</style>
