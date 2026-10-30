<template>
  <Teleport to="body">
    <div v-if="visible" class="dp-mask" @click.self="handleClose">
      <div class="dp-modal">
        <div class="dp-header">
          <span class="dp-title">{{ t('home.dailyPlanner.title') }}</span>
          <button class="dp-close" type="button" @click="handleClose">×</button>
        </div>
        <p class="dp-subtitle">{{ t('home.dailyPlanner.subtitle') }}</p>

        <!-- 天标签 -->
        <div class="dp-day-tabs">
          <button
            v-for="d in days"
            :key="d"
            class="dp-day-tab"
            :class="{ active: activeDay === d }"
            type="button"
            @click="activeDay = d"
          >
            <span class="dp-day-name">{{ t('home.dailyPlanner.dayN', { n: d }) }}</span>
            <span class="dp-day-count">
              {{ (assignments[d]?.length || 0) > 0 ? t('home.dailyPlanner.plannedCount', { n: assignments[d].length }) : t('home.dailyPlanner.unplanned') }}
            </span>
          </button>
        </div>

        <div class="dp-body">
          <!-- 左：待分配池 -->
          <div class="dp-pool">
            <div class="dp-col-label">{{ t('home.dailyPlanner.poolTitle') }}</div>
            <div v-if="poolItems.length === 0" class="dp-pool-empty">{{ t('home.dailyPlanner.poolEmpty') }}</div>
            <div
              v-for="item in poolItems"
              :key="item.name"
              class="dp-pool-item"
              @click="addToDay(item.name)"
            >
              <span class="dp-pool-name">{{ item.name }}</span>
              <span class="dp-pool-add">+</span>
            </div>
            <p class="dp-pool-hint">{{ t('home.dailyPlanner.poolHint') }}</p>
          </div>

          <!-- 右：当天顺序 -->
          <div class="dp-order">
            <div class="dp-col-label">{{ t('home.dailyPlanner.orderTitle', { n: activeDay }) }}</div>
            <div v-if="currentOrder.length === 0" class="dp-order-empty">{{ t('home.dailyPlanner.orderEmpty') }}</div>
            <div
              v-for="(name, idx) in currentOrder"
              :key="name"
              class="dp-order-item"
            >
              <span class="dp-order-badge">{{ idx + 1 }}</span>
              <span class="dp-order-name">
                {{ name }}
                <span v-if="metaOf(name)" class="dp-order-meta">{{ metaOf(name) }}</span>
              </span>
              <span class="dp-order-actions">
                <button class="dp-act" type="button" :disabled="idx === 0" @click="move(idx, -1)">↑</button>
                <button class="dp-act" type="button" :disabled="idx === currentOrder.length - 1" @click="move(idx, 1)">↓</button>
                <button class="dp-act dp-act-remove" type="button" @click="removeFromDay(idx)">×</button>
              </span>
            </div>
            <button
              v-if="currentOrder.length >= 2"
              class="dp-auto-btn"
              type="button"
              @click="autoArrange"
            >⚡ {{ t('home.dailyPlanner.autoArrange') }}</button>
          </div>
        </div>

        <div class="dp-footer">
          <span class="dp-progress">{{ t('home.dailyPlanner.progress', { done: plannedDays, total: days }) }}</span>
          <button class="dp-skip" type="button" @click="skip">{{ t('home.dailyPlanner.skip') }}</button>
          <button class="dp-save" type="button" @click="save">{{ t('home.dailyPlanner.save') }}</button>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { message } from 'ant-design-vue'
import type { AttractionOption, DayPlanAssignment } from '@/types'

const props = defineProps<{
  visible: boolean
  days: number
  attractions: AttractionOption[]
}>()

const emit = defineEmits<{
  (e: 'update:visible', v: boolean): void
  (e: 'save', plan: DayPlanAssignment[]): void
}>()

const { t } = useI18n()

const activeDay = ref(1)
// day -> 有序景点名数组
const assignments = ref<Record<number, string[]>>({})

const daysList = computed(() => Array.from({ length: Math.max(props.days, 1) }, (_, i) => i + 1))

const plannedDays = computed(() =>
  daysList.value.filter(d => (assignments.value[d]?.length || 0) > 0).length
)

const poolItems = computed(() => {
  const assigned = new Set<string>()
  for (const d of daysList.value) {
    for (const name of assignments.value[d] || []) assigned.add(name)
  }
  return props.attractions.filter(a => !assigned.has(a.name))
})

const currentOrder = computed(() => assignments.value[activeDay.value] || [])

const metaOf = (name: string) => {
  const a = props.attractions.find(x => x.name === name)
  if (!a) return ''
  const parts: string[] = []
  if (a.duration) parts.push(t('home.attractionPicker.durationMin', { n: a.duration }))
  if (a.reservation_required) parts.push(t('home.attractionPicker.needReservation'))
  return parts.join(' · ')
}

watch(
  () => props.visible,
  (open) => {
    if (open) {
      // 重新打开时保留已有分配；清理越界的天
      const clean: Record<number, string[]> = {}
      for (const d of daysList.value) {
        clean[d] = assignments.value[d] || []
      }
      assignments.value = clean
      activeDay.value = 1
    }
  }
)

const addToDay = (name: string) => {
  if (!assignments.value[activeDay.value]) assignments.value[activeDay.value] = []
  if (assignments.value[activeDay.value].includes(name)) return
  assignments.value[activeDay.value].push(name)
}

const removeFromDay = (idx: number) => {
  assignments.value[activeDay.value].splice(idx, 1)
}

const move = (idx: number, dir: -1 | 1) => {
  const arr = assignments.value[activeDay.value]
  const target = idx + dir
  if (target < 0 || target >= arr.length) return
  const [item] = arr.splice(idx, 1)
  arr.splice(target, 0, item)
}

/** 就近排序：从第一个景点出发的最近邻贪心 */
const autoArrange = () => {
  const arr = assignments.value[activeDay.value]
  if (arr.length < 2) return
  const locOf = (name: string) =>
    props.attractions.find(a => a.name === name)?.location || null
  const dist = (a: { longitude: number; latitude: number }, b: { longitude: number; latitude: number }) => {
    const dx = a.longitude - b.longitude
    const dy = a.latitude - b.latitude
    return dx * dx + dy * dy
  }
  const rest = [...arr]
  const ordered: string[] = [rest.shift()!]
  while (rest.length) {
    const cur = locOf(ordered[ordered.length - 1])
    let bestIdx = 0
    let bestDist = Infinity
    rest.forEach((name, i) => {
      const loc = locOf(name)
      const d = cur && loc ? dist(cur, loc) : i
      if (d < bestDist) {
        bestDist = d
        bestIdx = i
      }
    })
    ordered.push(rest.splice(bestIdx, 1)[0])
  }
  assignments.value[activeDay.value] = ordered
  message.success(t('home.dailyPlanner.autoArranged'))
}

const handleClose = () => emit('update:visible', false)

const skip = () => {
  assignments.value = {}
  emit('save', [])
  emit('update:visible', false)
}

const save = () => {
  const plan: DayPlanAssignment[] = daysList.value
    .map(d => ({ day: d, attraction_names: assignments.value[d] || [] }))
    .filter(p => p.attraction_names.length > 0)
  emit('save', plan)
  emit('update:visible', false)
}
</script>

<style scoped>
.dp-mask {
  position: fixed;
  inset: 0;
  z-index: 1100;
  background: rgba(6, 12, 22, 0.72);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
}

.dp-modal {
  width: 100%;
  max-width: 640px;
  max-height: 88vh;
  overflow-y: auto;
  background: #141d2f;
  border: 1px solid rgba(255, 255, 255, 0.14);
  border-radius: 16px;
  padding: 20px 22px;
  color: #e8ecf4;
}

.dp-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.dp-title {
  font-size: 16px;
  font-weight: 500;
}

.dp-close {
  border: none;
  background: transparent;
  color: rgba(255, 255, 255, 0.4);
  font-size: 20px;
  cursor: pointer;
  line-height: 1;
}

.dp-subtitle {
  margin: 4px 0 14px;
  font-size: 12px;
  color: rgba(255, 255, 255, 0.4);
}

.dp-day-tabs {
  display: flex;
  gap: 8px;
  margin-bottom: 14px;
  flex-wrap: wrap;
}

.dp-day-tab {
  border: 1px solid rgba(255, 255, 255, 0.12);
  background: rgba(255, 255, 255, 0.04);
  border-radius: 10px;
  padding: 6px 14px;
  cursor: pointer;
  display: flex;
  flex-direction: column;
  gap: 1px;
  font-family: inherit;
  min-width: 84px;
}

.dp-day-tab.active {
  border-color: #ffb347;
  background: rgba(255, 179, 71, 0.12);
}

.dp-day-name {
  font-size: 12px;
  font-weight: 500;
  color: rgba(255, 255, 255, 0.75);
}

.dp-day-tab.active .dp-day-name {
  color: #ffd699;
}

.dp-day-count {
  font-size: 10px;
  color: rgba(255, 255, 255, 0.35);
}

.dp-body {
  display: flex;
  gap: 14px;
}

.dp-pool {
  flex: 1;
}

.dp-order {
  flex: 1.4;
}

.dp-col-label {
  font-size: 11px;
  color: rgba(255, 255, 255, 0.45);
  margin-bottom: 8px;
}

.dp-pool-empty,
.dp-order-empty {
  border: 1px dashed rgba(255, 255, 255, 0.14);
  border-radius: 9px;
  padding: 12px 10px;
  text-align: center;
  font-size: 11px;
  color: rgba(255, 255, 255, 0.35);
}

.dp-pool-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.10);
  border-radius: 9px;
  padding: 7px 10px;
  margin-bottom: 6px;
  cursor: pointer;
  transition: border-color 0.2s ease;
}

.dp-pool-item:hover {
  border-color: rgba(123, 224, 195, 0.4);
}

.dp-pool-name {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.7);
}

.dp-pool-add {
  font-size: 13px;
  color: #7be0c3;
}

.dp-pool-hint {
  margin: 8px 0 0;
  font-size: 10px;
  color: rgba(255, 255, 255, 0.3);
  line-height: 1.6;
}

.dp-order-item {
  display: flex;
  align-items: center;
  gap: 8px;
  background: rgba(255, 179, 71, 0.10);
  border: 1px solid rgba(255, 179, 71, 0.5);
  border-radius: 9px;
  padding: 7px 10px;
  margin-bottom: 6px;
}

.dp-order-badge {
  width: 22px;
  height: 22px;
  border-radius: 50%;
  background: #ffb347;
  color: #1a1305;
  font-size: 11px;
  font-weight: 500;
  text-align: center;
  line-height: 22px;
  flex-shrink: 0;
}

.dp-order-name {
  flex: 1;
  font-size: 12px;
  font-weight: 500;
  min-width: 0;
}

.dp-order-meta {
  font-size: 10px;
  font-weight: 400;
  color: rgba(255, 255, 255, 0.4);
  margin-left: 4px;
}

.dp-order-actions {
  display: flex;
  gap: 3px;
  flex-shrink: 0;
}

.dp-act {
  width: 18px;
  height: 18px;
  border: none;
  border-radius: 4px;
  background: rgba(255, 255, 255, 0.08);
  color: rgba(255, 255, 255, 0.6);
  font-size: 10px;
  cursor: pointer;
  line-height: 1;
}

.dp-act:disabled {
  opacity: 0.3;
  cursor: default;
}

.dp-act-remove {
  color: #ff8a8a;
}

.dp-auto-btn {
  margin-top: 8px;
  width: 100%;
  border: 1px dashed rgba(192, 132, 252, 0.4);
  border-radius: 9px;
  background: transparent;
  padding: 6px 10px;
  font-size: 11px;
  color: #c084fc;
  cursor: pointer;
  font-family: inherit;
}

.dp-footer {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 16px;
}

.dp-progress {
  flex: 1;
  font-size: 11px;
  color: rgba(255, 255, 255, 0.4);
}

.dp-skip {
  border: 1px solid rgba(255, 255, 255, 0.16);
  border-radius: 10px;
  background: transparent;
  padding: 7px 14px;
  font-size: 12px;
  color: rgba(255, 255, 255, 0.6);
  cursor: pointer;
  font-family: inherit;
}

.dp-save {
  border: none;
  border-radius: 10px;
  background: linear-gradient(135deg, #ffb347, #ff6b6b);
  padding: 7px 16px;
  font-size: 12px;
  font-weight: 500;
  color: white;
  cursor: pointer;
  font-family: inherit;
}
</style>
