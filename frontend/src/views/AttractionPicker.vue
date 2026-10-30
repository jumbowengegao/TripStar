<template>
  <div class="picker-page">
    <!-- 步骤指示 -->
    <div class="steps-bar">
      <button class="step-chip done" type="button" @click="goBack">✓ {{ t('home.attractionPicker.stepInfo') }}</button>
      <span class="step-sep">→</span>
      <span class="step-chip" :class="{ active: stage === 'attractions' }">2 {{ t('home.attractionPicker.stepAttractions') }}</span>
      <span class="step-sep">→</span>
      <span class="step-chip" :class="{ active: stage === 'hotel' }">3 {{ t('home.attractionPicker.stepHotel') }}</span>
      <span class="step-sep">→</span>
      <span class="step-chip">4 {{ t('home.attractionPicker.stepGenerate') }}</span>
    </div>

    <!-- 上下文信息条 -->
    <div class="context-bar">
      <span class="ctx-chip">{{ formData.city }}</span>
      <span class="ctx-chip">{{ formData.start_date }} · {{ formData.travel_days }} {{ t('home.travelDaysUnit') }}</span>
      <span v-if="formData.preferences.length" class="ctx-chip">{{ t('home.attractionPicker.preferences') }}: {{ formData.preferences.join(' · ') }}</span>
    </div>

    <!-- ============ Stage 2: 选择景点 ============ -->
    <div v-if="stage === 'attractions'" class="stage-body">
      <!-- 左：区域分组列表 -->
      <div class="list-panel">
        <div v-if="loading" class="state-hint">
          <div class="spinner"></div>
          {{ t('home.attractionPicker.loading') }}
        </div>
        <div v-else-if="loadError" class="state-hint error">
          {{ loadError }}
          <button class="retry-btn" type="button" @click="loadAttractions">{{ t('home.attractionPicker.retry') }}</button>
        </div>
        <div v-else-if="!regionGroups.length" class="state-hint">{{ t('home.attractionPicker.emptyHint') }}</div>

        <template v-else>
          <div v-for="group in regionGroups" :key="group.region" class="region-block">
            <div class="region-head">
              <span class="region-marker"></span>
              <span class="region-name">{{ group.region }}</span>
              <span class="region-count">{{ t('home.attractionPicker.regionCount', { n: group.attractions.length }) }}</span>
              <button class="region-all-btn" type="button" @click="toggleRegion(group)">
                {{ isRegionAllSelected(group) ? t('home.attractionPicker.deselectAll') : t('home.attractionPicker.selectAllRegion') }}
              </button>
            </div>
            <div
              v-for="a in group.attractions"
              :key="a.name"
              class="attraction-card"
              :class="{ selected: isSelected(a.name) }"
              @click="toggleAttraction(a)"
            >
              <span class="check-box" :class="{ checked: isSelected(a.name) }">{{ isSelected(a.name) ? '✓' : '' }}</span>
              <div class="attraction-main">
                <div class="attraction-name">
                  {{ a.name }}
                  <span v-if="a.rating" class="attraction-rating">⭐ {{ a.rating }}</span>
                </div>
                <div class="attraction-meta">
                  <span v-if="a.duration">{{ t('home.attractionPicker.durationMin', { n: a.duration }) }}</span>
                  <span v-if="a.mention_count">{{ t('home.attractionPicker.mentions', { n: a.mention_count }) }}</span>
                  <span v-if="a.reservation_required" class="reservation-tag">{{ t('home.attractionPicker.needReservation') }}</span>
                </div>
                <div v-if="a.reason" class="attraction-reason">{{ a.reason }}</div>
                <div v-if="a.reservation_required && a.reservation_tips" class="attraction-res-tips">{{ a.reservation_tips }}</div>
              </div>
            </div>
          </div>
        </template>
      </div>

      <!-- 右：地图 + 操作 -->
      <div class="map-panel">
        <div class="map-box">
          <div class="map-head">
            <span>{{ t('home.attractionPicker.mapTitle') }}</span>
            <span class="map-provider">AMap</span>
          </div>
          <div ref="mapEl" class="map-container"></div>
          <div class="map-legend">
            <span class="legend-item on">● {{ t('home.attractionPicker.legendSelected', { n: selectedCount }) }}</span>
            <span class="legend-item off">○ {{ t('home.attractionPicker.legendUnselected', { n: totalCount - selectedCount }) }}</span>
          </div>
        </div>

        <div class="action-bar">
          <div class="selected-text">
            {{ t('home.attractionPicker.selectedCount', { s: selectedCount, t: totalCount }) }}
          </div>
          <div class="action-btns">
            <button
              class="plan-btn"
              type="button"
              :disabled="!selectedCount || planning"
              @click="openPlanner"
            >
              🗓 {{ t('home.attractionPicker.planTrip') }}
              <span v-if="dailyPlan.length" class="plan-badge">{{ t('home.attractionPicker.planBadge', { n: dailyPlan.length }) }}</span>
            </button>
            <button
              class="next-btn"
              type="button"
              :disabled="!selectedCount"
              @click="goHotelStage"
            >{{ t('home.attractionPicker.nextHotel') }} →</button>
          </div>
          <div class="plan-hint">{{ t('home.attractionPicker.planHint') }}</div>
        </div>
      </div>
    </div>

    <!-- ============ Stage 3: 选择住宿 ============ -->
    <div v-else class="stage-body hotel-stage">
      <div class="hotel-wrap">
        <HotelPicker
          :city="formData.city"
          :accommodation-type="formData.accommodation"
          @selection-change="onHotelSelectionChange"
        />
        <div class="action-bar hotel-action">
          <button class="back-btn" type="button" @click="stage = 'attractions'">← {{ t('home.attractionPicker.backToAttractions') }}</button>
          <button
            class="next-btn"
            type="button"
            :disabled="planning"
            @click="handleGenerate"
          >{{ planning ? t('home.attractionPicker.generating') : t('home.attractionPicker.generateTrip') }} →</button>
        </div>
      </div>
    </div>

    <!-- 每日规划弹窗 -->
    <DailyPlanner
      v-model:visible="plannerVisible"
      :days="formData.travel_days"
      :attractions="selectedAttractionOptions"
      @save="onDailyPlanSave"
    />

    <!-- 生成进度遮罩 -->
    <Teleport to="body">
      <div v-if="planning" class="loading-mask">
        <div class="loading-card">
          <div class="loading-plan-code" v-if="planCode">{{ planCode }}</div>
          <div class="progress-track">
            <div class="progress-fill" :style="{ width: loadingProgress + '%' }"></div>
          </div>
          <div class="loading-status">{{ loadingStatus }}</div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { message } from 'ant-design-vue'
import AMapLoader from '@amap/amap-jsapi-loader'
import { fetchAttractionCandidates, generateTripPlan, getRuntimeMapJsKey } from '@/services/api'
import { getCurrentLocale } from '@/i18n'
import HotelPicker from '@/components/HotelPicker.vue'
import DailyPlanner from '@/components/DailyPlanner.vue'
import type {
  AttractionOption,
  AttractionRegionGroup,
  DayPlanAssignment,
  HotelSelection,
  SelectedAttraction,
  TripFormData,
  TripTaskEvent,
} from '@/types'

const router = useRouter()
const { t } = useI18n()

const STORE_KEY = 'tripFormData'

// ============ 表单数据（来自第一步 Landing） ============
const formData = reactive<TripFormData>({
  city: '',
  cities: [],
  start_date: '',
  end_date: '',
  travel_days: 1,
  transportation: '公共交通',
  accommodation: '经济型酒店',
  preferences: [],
  free_text_input: '',
  language: 'zh',
})

const stage = ref<'attractions' | 'hotel'>('attractions')

// ============ 景点候选 ============
const loading = ref(false)
const loadError = ref('')
const regionGroups = ref<AttractionRegionGroup[]>([])

const allAttractions = computed<AttractionOption[]>(() =>
  regionGroups.value.flatMap(g => g.attractions)
)
const totalCount = computed(() => allAttractions.value.length)

const selectedNames = ref<Set<string>>(new Set())
const selectedCount = computed(() => selectedNames.value.size)
const isSelected = (name: string) => selectedNames.value.has(name)

const selectedAttractionOptions = computed<AttractionOption[]>(() =>
  allAttractions.value.filter(a => selectedNames.value.has(a.name))
)

const loadAttractions = async () => {
  if (!formData.city.trim()) {
    message.error(t('home.attractionPicker.missingCity'))
    router.replace('/')
    return
  }
  loading.value = true
  loadError.value = ''
  try {
    const resp = await fetchAttractionCandidates({
      city: formData.city.trim(),
      preferences: formData.preferences || [],
      language: getCurrentLocale(),
      limit: 18,
    })
    regionGroups.value = resp.regions || []
    if (resp.message) message.info(resp.message)
    if (!regionGroups.value.length) {
      loadError.value = resp.message || t('home.attractionPicker.emptyHint')
    }
    await nextTick()
    renderMarkers()
  } catch (err: any) {
    loadError.value = err.message || t('api.searchAttractionsFailed')
  } finally {
    loading.value = false
  }
}

const toggleAttraction = (a: AttractionOption) => {
  const next = new Set(selectedNames.value)
  if (next.has(a.name)) next.delete(a.name)
  else next.add(a.name)
  selectedNames.value = next
  renderMarkers()
}

const isRegionAllSelected = (group: AttractionRegionGroup) =>
  group.attractions.every(a => selectedNames.value.has(a.name))

const toggleRegion = (group: AttractionRegionGroup) => {
  const next = new Set(selectedNames.value)
  if (isRegionAllSelected(group)) {
    group.attractions.forEach(a => next.delete(a.name))
  } else {
    group.attractions.forEach(a => next.add(a.name))
  }
  selectedNames.value = next
  renderMarkers()
}

// ============ 地图 ============
const mapEl = ref<HTMLDivElement | null>(null)
let AMapNS: any = null
let mapInstance: any = null
const markers: any[] = []
let mapLoading = false

const initMap = async () => {
  if (mapInstance || mapLoading || !mapEl.value) return
  const mapJsKey = getRuntimeMapJsKey()
  if (!mapJsKey) {
    message.warning(t('home.attractionPicker.needJsKey'))
    return
  }
  mapLoading = true
  try {
    AMapNS = await AMapLoader.load({ key: mapJsKey, version: '2.0', plugins: [] })
    mapInstance = new AMapNS.Map(mapEl.value, {
      zoom: 11,
      center: [108.94, 34.34],
      mapStyle: 'amap://styles/darkblue',
    })
  } catch (err) {
    console.error('景点地图加载失败:', err)
    message.error(t('home.attractionPicker.mapLoadFailed'))
  } finally {
    mapLoading = false
  }
}

const clearMarkers = () => {
  for (const m of markers) m.setMap(null)
  markers.length = 0
}

const renderMarkers = () => {
  if (!mapInstance || !AMapNS) return
  clearMarkers()
  const points: [number, number][] = []
  for (const a of allAttractions.value) {
    if (!a.location) continue
    const selected = selectedNames.value.has(a.name)
    points.push([a.location.longitude, a.location.latitude])
    const marker = new AMapNS.Marker({
      position: [a.location.longitude, a.location.latitude],
      map: mapInstance,
      content:
        `<div style="width:24px;height:24px;border-radius:50%;` +
        (selected
          ? `background:#ffb347;border:2px solid #0d1321;color:#1a1305;`
          : `background:#1a2438;border:1.5px solid rgba(255,255,255,0.35);color:#7d8aa5;`) +
        `text-align:center;line-height:20px;font-size:11px;font-weight:600;cursor:pointer;">${selected ? '●' : ''}</div>`,
      title: a.name,
    })
    marker.on('click', () => toggleAttraction(a))
    markers.push(marker)
  }
  if (points.length && mapInstance) {
    mapInstance.setFitView(markers, false, [40, 40, 40, 40])
  }
}

// ============ 每日规划弹窗 ============
const plannerVisible = ref(false)
const dailyPlan = ref<DayPlanAssignment[]>([])

const openPlanner = () => {
  plannerVisible.value = true
}

const onDailyPlanSave = (plan: DayPlanAssignment[]) => {
  dailyPlan.value = plan
  if (plan.length) message.success(t('home.dailyPlanner.saved'))
}

// ============ 住宿选择（第三步） ============
const hotelSelection = ref<HotelSelection | null>(null)

const onHotelSelectionChange = (selection: HotelSelection | null) => {
  hotelSelection.value = selection
}

const goHotelStage = () => {
  stage.value = 'hotel'
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

// ============ 生成行程 ============
const planning = ref(false)
const loadingProgress = ref(0)
const loadingStatus = ref('')
const planCode = ref('')

const getStageStatusText = (stageStr: string) => {
  if (stageStr === 'attraction_search') return t('home.loading.searchingAttractions')
  if (stageStr === 'weather_search') return t('home.loading.queryingWeather')
  if (stageStr === 'hotel_search') return t('home.loading.recommendingHotels')
  if (stageStr === 'planning') return t('home.loading.generatingPlan')
  if (stageStr === 'graph_building') return t('home.loading.generatingPlan')
  if (stageStr === 'completed') return t('home.loading.done')
  return t('home.loading.initializing')
}

const handleGenerate = async () => {
  planning.value = true
  loadingProgress.value = 5
  loadingStatus.value = t('home.loading.initializing')
  planCode.value = ''

  try {
    sessionStorage.removeItem('tripPlan')
    sessionStorage.removeItem('graphData')
    sessionStorage.removeItem('planId')

    const selected_attractions: SelectedAttraction[] = selectedAttractionOptions.value.map(a => ({
      name: a.name,
      name_zh: a.name_zh,
      name_en: a.name_en,
      location: a.location || null,
      duration: a.duration ?? null,
      reason: a.reason || '',
      reservation_required: a.reservation_required,
      reservation_tips: a.reservation_tips || '',
      region: a.region || '',
    }))

    const requestData: TripFormData = {
      ...formData,
      hotel_selection: hotelSelection.value,
      selected_attractions,
      daily_plan: dailyPlan.value.length ? dailyPlan.value : null,
      language: getCurrentLocale(),
    }

    const response = await generateTripPlan(requestData, {
      onTaskCreated: (task) => {
        planCode.value = task.plan_id || task.task_id
        loadingProgress.value = 5
        loadingStatus.value = t('home.loading.initializing')
      },
      onTaskEvent: (event: TripTaskEvent) => {
        if (event.plan_id) planCode.value = event.plan_id
        if (Number.isFinite(event.progress)) {
          loadingProgress.value = Math.max(0, Math.min(100, event.progress))
        }
        loadingStatus.value = event.message || getStageStatusText(event.stage)
      },
    })

    loadingProgress.value = 100
    loadingStatus.value = t('home.loading.done')

    if (response.success && response.data) {
      const planId = response.plan_id || planCode.value
      sessionStorage.setItem('tripPlan', JSON.stringify(response.data))
      if (response.graph_data) sessionStorage.setItem('graphData', JSON.stringify(response.graph_data))
      if (planId) sessionStorage.setItem('planId', planId)
      message.success(t('home.messages.generateSuccess'))
      sessionStorage.removeItem(STORE_KEY)
      setTimeout(() => {
        if (planId) router.push({ path: '/result', query: { plan_id: planId } })
        else router.push('/result')
      }, 500)
    } else {
      message.error(response.message || t('home.messages.generateFailed'))
    }
  } catch (error: any) {
    sessionStorage.removeItem('tripPlan')
    sessionStorage.removeItem('graphData')
    sessionStorage.removeItem('planId')
    message.error(error.message || t('home.messages.generateRetry'))
  } finally {
    setTimeout(() => {
      planning.value = false
      loadingProgress.value = 0
      loadingStatus.value = ''
    }, 800)
  }
}

const goBack = () => router.push('/')

onMounted(async () => {
  const raw = sessionStorage.getItem(STORE_KEY)
  if (!raw) {
    message.warning(t('home.attractionPicker.missingForm'))
    router.replace('/')
    return
  }
  try {
    const saved = JSON.parse(raw) as TripFormData
    Object.assign(formData, saved)
  } catch {
    message.warning(t('home.attractionPicker.missingForm'))
    router.replace('/')
    return
  }
  await initMap()
  await loadAttractions()
})

onBeforeUnmount(() => {
  if (mapInstance) {
    mapInstance.destroy?.()
    mapInstance = null
  }
})
</script>

<style scoped>
.picker-page {
  min-height: 100vh;
  background: linear-gradient(180deg, #0d171d 0%, #142430 58%, #0f1a22 100%);
  color: #ecf3fa;
  padding: 24px clamp(16px, 4vw, 48px) 40px;
  box-sizing: border-box;
}

/* 步骤条 */
.steps-bar {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
  margin-bottom: 14px;
}

.step-chip {
  font-size: 12px;
  color: rgba(236, 243, 250, 0.45);
  border: 1px solid rgba(236, 243, 250, 0.14);
  border-radius: 14px;
  padding: 5px 14px;
  background: rgba(236, 243, 250, 0.03);
  font-family: inherit;
}

.step-chip.active {
  color: #ffd699;
  border-color: #ffb347;
  background: rgba(255, 179, 71, 0.1);
}

.step-chip.done {
  color: #7be0c3;
  border-color: rgba(123, 224, 195, 0.4);
  cursor: pointer;
}

.step-sep {
  color: rgba(236, 243, 250, 0.25);
  font-size: 12px;
}

/* 上下文条 */
.context-bar {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  margin-bottom: 18px;
}

.ctx-chip {
  font-size: 11px;
  color: rgba(236, 243, 250, 0.55);
  border: 1px solid rgba(236, 243, 250, 0.12);
  border-radius: 12px;
  padding: 3px 12px;
}

/* 主体布局 */
.stage-body {
  display: flex;
  gap: 16px;
  align-items: flex-start;
}

.list-panel {
  flex: 1.2;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.map-panel {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 12px;
  position: sticky;
  top: 20px;
}

/* 状态提示 */
.state-hint {
  border: 1px dashed rgba(236, 243, 250, 0.16);
  border-radius: 14px;
  padding: 40px 20px;
  text-align: center;
  font-size: 13px;
  color: rgba(236, 243, 250, 0.45);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
}

.state-hint.error {
  color: #ff9a9a;
}

.spinner {
  width: 26px;
  height: 26px;
  border: 3px solid rgba(255, 179, 71, 0.2);
  border-top-color: #ffb347;
  border-radius: 50%;
  animation: spin 0.9s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.retry-btn {
  border: 1px solid rgba(255, 179, 71, 0.4);
  background: rgba(255, 179, 71, 0.08);
  color: #ffd699;
  border-radius: 10px;
  padding: 6px 18px;
  font-size: 12px;
  cursor: pointer;
  font-family: inherit;
}

/* 区域分组 */
.region-block {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.region-head {
  display: flex;
  align-items: center;
  gap: 8px;
}

.region-marker {
  width: 3px;
  height: 13px;
  background: #ffb347;
  border-radius: 2px;
}

.region-name {
  font-size: 14px;
  font-weight: 500;
  color: #ffd699;
}

.region-count {
  font-size: 11px;
  color: rgba(236, 243, 250, 0.4);
}

.region-all-btn {
  margin-left: auto;
  font-size: 11px;
  color: rgba(236, 243, 250, 0.55);
  border: 1px solid rgba(236, 243, 250, 0.16);
  border-radius: 12px;
  padding: 2px 12px;
  background: transparent;
  cursor: pointer;
  font-family: inherit;
  transition: border-color 0.2s ease;
}

.region-all-btn:hover {
  border-color: rgba(255, 179, 71, 0.5);
}

/* 景点卡片 */
.attraction-card {
  display: flex;
  gap: 10px;
  align-items: flex-start;
  background: rgba(236, 243, 250, 0.04);
  border: 1px solid rgba(236, 243, 250, 0.1);
  border-radius: 12px;
  padding: 10px 14px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.attraction-card:hover {
  border-color: rgba(255, 179, 71, 0.4);
}

.attraction-card.selected {
  background: rgba(255, 179, 71, 0.1);
  border-color: #ffb347;
}

.check-box {
  width: 17px;
  height: 17px;
  border-radius: 5px;
  border: 1px solid rgba(236, 243, 250, 0.28);
  flex-shrink: 0;
  margin-top: 2px;
  text-align: center;
  line-height: 15px;
  font-size: 11px;
  color: #1a1305;
}

.check-box.checked {
  background: #ffb347;
  border-color: #ffb347;
}

.attraction-main {
  flex: 1;
  min-width: 0;
}

.attraction-name {
  font-size: 14px;
  font-weight: 500;
}

.attraction-rating {
  font-size: 12px;
  color: #ffd699;
  margin-left: 6px;
  font-weight: 400;
}

.attraction-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 3px;
  font-size: 11px;
  color: rgba(236, 243, 250, 0.45);
}

.reservation-tag {
  color: #f0a35c;
}

.attraction-reason {
  margin-top: 4px;
  font-size: 11px;
  color: rgba(236, 243, 250, 0.38);
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.attraction-res-tips {
  margin-top: 3px;
  font-size: 11px;
  color: #f0a35c;
}

/* 地图 */
.map-box {
  background: rgba(236, 243, 250, 0.04);
  border: 1px solid rgba(236, 243, 250, 0.1);
  border-radius: 14px;
  padding: 12px;
}

.map-head {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  color: rgba(236, 243, 250, 0.55);
  margin-bottom: 8px;
}

.map-provider {
  color: rgba(236, 243, 250, 0.3);
}

.map-container {
  width: 100%;
  height: 420px;
  border-radius: 10px;
  overflow: hidden;
  border: 1px solid rgba(236, 243, 250, 0.1);
}

.map-legend {
  display: flex;
  gap: 14px;
  margin-top: 8px;
  font-size: 11px;
}

.legend-item.on {
  color: #ffd699;
}

.legend-item.off {
  color: rgba(236, 243, 250, 0.35);
}

/* 操作栏 */
.action-bar {
  background: rgba(236, 243, 250, 0.05);
  border: 1px solid rgba(236, 243, 250, 0.12);
  border-radius: 14px;
  padding: 12px 14px;
}

.selected-text {
  font-size: 13px;
  margin-bottom: 10px;
}

.action-btns {
  display: flex;
  gap: 10px;
}

.plan-btn {
  flex: 1;
  border: 1.5px solid #c084fc;
  background: rgba(192, 132, 252, 0.1);
  border-radius: 12px;
  padding: 10px 0;
  font-size: 14px;
  font-weight: 500;
  color: #e3ccfa;
  cursor: pointer;
  font-family: inherit;
  position: relative;
}

.plan-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.plan-badge {
  position: absolute;
  top: -8px;
  right: 10px;
  background: #c084fc;
  color: #1a0f2a;
  font-size: 10px;
  border-radius: 9px;
  padding: 1px 8px;
}

.next-btn {
  flex: 1;
  border: none;
  border-radius: 12px;
  padding: 10px 0;
  font-size: 14px;
  font-weight: 500;
  color: white;
  background: linear-gradient(135deg, #ffb347 0%, #ff6b6b 60%, #c084fc 100%);
  cursor: pointer;
  font-family: inherit;
}

.next-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.plan-hint {
  margin-top: 8px;
  font-size: 10px;
  color: rgba(236, 243, 250, 0.35);
  text-align: center;
}

/* 第三步住宿 */
.hotel-stage {
  display: block;
}

.hotel-wrap {
  max-width: 860px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.hotel-action {
  display: flex;
  gap: 12px;
}

.back-btn {
  border: 1px solid rgba(236, 243, 250, 0.16);
  border-radius: 12px;
  background: transparent;
  padding: 10px 22px;
  font-size: 13px;
  color: rgba(236, 243, 250, 0.6);
  cursor: pointer;
  font-family: inherit;
}

.back-btn:hover {
  border-color: rgba(255, 179, 71, 0.5);
}

.hotel-action .next-btn {
  flex: 1;
}

/* 生成进度遮罩 */
.loading-mask {
  position: fixed;
  inset: 0;
  z-index: 1200;
  background: rgba(6, 12, 22, 0.85);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
}

.loading-card {
  width: 100%;
  max-width: 460px;
  background: #141d2f;
  border: 1px solid rgba(255, 255, 255, 0.14);
  border-radius: 16px;
  padding: 26px 28px;
  text-align: center;
}

.loading-plan-code {
  font-size: 11px;
  color: rgba(236, 243, 250, 0.4);
  margin-bottom: 14px;
}

.progress-track {
  width: 100%;
  height: 8px;
  border-radius: 6px;
  background: rgba(236, 243, 250, 0.08);
  overflow: hidden;
  margin-bottom: 14px;
}

.progress-fill {
  height: 100%;
  border-radius: 6px;
  background: linear-gradient(90deg, #ffb347, #ff6b6b);
  transition: width 0.4s ease;
}

.loading-status {
  font-size: 13px;
  color: rgba(236, 243, 250, 0.7);
}

/* 窄屏适配 */
@media (max-width: 900px) {
  .stage-body {
    flex-direction: column;
  }

  .map-panel {
    position: static;
    width: 100%;
  }

  .map-container {
    height: 300px;
  }
}
</style>
