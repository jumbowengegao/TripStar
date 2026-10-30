<template>
  <div class="hotel-picker">
    <!-- 折叠头 -->
    <div class="picker-header" @click="expanded = !expanded">
      <div class="picker-title">
        <span class="picker-icon">🏨</span>
        <span class="picker-name">{{ t('home.hotelPicker.title') }}</span>
        <span v-if="selected" class="picker-selected-chip">{{ selected.name }}</span>
      </div>
      <span class="picker-toggle">{{ expanded ? '▾' : '▸' }}</span>
    </div>
    <p class="picker-subtitle">{{ t('home.hotelPicker.subtitle') }}</p>

    <div v-if="expanded" class="picker-body">
      <!-- ① 位置选择 -->
      <div class="picker-row">
        <span class="row-label">{{ t('home.hotelPicker.locationLabel') }}</span>
        <div class="mode-tabs">
          <button
            class="mode-tab"
            :class="{ active: mode === 'map' }"
            type="button"
            @click="switchMode('map')"
          >{{ t('home.hotelPicker.modeMap') }}</button>
          <button
            class="mode-tab"
            :class="{ active: mode === 'keyword' }"
            type="button"
            @click="switchMode('keyword')"
          >{{ t('home.hotelPicker.modeKeyword') }}</button>
        </div>
      </div>

      <div v-if="mode === 'keyword'" class="keyword-row">
        <a-input
          v-model:value="keyword"
          size="large"
          class="dark-input"
          :placeholder="t('home.hotelPicker.keywordPlaceholder')"
          @pressEnter="locateByKeyword"
        />
        <button class="locate-btn" type="button" :disabled="locating" @click="locateByKeyword">
          {{ locating ? t('home.hotelPicker.locating') : t('home.hotelPicker.locate') }}
        </button>
      </div>

      <div v-show="mode === 'map'" class="map-wrap">
        <div ref="mapEl" class="map-container"></div>
        <p class="map-hint">{{ t('home.hotelPicker.mapHint') }}</p>
      </div>

      <!-- ② 半径 -->
      <div class="picker-row">
        <span class="row-label">{{ t('home.hotelPicker.radiusLabel') }}</span>
        <div class="radius-row">
          <a-slider
            v-model:value="radius"
            :min="500"
            :max="10000"
            :step="500"
            :tooltip-formatter="radiusFormatter"
            class="radius-slider"
          />
          <span class="radius-value">{{ (radius / 1000).toFixed(1) }} km</span>
        </div>
      </div>

      <!-- ③ 价格范围 -->
      <div class="picker-row">
        <span class="row-label">{{ t('home.hotelPicker.priceLabel') }}</span>
        <div class="price-row">
          <a-input-number
            v-model:value="priceMin"
            :min="0"
            :max="100000"
            :controls="false"
            size="large"
            class="dark-input price-input"
            :placeholder="t('home.hotelPicker.priceMin')"
          />
          <span class="price-sep">—</span>
          <a-input-number
            v-model:value="priceMax"
            :min="0"
            :max="100000"
            :controls="false"
            size="large"
            class="dark-input price-input"
            :placeholder="t('home.hotelPicker.priceMax')"
          />
          <span class="price-unit">{{ t('home.hotelPicker.priceUnit') }}</span>
        </div>
      </div>

      <!-- ④ 排序 -->
      <div class="picker-row">
        <span class="row-label">{{ t('home.hotelPicker.sortLabel') }}</span>
        <div class="sort-tabs">
          <button
            v-for="opt in sortOptions"
            :key="opt.value"
            class="sort-tab"
            :class="{ active: sortMode === opt.value }"
            type="button"
            @click="sortMode = opt.value"
          >{{ opt.label }}</button>
        </div>
      </div>

      <div class="picker-actions">
        <button class="search-btn" type="button" :disabled="searching" @click="handleSearch">
          <span v-if="!searching">{{ t('home.hotelPicker.search') }}</span>
          <span v-else class="searching">{{ t('home.hotelPicker.searching') }}</span>
        </button>
        <button v-if="selected" class="clear-btn" type="button" @click="clearSelection">
          {{ t('home.hotelPicker.clear') }}
        </button>
      </div>

      <p v-if="respMessage" class="resp-message">{{ respMessage }}</p>

      <!-- 候选列表 -->
      <div v-if="candidates.length" class="candidates">
        <div class="candidates-header">
          <span>{{ t('home.hotelPicker.candidatesTitle', { count: candidates.length }) }}</span>
          <button class="auto-btn" type="button" @click="selectCandidate(candidates[0])">
            ⚡ {{ t('home.hotelPicker.autoBest') }}
          </button>
        </div>
        <label
          v-for="(c, i) in candidates"
          :key="c.name + i"
          class="candidate-card"
          :class="{ active: selected?.name === c.name }"
        >
          <input
            type="radio"
            name="hotel-candidate"
            class="candidate-radio"
            :checked="selected?.name === c.name"
            @change="selectCandidate(c)"
          />
          <div class="candidate-main">
            <div class="candidate-name">{{ c.name }}</div>
            <div class="candidate-meta">
              <span class="meta-type">{{ c.hotel_type || accommodationType }}</span>
              <span class="meta-rating" :class="{ unavailable: !c.rating_available }">
                {{ c.rating_available ? `⭐ ${c.rating}` : t('home.hotelPicker.ratingUnavailable') }}
              </span>
              <span v-if="c.estimated_cost" class="meta-price">¥{{ c.estimated_cost }}/{{ t('home.hotelPicker.perNight') }}</span>
              <span v-if="c.distance_m != null" class="meta-distance">{{ formatDistance(c.distance_m) }}</span>
            </div>
            <div class="candidate-address">{{ c.address }}</div>
          </div>
          <div class="candidate-score">
            <span class="score-value">{{ (c.total_score * 100).toFixed(0) }}</span>
            <span class="score-label">{{ t('home.hotelPicker.scoreLabel') }}</span>
          </div>
        </label>
      </div>

      <div v-else-if="searched && !candidates.length" class="empty-hint">
        {{ t('home.hotelPicker.emptyHint') }}
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { message } from 'ant-design-vue'
import AMapLoader from '@amap/amap-jsapi-loader'
import { getRuntimeMapJsKey } from '@/services/api'
import { searchHotelCandidates } from '@/services/api'
import type { HotelCandidate, HotelSelection, HotelSortMode } from '@/types'

const props = defineProps<{
  city: string
  accommodationType: string
}>()

const emit = defineEmits<{
  (e: 'selection-change', selection: HotelSelection | null): void
}>()

const { t } = useI18n()

const expanded = ref(false)
const mode = ref<'map' | 'keyword'>('map')
const keyword = ref('')
const locating = ref(false)
const radius = ref(3000)
const priceMin = ref<number | null>(null)
const priceMax = ref<number | null>(null)
const sortMode = ref<HotelSortMode>('cost_perf')
const searching = ref(false)
const searched = ref(false)
const candidates = ref<HotelCandidate[]>([])
const respMessage = ref('')
const selected = ref<HotelCandidate | null>(null)
const center = ref<{ longitude: number; latitude: number; name: string } | null>(null)

const sortOptions = computed(() => [
  { value: 'cost_perf' as HotelSortMode, label: t('home.hotelPicker.sortCostPerf') },
  { value: 'rating' as HotelSortMode, label: t('home.hotelPicker.sortRating') },
  { value: 'price' as HotelSortMode, label: t('home.hotelPicker.sortPrice') },
])

// ============ 地图选点（懒加载 AMap JS API） ============
const mapEl = ref<HTMLDivElement | null>(null)
let AMapNS: any = null
let mapInstance: any = null
let marker: any = null
let circle: any = null
let mapLoading = false

const CENTER = { lng: 116.397128, lat: 39.916527 } // 默认北京中心

const switchMode = async (m: 'map' | 'keyword') => {
  mode.value = m
  if (m === 'map') {
    await nextTick()
    await initMap()
  }
}

watch(expanded, async (open) => {
  if (open && mode.value === 'map') {
    await nextTick()
    await initMap()
  }
})

const initMap = async () => {
  if (mapInstance || mapLoading || !mapEl.value) return
  const mapJsKey = getRuntimeMapJsKey()
  if (!mapJsKey) {
    message.warning(t('home.hotelPicker.needJsKey'))
    return
  }
  mapLoading = true
  try {
    AMapNS = await AMapLoader.load({
      key: mapJsKey,
      version: '2.0',
      plugins: ['AMap.PlaceSearch', 'AMap.Geocoder'],
    })
    mapInstance = new AMapNS.Map(mapEl.value, {
      zoom: 12,
      center: [CENTER.lng, CENTER.lat],
      mapStyle: 'amap://styles/darkblue',
    })
    mapInstance.on('click', (e: any) => {
      setCenter(e.lnglat.getLng(), e.lnglat.getLat(), t('home.hotelPicker.mapPickedName'), false)
    })
  } catch (err) {
    console.error('住宿选点地图加载失败:', err)
    message.error(t('home.hotelPicker.mapLoadFailed'))
  } finally {
    mapLoading = false
  }
}

const setCenter = (lng: number, lat: number, name: string, fitView: boolean = true) => {
  center.value = { longitude: lng, latitude: lat, name }
  drawCenterOverlay(lng, lat)
  if (fitView && mapInstance) {
    mapInstance.setZoomAndCenter(13, [lng, lat])
  }
}

const drawCenterOverlay = (lng: number, lat: number) => {
  if (!mapInstance || !AMapNS) return
  if (marker) marker.setMap(null)
  if (circle) circle.setMap(null)
  marker = new AMapNS.Marker({
    position: [lng, lat],
    map: mapInstance,
  })
  circle = new AMapNS.Circle({
    center: [lng, lat],
    radius: radius.value,
    map: mapInstance,
    strokeColor: '#FFB347',
    strokeWeight: 2,
    strokeOpacity: 0.8,
    fillColor: '#FFB347',
    fillOpacity: 0.12,
  })
}

watch(radius, () => {
  if (circle && center) {
    circle.setRadius(radius.value)
  }
})

// 关键词选点：用高德 PlaceSearch 搜索 POI
const locateByKeyword = async () => {
  const kw = keyword.value.trim()
  if (!kw) {
    message.warning(t('home.hotelPicker.keywordRequired'))
    return
  }
  if (!props.city.trim()) {
    message.warning(t('home.hotelPicker.cityRequired'))
    return
  }
  locating.value = true
  try {
    await initMap()
    if (!AMapNS) return
    const placeSearch = new AMapNS.PlaceSearch({ city: props.city.trim(), citylimit: true })
    placeSearch.search(kw, (status: string, result: any) => {
      locating.value = false
      if (status === 'complete' && result?.poiList?.pois?.length) {
        const poi = result.poiList.pois[0]
        const lng = poi.location.getLng()
        const lat = poi.location.getLat()
        mode.value = 'map'
        nextTick().then(async () => {
          await initMap()
          setCenter(lng, lat, poi.name)
        })
      } else {
        message.error(t('home.hotelPicker.keywordNotFound', { kw }))
      }
    })
  } catch (err) {
    locating.value = false
    console.error('关键词选点失败:', err)
    message.error(t('home.hotelPicker.mapLoadFailed'))
  }
}

// ============ 搜索候选 ============
const handleSearch = async () => {
  if (!center.value) {
    message.warning(t('home.hotelPicker.centerRequired'))
    return
  }
  if (!props.city.trim()) {
    message.warning(t('home.hotelPicker.cityRequired'))
    return
  }
  if (priceMin.value != null && priceMax.value != null && priceMin.value > priceMax.value) {
    message.warning(t('home.hotelPicker.priceReversed'))
    return
  }
  searching.value = true
  respMessage.value = ''
  try {
    const resp = await searchHotelCandidates({
      city: props.city.trim(),
      keywords: center.value.name,
      location: { longitude: center.value.longitude, latitude: center.value.latitude },
      radius: radius.value,
      accommodation_type: props.accommodationType,
      price_min: priceMin.value,
      price_max: priceMax.value,
      sort_mode: sortMode.value,
      limit: 8,
    })
    searched.value = true
    candidates.value = resp.candidates || []
    respMessage.value = resp.message || ''
    if (!candidates.value.length) {
      message.warning(t('home.hotelPicker.emptyHint'))
    }
  } catch (err: any) {
    searched.value = true
    message.error(err.message || t('home.hotelPicker.searchFailed'))
  } finally {
    searching.value = false
  }
}

const selectCandidate = (c: HotelCandidate | null) => {
  selected.value = c
  if (!c) {
    emit('selection-change', null)
    return
  }
  const selection: HotelSelection = {
    name: c.name,
    address: c.address || '',
    location: c.location || null,
    type: c.hotel_type || props.accommodationType,
    rating: c.rating != null ? String(c.rating) : '',
    estimated_cost: c.estimated_cost || 0,
  }
  emit('selection-change', selection)
}

const clearSelection = () => {
  selected.value = null
  emit('selection-change', null)
}

const formatDistance = (m: number) => {
  return m >= 1000 ? `${(m / 1000).toFixed(1)} km` : `${m} m`
}

const radiusFormatter = (v: number) => `${(v / 1000).toFixed(1)} km`

onBeforeUnmount(() => {
  if (mapInstance) {
    mapInstance.destroy?.()
    mapInstance = null
  }
})
</script>

<style scoped>
/* ===== 住宿定制选择器（暗黑玻璃风格，与首页一致） ===== */
.hotel-picker {
  margin-top: 4px;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 16px;
  padding: 18px 20px;
}

.picker-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  cursor: pointer;
  user-select: none;
}

.picker-title {
  display: flex;
  align-items: center;
  gap: 8px;
}

.picker-icon {
  font-size: 16px;
}

.picker-name {
  font-size: 14px;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.85);
}

.picker-selected-chip {
  font-size: 12px;
  color: #FFD699;
  background: rgba(255, 179, 71, 0.12);
  border: 1px solid rgba(255, 179, 71, 0.3);
  padding: 2px 10px;
  border-radius: 12px;
  max-width: 260px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.picker-toggle {
  color: rgba(255, 255, 255, 0.4);
  font-size: 14px;
}

.picker-subtitle {
  margin: 8px 0 0;
  font-size: 12px;
  color: rgba(255, 255, 255, 0.35);
}

.picker-body {
  margin-top: 16px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.picker-row {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.row-label {
  font-size: 12px;
  font-weight: 500;
  color: rgba(255, 255, 255, 0.5);
  letter-spacing: 0.04em;
}

/* 模式切换 */
.mode-tabs,
.sort-tabs {
  display: inline-flex;
  gap: 8px;
}

.mode-tab,
.sort-tab {
  border: 1px solid rgba(255, 255, 255, 0.1);
  background: rgba(255, 255, 255, 0.04);
  color: rgba(255, 255, 255, 0.6);
  border-radius: 10px;
  padding: 8px 16px;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.25s ease;
  font-family: inherit;
}

.mode-tab:hover,
.sort-tab:hover {
  border-color: rgba(255, 179, 71, 0.35);
}

.mode-tab.active,
.sort-tab.active {
  border-color: #FFB347;
  background: rgba(255, 179, 71, 0.12);
  color: #FFD699;
}

/* 关键词行 */
.keyword-row {
  display: flex;
  gap: 10px;
}

.keyword-row .dark-input {
  flex: 1;
}

.locate-btn {
  border: none;
  border-radius: 12px;
  padding: 0 20px;
  font-size: 14px;
  font-weight: 600;
  color: white;
  background: linear-gradient(135deg, #FFB347, #FF6B6B);
  cursor: pointer;
  font-family: inherit;
  transition: opacity 0.25s ease;
}

.locate-btn:disabled {
  opacity: 0.5;
  cursor: wait;
}

/* 地图 */
.map-wrap {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.map-container {
  width: 100%;
  height: 260px;
  border-radius: 12px;
  overflow: hidden;
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.map-hint {
  margin: 0;
  font-size: 12px;
  color: rgba(255, 255, 255, 0.35);
}

/* 半径 */
.radius-row {
  display: flex;
  align-items: center;
  gap: 16px;
}

.radius-slider {
  flex: 1;
}

.radius-value {
  font-size: 13px;
  color: #FFD699;
  font-weight: 600;
  min-width: 56px;
  text-align: right;
}

/* 价格 */
.price-row {
  display: flex;
  align-items: center;
  gap: 10px;
}

.price-input {
  width: 130px !important;
}

.price-sep {
  color: rgba(255, 255, 255, 0.35);
}

.price-unit {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.35);
}

/* 操作按钮 */
.picker-actions {
  display: flex;
  gap: 10px;
}

.search-btn {
  flex: 1;
  height: 44px;
  border: none;
  border-radius: 12px;
  font-size: 15px;
  font-weight: 600;
  color: white;
  background: linear-gradient(135deg, #FFB347 0%, #FF6B6B 60%, #C084FC 100%);
  cursor: pointer;
  font-family: inherit;
  transition: transform 0.25s ease, box-shadow 0.25s ease;
}

.search-btn:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 8px 24px rgba(255, 107, 107, 0.35);
}

.search-btn:disabled {
  opacity: 0.6;
  cursor: wait;
}

.clear-btn {
  height: 44px;
  border: 1px solid rgba(255, 255, 255, 0.15);
  border-radius: 12px;
  padding: 0 18px;
  background: transparent;
  color: rgba(255, 255, 255, 0.6);
  cursor: pointer;
  font-size: 13px;
  font-family: inherit;
}

.clear-btn:hover {
  border-color: rgba(255, 107, 107, 0.5);
  color: #FF6B6B;
}

.resp-message {
  margin: 0;
  font-size: 12px;
  color: rgba(255, 213, 153, 0.75);
}

/* 候选列表 */
.candidates {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.candidates-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 13px;
  color: rgba(255, 255, 255, 0.65);
}

.auto-btn {
  border: 1px solid rgba(255, 179, 71, 0.35);
  background: rgba(255, 179, 71, 0.08);
  color: #FFD699;
  border-radius: 10px;
  padding: 6px 14px;
  font-size: 12px;
  cursor: pointer;
  font-family: inherit;
  transition: all 0.25s ease;
}

.auto-btn:hover {
  background: rgba(255, 179, 71, 0.18);
}

.candidate-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 16px;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 14px;
  cursor: pointer;
  transition: all 0.25s ease;
}

.candidate-card:hover {
  border-color: rgba(255, 179, 71, 0.35);
  transform: translateY(-1px);
}

.candidate-card.active {
  border-color: #FFB347;
  background: rgba(255, 179, 71, 0.1);
}

.candidate-radio {
  accent-color: #FFB347;
  width: 16px;
  height: 16px;
  flex-shrink: 0;
}

.candidate-main {
  flex: 1;
  min-width: 0;
}

.candidate-name {
  font-size: 14px;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.88);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.candidate-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 6px;
  font-size: 12px;
}

.meta-type {
  color: #C084FC;
}

.meta-rating {
  color: #FFD699;
}

.meta-rating.unavailable {
  color: rgba(255, 255, 255, 0.3);
}

.meta-price {
  color: #7BE0C3;
  font-weight: 600;
}

.meta-distance {
  color: rgba(255, 255, 255, 0.45);
}

.candidate-address {
  margin-top: 4px;
  font-size: 12px;
  color: rgba(255, 255, 255, 0.35);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.candidate-score {
  display: flex;
  flex-direction: column;
  align-items: center;
  flex-shrink: 0;
}

.score-value {
  font-size: 20px;
  font-weight: 800;
  background: linear-gradient(135deg, #FFB347, #FF6B6B);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.score-label {
  font-size: 10px;
  color: rgba(255, 255, 255, 0.35);
}

.empty-hint {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.4);
  text-align: center;
  padding: 12px 0;
}

/* 复用暗色输入 */
.dark-input.ant-input,
.dark-input.ant-input-number {
  background: rgba(255, 255, 255, 0.06) !important;
  border: 1px solid rgba(255, 255, 255, 0.1) !important;
  border-radius: 12px !important;
  color: rgba(255, 255, 255, 0.9) !important;
}

.dark-input.ant-input::placeholder,
.dark-input.ant-input-number::placeholder {
  color: rgba(255, 255, 255, 0.25) !important;
}

:deep(.ant-input-number-input) {
  color: rgba(255, 255, 255, 0.9) !important;
}

:deep(.ant-input-number-input::placeholder) {
  color: rgba(255, 255, 255, 0.25) !important;
}

:deep(.ant-slider-track) {
  background: linear-gradient(90deg, #FFB347, #FF6B6B) !important;
}

:deep(.ant-slider-handle::after) {
  box-shadow: 0 0 0 3px rgba(255, 179, 71, 0.25) !important;
}
</style>
