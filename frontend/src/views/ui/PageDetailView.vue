<template>
  <div class="page-detail">
    <!-- 顶部导航栏 -->
    <div class="detail-header">
      <div class="header-left">
        <el-button text @click="goBack" class="back-btn">
          <el-icon><ArrowLeft /></el-icon>
          返回列表
        </el-button>
        <div class="divider"></div>
        <div class="page-info" v-if="pageData">
          <el-tag :color="getAppColor(pageData.app_name)" effect="dark" size="small">
            {{ pageData.app_name }}
          </el-tag>
          <h2 class="page-name">{{ pageData.page_name }}</h2>
          <el-tag size="small" type="info">{{ pageData.page_type }}</el-tag>
        </div>
      </div>
      <div class="header-right">
        <el-button @click="goToReAnalyze">
          <el-icon><Refresh /></el-icon>
          重新识别
        </el-button>
        <el-button type="danger" @click="handleDelete">
          <el-icon><Delete /></el-icon>
          删除页面
        </el-button>
      </div>
    </div>

    <!-- 主体内容 -->
    <div class="detail-body" v-loading="loading">
      <!-- 左侧：页面信息卡片 -->
      <div class="info-column">
        <!-- 页面截图预览 -->
        <div class="screenshot-card" v-if="pageData">
          <div class="screenshot-preview" @click="showScreenshotDialog = true">
            <img 
              v-if="pageData.screenshot_url" 
              :src="pageData.screenshot_url" 
              class="screenshot-image"
              @error="handleImageError"
            />
            <div v-else class="screenshot-placeholder">
              <el-icon :size="48"><Picture /></el-icon>
              <span>暂无截图</span>
            </div>
            <div class="screenshot-overlay" v-if="pageData.screenshot_url">
              <el-icon :size="24"><ZoomIn /></el-icon>
              <span>点击放大</span>
            </div>
          </div>
        </div>
        
        <!-- 页面基本信息 -->
        <div class="info-card">
          <h3 class="card-title">页面信息</h3>
          <div class="info-grid" v-if="pageData">
            <div class="info-item full">
              <span class="info-label">页面描述</span>
              <p class="info-value">{{ pageData.page_description || '暂无描述' }}</p>
            </div>
            <div class="info-item full" v-if="pageData.user_context">
              <span class="info-label">用户备注</span>
              <p class="info-value">{{ pageData.user_context }}</p>
            </div>
            <div class="info-item">
              <span class="info-label">元素数量</span>
              <span class="info-value highlight">{{ elements.length }}</span>
            </div>
            <div class="info-item">
              <span class="info-label">置信度</span>
              <span class="info-value" :class="getConfidenceClass(pageData.confidence_score)">
                {{ ((pageData.confidence_score || 0) * 100).toFixed(0) }}%
              </span>
            </div>
            <div class="info-item">
              <span class="info-label">平台</span>
              <span class="info-value">{{ pageData.platform || '-' }}</span>
            </div>
            <div class="info-item">
              <span class="info-label">创建时间</span>
              <span class="info-value">{{ formatTime(pageData.created_at) }}</span>
            </div>
            <div class="info-item">
              <span class="info-label">更新时间</span>
              <span class="info-value">{{ formatTime(pageData.updated_at) }}</span>
            </div>
          </div>
        </div>
        
        <!-- 统计信息 -->
        <div class="stats-card">
          <h3 class="card-title">元素统计</h3>
          <div class="stats-grid">
            <div class="stat-item" v-for="(count, type) in elementStats" :key="type">
              <span class="stat-type">{{ type }}</span>
              <span class="stat-count">{{ count }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 右侧：元素列表 -->
      <div class="elements-column">
        <div class="elements-header">
          <h3 class="section-title">元素列表</h3>
          <span class="element-count">共 {{ elements.length }} 个元素</span>
        </div>
        
        <div class="elements-list" v-loading="loadingElements">
          <div
            v-for="(element, index) in elements"
            :key="element.id"
            class="element-card"
            :class="{ 'is-selected': selectedElementId === element.id }"
            @click="selectedElementId = element.id"
          >
            <div class="element-header">
              <span class="element-index">{{ index + 1 }}</span>
              <span class="element-name">{{ element.element_name }}</span>
              <el-tag size="small" :type="getElementTypeColor(element.element_type)">
                {{ element.element_type }}
              </el-tag>
              <!-- 导航标识 -->
              <el-tag v-if="element.is_navigation" size="small" type="warning" effect="plain">
                跳转
              </el-tag>
              <!-- 切图缩略图 -->
              <img 
                v-if="element.crop_image_url" 
                :src="element.crop_image_url" 
                class="element-thumbnail"
                @click.stop="viewElementCrop(element)"
              />
              <div class="element-actions">
                <el-button 
                  v-if="(element.bbox && pageData?.screenshot_url) || element.crop_image_url" 
                  size="small" 
                  text 
                  type="primary"
                  @click.stop="viewElementCrop(element)"
                >
                  <el-icon><Picture /></el-icon>
                </el-button>
                <el-button size="small" text @click.stop="openEditElement(element)">
                  <el-icon><Edit /></el-icon>
                </el-button>
                <el-button size="small" text type="danger" @click.stop="deleteElement(element)">
                  <el-icon><Delete /></el-icon>
                </el-button>
              </div>
            </div>
            
            <div class="element-content" v-if="element.text_content">
              <span class="content-label">文字：</span>
              <span class="content-value">{{ element.text_content }}</span>
            </div>
            
            <div class="element-desc" v-if="element.description">
              {{ element.description }}
            </div>
            
            <div class="element-locator" v-if="element.midscene_locator">
              <span class="locator-label">Midscene 定位：</span>
              <code class="locator-value">{{ element.midscene_locator }}</code>
            </div>
            
            <!-- 导航信息 -->
            <div class="element-navigation" v-if="element.is_navigation && element.target_page_name">
              <el-icon><Right /></el-icon>
              <span class="nav-label">跳转到：</span>
              <span class="nav-target">{{ element.target_page_name }}</span>
            </div>
            
            <div class="element-bbox" v-if="element.bbox">
              <span class="bbox-label">位置：</span>
              <span class="bbox-value">
                x: {{ element.bbox[0]?.toFixed(1) }}%, 
                y: {{ element.bbox[1]?.toFixed(1) }}%, 
                w: {{ element.bbox[2]?.toFixed(1) }}%, 
                h: {{ element.bbox[3]?.toFixed(1) }}%
              </span>
            </div>
          </div>
          
          <div v-if="!loadingElements && elements.length === 0" class="empty-state">
            <el-icon :size="48"><Warning /></el-icon>
            <p>该页面暂无元素数据</p>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 截图放大弹窗 -->
    <el-dialog v-model="showScreenshotDialog" title="页面截图" width="auto" class="screenshot-dialog">
      <div class="dialog-screenshot">
        <img :src="pageData?.screenshot_url" />
      </div>
    </el-dialog>
    
    <!-- 元素切图弹窗 -->
    <el-dialog v-model="showCropDialog" :title="cropElement?.element_name" width="auto" class="crop-dialog">
      <div class="dialog-crop" v-if="cropElement">
        <!-- 优先展示真实切图 -->
        <div v-if="cropElement.crop_image_url" class="crop-real">
          <img :src="cropElement.crop_image_url" class="crop-real-image" />
        </div>
        <!-- 没有真实切图时，用 bbox 在原图上标注 -->
        <div v-else-if="pageData?.screenshot_url" class="crop-container" ref="cropContainerRef">
          <img 
            :src="pageData.screenshot_url" 
            class="crop-image"
            @load="handleCropImageLoad"
          />
          <div 
            class="crop-highlight"
            :style="getCropHighlightStyle(cropElement)"
          ></div>
        </div>
        <div class="crop-info">
          <p><strong>元素名称：</strong>{{ cropElement.element_name }}</p>
          <p><strong>元素类型：</strong>{{ cropElement.element_type }}</p>
          <p v-if="cropElement.text_content"><strong>文字内容：</strong>{{ cropElement.text_content }}</p>
          <p v-if="cropElement.description"><strong>描述：</strong>{{ cropElement.description }}</p>
          <p v-if="cropElement.crop_image_url" class="crop-source">
            <el-tag type="success" size="small">真实切图</el-tag>
          </p>
          <p v-else class="crop-source">
            <el-tag type="warning" size="small">AI 估算位置</el-tag>
          </p>
        </div>
      </div>
    </el-dialog>
    
    <!-- 编辑元素弹窗 -->
    <el-dialog v-model="editElementVisible" title="编辑元素" width="520px">
      <el-form :model="editElementForm" label-width="100px">
        <el-form-item label="元素名称">
          <el-input v-model="editElementForm.element_name" />
        </el-form-item>
        <el-form-item label="元素类型">
          <el-select v-model="editElementForm.element_type">
            <el-option label="按钮" value="button" />
            <el-option label="图标按钮" value="icon_button" />
            <el-option label="链接" value="link" />
            <el-option label="标签页" value="tab" />
            <el-option label="输入框" value="text_input" />
            <el-option label="开关" value="switch" />
            <el-option label="卡片" value="card" />
            <el-option label="横幅" value="banner" />
            <el-option label="导航项" value="nav_item" />
            <el-option label="列表项" value="list_item" />
            <el-option label="文本" value="text" />
            <el-option label="图片" value="image" />
          </el-select>
        </el-form-item>
        <el-form-item label="文字内容">
          <el-input v-model="editElementForm.text_content" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="editElementForm.description" type="textarea" :rows="2" />
        </el-form-item>
        <el-form-item label="Midscene定位">
          <el-input v-model="editElementForm.midscene_locator" type="textarea" :rows="2" />
        </el-form-item>
        
        <!-- 导航信息 -->
        <el-divider content-position="left">
          <span class="divider-text">导航信息</span>
        </el-divider>
        <el-form-item label="是否跳转">
          <el-switch 
            v-model="editElementForm.is_navigation" 
            active-text="是" 
            inactive-text="否"
          />
          <span class="form-tip">点击此元素是否会跳转到其他页面</span>
        </el-form-item>
        <el-form-item label="目标页面" v-if="editElementForm.is_navigation">
          <el-input 
            v-model="editElementForm.target_page_name" 
            placeholder="如：转账页、设置页、上一页"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editElementVisible = false">取消</el-button>
        <el-button type="primary" :loading="savingElement" @click="saveElement">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { ArrowLeft, Refresh, Delete, Warning, Picture, ZoomIn, Edit, Right } from '@element-plus/icons-vue'
import { knowledgeApi } from '@/api'

defineOptions({ name: 'PageDetailView' })

const route = useRoute()
const router = useRouter()

// 状态
const pageId = computed(() => route.params.id)
const pageData = ref(null)
const elements = ref([])
const loading = ref(false)
const loadingElements = ref(false)
const selectedElementId = ref(null)

// 弹窗状态
const showScreenshotDialog = ref(false)
const showCropDialog = ref(false)
const cropElement = ref(null)
const cropContainerRef = ref(null)
const editElementVisible = ref(false)
const editElementForm = ref({})
const savingElement = ref(false)

// 颜色
const appColors = {}
const colorPalette = ['#f97316', '#3b82f6', '#10b981', '#8b5cf6', '#ef4444']

function getAppColor(appName) {
  if (!appColors[appName]) {
    const index = Object.keys(appColors).length % colorPalette.length
    appColors[appName] = colorPalette[index]
  }
  return appColors[appName]
}

function getConfidenceClass(score) {
  if (score >= 0.8) return 'confidence-high'
  if (score >= 0.5) return 'confidence-medium'
  return 'confidence-low'
}

function getElementTypeColor(type) {
  const colors = {
    button: 'primary',
    icon_button: 'primary',
    link: 'success',
    tab: 'warning',
    text_input: 'info',
    switch: 'info',
    card: '',
    banner: '',
    nav_item: 'warning',
    list_item: ''
  }
  return colors[type] || ''
}

function formatTime(timeStr) {
  if (!timeStr) return '-'
  return new Date(timeStr).toLocaleString('zh-CN')
}

// 元素类型统计
const elementStats = computed(() => {
  const stats = {}
  elements.value.forEach(el => {
    const type = el.element_type || 'unknown'
    stats[type] = (stats[type] || 0) + 1
  })
  return stats
})

// 加载页面数据
async function loadPageData() {
  loading.value = true
  try {
    // 从列表获取页面数据（因为没有单独的获取详情接口）
    const res = await knowledgeApi.getPages({ limit: 500 })
    const pages = res.data || []
    pageData.value = pages.find(p => String(p.id) === String(pageId.value))
    
    if (!pageData.value) {
      ElMessage.error('页面不存在')
      router.push('/ui/knowledge')
    }
  } catch (e) {
    console.error('加载页面数据失败:', e)
    ElMessage.error('加载页面数据失败')
  } finally {
    loading.value = false
  }
}

// 加载元素列表
async function loadElements() {
  loadingElements.value = true
  try {
    const res = await knowledgeApi.getPageElements(pageId.value, { testable_only: false })
    elements.value = res.data || []
  } catch (e) {
    console.error('加载元素失败:', e)
  } finally {
    loadingElements.value = false
  }
}

// 跳转重新识别
function goToReAnalyze() {
  router.push('/ui/knowledge/new')
}

// 删除页面
async function handleDelete() {
  try {
    await ElMessageBox.confirm(
      `确定要删除页面「${pageData.value?.page_name}」吗？此操作不可恢复。`,
      '删除确认',
      { type: 'warning' }
    )
    
    await knowledgeApi.deletePage(pageId.value)
    ElMessage.success('删除成功')
    router.push('/ui/knowledge')
  } catch (e) {
    if (e !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

// 返回列表
function goBack() {
  router.push('/ui/knowledge')
}

// 截图加载失败
function handleImageError() {
  if (pageData.value) {
    pageData.value.screenshot_url = null
  }
}

// 查看元素切图
function viewElementCrop(element) {
  cropElement.value = element
  showCropDialog.value = true
}

// 获取切图高亮样式
function getCropHighlightStyle(element) {
  if (!element?.bbox || element.bbox.length < 4) return {}
  const [left, top, width, height] = element.bbox
  return {
    left: `${left}%`,
    top: `${top}%`,
    width: `${width}%`,
    height: `${height}%`
  }
}

// 切图图片加载完成
function handleCropImageLoad() {
  // 图片加载完成后可以做一些处理
}

// 编辑元素
function openEditElement(element) {
  editElementForm.value = {
    id: element.id,
    element_name: element.element_name,
    element_type: element.element_type,
    text_content: element.text_content || '',
    description: element.description || '',
    midscene_locator: element.midscene_locator || '',
    is_navigation: element.is_navigation || false,
    target_page_name: element.target_page_name || ''
  }
  editElementVisible.value = true
}

// 保存元素
async function saveElement() {
  savingElement.value = true
  try {
    await knowledgeApi.updateElement(editElementForm.value.id, editElementForm.value)
    ElMessage.success('保存成功')
    editElementVisible.value = false
    loadElements()
  } catch (e) {
    console.error('保存元素失败:', e)
    ElMessage.error('保存失败')
  } finally {
    savingElement.value = false
  }
}

// 删除元素
async function deleteElement(element) {
  try {
    await ElMessageBox.confirm(
      `确定要删除元素「${element.element_name}」吗？`,
      '删除确认',
      { type: 'warning' }
    )
    await knowledgeApi.deleteElement(element.id)
    ElMessage.success('删除成功')
    loadElements()
  } catch (e) {
    if (e !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

onMounted(() => {
  loadPageData()
  loadElements()
})
</script>

<style scoped>
.page-detail {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: #f5f7fa;
}

/* 顶部导航栏 */
.detail-header {
  height: 56px;
  background: white;
  border-bottom: 1px solid #e2e8f0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
  flex-shrink: 0;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.back-btn {
  font-size: 14px;
  color: #64748b;
}

.back-btn:hover {
  color: #3b82f6;
}

.divider {
  width: 1px;
  height: 20px;
  background: #e2e8f0;
}

.page-info {
  display: flex;
  align-items: center;
  gap: 10px;
}

.page-name {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #1e293b;
}

.header-right {
  display: flex;
  gap: 12px;
}

/* 主体内容 */
.detail-body {
  flex: 1;
  display: flex;
  padding: 20px;
  gap: 20px;
  overflow: hidden;
}

/* 左侧信息列 */
.info-column {
  width: 340px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.info-card, .stats-card {
  background: white;
  border-radius: 12px;
  padding: 20px;
}

.card-title {
  font-size: 15px;
  font-weight: 600;
  color: #1e293b;
  margin: 0 0 16px 0;
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
}

.info-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.info-item.full {
  grid-column: span 2;
}

.info-label {
  font-size: 12px;
  color: #94a3b8;
}

.info-value {
  font-size: 14px;
  color: #1e293b;
  margin: 0;
}

.info-value.highlight {
  font-size: 20px;
  font-weight: 600;
  color: #3b82f6;
}

.confidence-high { color: #10b981; font-weight: 600; }
.confidence-medium { color: #f59e0b; font-weight: 600; }
.confidence-low { color: #ef4444; font-weight: 600; }

/* 统计卡片 */
.stats-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  background: #f8fafc;
  border-radius: 6px;
}

.stat-type {
  font-size: 12px;
  color: #64748b;
}

.stat-count {
  font-size: 14px;
  font-weight: 600;
  color: #1e293b;
}

/* 右侧元素列 */
.elements-column {
  flex: 1;
  background: white;
  border-radius: 12px;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.elements-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid #f1f5f9;
}

.section-title {
  font-size: 15px;
  font-weight: 600;
  color: #1e293b;
  margin: 0;
}

.element-count {
  font-size: 13px;
  color: #64748b;
}

.elements-list {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.element-card {
  padding: 16px;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.element-card:hover {
  border-color: #3b82f6;
  background: #f8fafc;
}

.element-card.is-selected {
  border-color: #3b82f6;
  background: #eff6ff;
  box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.2);
}

.element-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 8px;
}

.element-index {
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #e2e8f0;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 600;
  color: #64748b;
}

.element-name {
  flex: 1;
  font-weight: 600;
  color: #1e293b;
}

.element-content, .element-desc, .element-locator, .element-bbox, .element-navigation {
  font-size: 13px;
  color: #64748b;
  margin-bottom: 6px;
}

.element-navigation {
  display: flex;
  align-items: center;
  gap: 4px;
  color: #f59e0b;
  background: #fef3c7;
  padding: 4px 8px;
  border-radius: 4px;
  margin-top: 8px;
}

.element-navigation .el-icon {
  font-size: 14px;
}

.nav-label {
  color: #92400e;
  font-size: 12px;
}

.nav-target {
  color: #b45309;
  font-weight: 500;
}

.content-label, .locator-label, .bbox-label {
  color: #94a3b8;
}

.locator-value {
  color: #3b82f6;
  font-family: monospace;
  font-size: 12px;
  background: #f1f5f9;
  padding: 2px 6px;
  border-radius: 4px;
}

.bbox-value {
  font-family: monospace;
  font-size: 12px;
}

/* 空状态 */
.empty-state {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #94a3b8;
}

.empty-state p {
  margin-top: 12px;
}

/* 截图卡片 */
.screenshot-card {
  background: white;
  border-radius: 12px;
  overflow: hidden;
}

.screenshot-preview {
  position: relative;
  cursor: pointer;
  min-height: 200px;
  max-height: 300px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(180deg, #f1f5f9 0%, #e2e8f0 100%);
}

.screenshot-image {
  width: 100%;
  height: auto;
  max-height: 300px;
  object-fit: contain;
}

.screenshot-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  color: #94a3b8;
}

.screenshot-overlay {
  position: absolute;
  inset: 0;
  background: rgba(0, 0, 0, 0.4);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  color: white;
  opacity: 0;
  transition: opacity 0.2s ease;
}

.screenshot-preview:hover .screenshot-overlay {
  opacity: 1;
}

/* 元素操作按钮 */
.element-actions {
  display: flex;
  gap: 4px;
  margin-left: auto;
  opacity: 0;
  transition: opacity 0.2s ease;
}

.element-card:hover .element-actions {
  opacity: 1;
}

/* 截图弹窗 */
.screenshot-dialog .dialog-screenshot {
  max-height: 80vh;
  overflow: auto;
}

.screenshot-dialog .dialog-screenshot img {
  max-width: 100%;
  height: auto;
}

/* 切图弹窗 */
.crop-dialog .dialog-crop {
  display: flex;
  gap: 20px;
}

.crop-container {
  position: relative;
  max-width: 400px;
  max-height: 600px;
  overflow: hidden;
  border-radius: 8px;
  border: 1px solid #e2e8f0;
}

.crop-image {
  width: 100%;
  height: auto;
}

.crop-highlight {
  position: absolute;
  border: 2px solid #ef4444;
  background: rgba(239, 68, 68, 0.2);
  box-shadow: 0 0 0 2000px rgba(0, 0, 0, 0.4);
  border-radius: 4px;
  pointer-events: none;
}

.crop-info {
  min-width: 200px;
  padding: 16px;
  background: #f8fafc;
  border-radius: 8px;
}

.crop-info p {
  margin: 0 0 8px 0;
  font-size: 14px;
  color: #475569;
}

.crop-info p:last-child {
  margin-bottom: 0;
}

.crop-info strong {
  color: #1e293b;
}

.crop-source {
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid #e2e8f0;
}

/* 真实切图样式 */
.crop-real {
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f8fafc;
  border-radius: 8px;
  padding: 16px;
  min-width: 200px;
  min-height: 100px;
}

.crop-real-image {
  max-width: 400px;
  max-height: 500px;
  border-radius: 4px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

/* 元素卡片中的切图缩略图 */
.element-thumbnail {
  width: 40px;
  height: 40px;
  border-radius: 4px;
  object-fit: cover;
  border: 1px solid #e2e8f0;
  margin-left: auto;
}

/* 编辑表单样式 */
.divider-text {
  font-size: 13px;
  color: #64748b;
}

.form-tip {
  font-size: 12px;
  color: #94a3b8;
  margin-left: 10px;
}
</style>
