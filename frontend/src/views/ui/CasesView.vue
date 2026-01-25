<template>
  <div class="cases-page">
    <!-- 页面标题栏 -->
    <div class="page-header">
      <div class="header-left">
        <h1>用例管理</h1>
        <el-tag size="small">共 {{ total }} 条</el-tag>
      </div>
      <div class="header-actions">
        <el-input
          v-model="searchKeyword"
          placeholder="搜索用例名称"
          prefix-icon="Search"
          clearable
          style="width: 250px;"
          @keyup.enter="handleSearch"
        />
        <el-select v-model="filterPlatform" placeholder="平台" style="width: 120px;" @change="handleSearch">
          <el-option label="全部" value="" />
          <el-option label="Android" value="android" />
          <el-option label="iOS" value="ios" />
        </el-select>
        <el-select v-model="filterStatus" placeholder="状态" style="width: 120px;" @change="handleSearch">
          <el-option label="全部" value="" />
          <el-option label="启用" value="enabled" />
          <el-option label="禁用" value="disabled" />
        </el-select>
        <el-button type="primary" @click="createCase">
          <el-icon><Plus /></el-icon> 新建用例
        </el-button>
        <el-dropdown trigger="click">
          <el-button>
            <el-icon><More /></el-icon>
          </el-button>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item @click="importCases">
                <el-icon><Upload /></el-icon>导入用例
              </el-dropdown-item>
              <el-dropdown-item @click="exportCases">
                <el-icon><Download /></el-icon>导出用例
              </el-dropdown-item>
              <el-dropdown-item divided @click="batchDelete" :disabled="selectedCases.length === 0">
                <el-icon><Delete /></el-icon>批量删除
              </el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </div>
    
    <!-- 用例列表 -->
    <div class="cases-table">
      <el-table 
        :data="cases" 
        style="width: 100%"
        v-loading="loading"
        @selection-change="handleSelectionChange"
        row-key="id"
      >
        <el-table-column type="selection" width="50" />
        
        <el-table-column prop="name" label="用例名称" min-width="250">
          <template #default="{ row }">
            <div class="case-name">
              <el-icon v-if="row.platform === 'android'" class="platform-icon android">
                <svg viewBox="0 0 24 24" fill="currentColor"><path d="M17.6 9.48l1.84-3.18c.16-.31.04-.69-.26-.85a.637.637 0 0 0-.83.22l-1.88 3.24a11.463 11.463 0 0 0-8.94 0L5.65 5.67a.643.643 0 0 0-.87-.2c-.28.18-.37.54-.22.83L6.4 9.48A10.78 10.78 0 0 0 1 18h22a10.78 10.78 0 0 0-5.4-8.52z"/></svg>
              </el-icon>
              <el-icon v-else class="platform-icon ios">
                <svg viewBox="0 0 24 24" fill="currentColor"><path d="M18.71 19.5c-.83 1.24-1.71 2.45-3.05 2.47-1.34.03-1.77-.79-3.29-.79-1.53 0-2 .77-3.27.82-1.31.05-2.3-1.32-3.14-2.53C4.25 17 2.94 12.45 4.7 9.39c.87-1.52 2.43-2.48 4.12-2.51 1.28-.02 2.5.87 3.29.87.78 0 2.26-1.07 3.81-.91.65.03 2.47.26 3.64 1.98-.09.06-2.17 1.28-2.15 3.81.03 3.02 2.65 4.03 2.68 4.04-.03.07-.42 1.44-1.38 2.83M13 3.5c.73-.83 1.94-1.46 2.94-1.5.13 1.17-.34 2.35-1.04 3.19-.69.85-1.83 1.51-2.95 1.42-.15-1.15.41-2.35 1.05-3.11z"/></svg>
              </el-icon>
              <span class="name-text" @click="editCase(row)">{{ row.name }}</span>
            </div>
          </template>
        </el-table-column>
        
        <el-table-column prop="steps_count" label="步骤数" width="100" align="center">
          <template #default="{ row }">
            <el-tag size="small" type="info">{{ row.steps_count || 0 }} 步</el-tag>
          </template>
        </el-table-column>
        
        <el-table-column prop="last_result" label="最近执行" width="100" align="center">
          <template #default="{ row }">
            <el-tag 
              v-if="row.last_result"
              size="small" 
              :type="row.last_result === 'pass' ? 'success' : 'danger'"
            >
              {{ row.last_result === 'pass' ? '通过' : '失败' }}
            </el-tag>
            <span v-else class="text-muted">未执行</span>
          </template>
        </el-table-column>
        
        <el-table-column prop="status" label="状态" width="100" align="center">
          <template #default="{ row }">
            <el-switch
              v-model="row.enabled"
              size="small"
              @change="toggleCaseStatus(row)"
            />
          </template>
        </el-table-column>
        
        <el-table-column prop="updated_at" label="更新时间" width="180">
          <template #default="{ row }">
            {{ formatDate(row.updated_at) }}
          </template>
        </el-table-column>
        
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link size="small" @click="editCase(row)">
              编辑
            </el-button>
            <el-button type="success" link size="small" @click="runCase(row)">
              执行
            </el-button>
            <el-button type="info" link size="small" @click="copyCase(row)">
              复制
            </el-button>
            <el-button type="danger" link size="small" @click="deleteCase(row)">
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
      
      <!-- 分页 -->
      <div class="pagination-wrapper">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :page-sizes="[10, 20, 50, 100]"
          :total="total"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSearch"
          @current-change="handleSearch"
        />
      </div>
    </div>
    
    <!-- 执行用例弹窗 -->
    <el-dialog v-model="runDialogVisible" title="执行用例" width="500px">
      <el-form label-width="100px">
        <el-form-item label="选择设备">
          <el-select v-model="runConfig.deviceUdid" placeholder="请选择设备" style="width: 100%;">
            <el-option-group label="Android">
              <el-option
                v-for="device in onlineDevices.android"
                :key="device.udid"
                :label="device.name"
                :value="device.udid"
              />
            </el-option-group>
            <el-option-group label="iOS">
              <el-option
                v-for="device in onlineDevices.ios"
                :key="device.udid"
                :label="device.name"
                :value="device.udid"
              />
            </el-option-group>
          </el-select>
        </el-form-item>
        <el-form-item label="执行环境">
          <el-select v-model="runConfig.env" style="width: 100%;">
            <el-option label="测试环境" value="test" />
            <el-option label="预发环境" value="staging" />
            <el-option label="生产环境" value="production" />
          </el-select>
        </el-form-item>
        <el-form-item label="失败重试">
          <el-input-number v-model="runConfig.retryCount" :min="0" :max="3" />
          <span class="ml-10 text-muted">次</span>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="runDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="confirmRunCase" :loading="running">
          开始执行
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, More, Upload, Download, Delete, Search } from '@element-plus/icons-vue'
import { caseApi, deviceApi } from '@/api'

const router = useRouter()

const loading = ref(false)
const cases = ref([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(20)

const searchKeyword = ref('')
const filterPlatform = ref('')
const filterStatus = ref('')
const selectedCases = ref([])

// 执行配置
const runDialogVisible = ref(false)
const running = ref(false)
const currentCase = ref(null)
const runConfig = reactive({
  deviceUdid: '',
  env: 'test',
  retryCount: 1
})

// 在线设备
const onlineDevices = ref({ android: [], ios: [] })

function formatDate(date) {
  if (!date) return '-'
  return new Date(date).toLocaleString('zh-CN')
}

async function loadCases() {
  loading.value = true
  try {
    const res = await caseApi.list({
      page: currentPage.value,
      page_size: pageSize.value,
      keyword: searchKeyword.value,
      platform: filterPlatform.value
    })
    cases.value = res.data.items || []
    total.value = res.data.total || 0
  } catch (e) {
    ElMessage.error('加载用例失败')
  } finally {
    loading.value = false
  }
}

async function loadDevices() {
  try {
    const res = await deviceApi.list()
    onlineDevices.value = {
      android: (res.data.android || []).filter(d => d.status === 'connected'),
      ios: (res.data.ios || []).filter(d => d.status === 'connected')
    }
  } catch (e) {
    console.error(e)
  }
}

function handleSearch() {
  currentPage.value = 1
  loadCases()
}

function handleSelectionChange(selection) {
  selectedCases.value = selection
}

function createCase() {
  router.push('/ui/cases/new')
}

function editCase(row) {
  router.push(`/ui/cases/${row.id}/edit`)
}

function runCase(row) {
  currentCase.value = row
  runDialogVisible.value = true
}

async function confirmRunCase() {
  if (!runConfig.deviceUdid) {
    ElMessage.warning('请选择设备')
    return
  }
  
  running.value = true
  try {
    await caseApi.run(currentCase.value.id, {
      device_udid: runConfig.deviceUdid,
      env: runConfig.env,
      retry_count: runConfig.retryCount
    })
    ElMessage.success('用例已开始执行')
    runDialogVisible.value = false
    router.push('/ui/executions')
  } catch (e) {
    ElMessage.error('执行失败')
  } finally {
    running.value = false
  }
}

async function copyCase(row) {
  try {
    await caseApi.copy(row.id)
    ElMessage.success('复制成功')
    loadCases()
  } catch (e) {
    ElMessage.error('复制失败')
  }
}

async function deleteCase(row) {
  try {
    await ElMessageBox.confirm(`确定删除用例 "${row.name}" 吗？`, '确认删除', {
      type: 'warning'
    })
    
    await caseApi.delete(row.id)
    ElMessage.success('删除成功')
    loadCases()
  } catch (e) {
    if (e !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

async function toggleCaseStatus(row) {
  try {
    await caseApi.update(row.id, { enabled: row.enabled })
    ElMessage.success(row.enabled ? '已启用' : '已禁用')
  } catch (e) {
    row.enabled = !row.enabled
    ElMessage.error('操作失败')
  }
}

function importCases() {
  ElMessage.info('功能开发中')
}

function exportCases() {
  ElMessage.info('功能开发中')
}

async function batchDelete() {
  if (selectedCases.value.length === 0) return
  
  try {
    await ElMessageBox.confirm(`确定删除选中的 ${selectedCases.value.length} 条用例吗？`, '确认删除', {
      type: 'warning'
    })
    
    // 批量删除
    await Promise.all(selectedCases.value.map(c => caseApi.delete(c.id)))
    ElMessage.success('批量删除成功')
    loadCases()
  } catch (e) {
    if (e !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

onMounted(() => {
  loadCases()
  loadDevices()
})
</script>

<style lang="scss" scoped>
.cases-page {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  
  .header-left {
    display: flex;
    align-items: center;
    gap: 12px;
    
    h1 {
      font-size: 20px;
      font-weight: 600;
      margin: 0;
    }
  }
  
  .header-actions {
    display: flex;
    gap: 12px;
  }
}

.cases-table {
  flex: 1;
  background: var(--card-bg);
  border-radius: 12px;
  border: 1px solid var(--border-color);
  padding: 20px;
  display: flex;
  flex-direction: column;
}

.case-name {
  display: flex;
  align-items: center;
  gap: 8px;
  
  .platform-icon {
    font-size: 18px;
    
    svg {
      width: 18px;
      height: 18px;
    }
    
    &.android {
      color: #3ddc84;
    }
    
    &.ios {
      color: #999;
    }
  }
  
  .name-text {
    cursor: pointer;
    color: var(--primary-color);
    
    &:hover {
      text-decoration: underline;
    }
  }
}

.text-muted {
  color: var(--text-muted);
  font-size: 13px;
}

.ml-10 {
  margin-left: 10px;
}

.pagination-wrapper {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}
</style>






