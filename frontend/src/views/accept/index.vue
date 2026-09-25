<template>
  <section class="page" data-module="accept">
    <header class="page-head">
      <div>
        <h2>竣工验收管理</h2>
        <p class="page-desc">维护验收单，围绕验收单号、关联施工、验收项目、验收标准做登记、筛选与状态流转。</p>
      </div>
      <div class="page-actions">
        <button class="btn primary" type="button" @click="openCreate">登记验收单</button>
        <button class="btn" type="button" @click="exportRows">导出竣工验收清单</button>
      </div>
    </header>

    <div class="stat-row">
      <article v-for="item in stats" :key="item.label" class="stat-card">
        <span class="stat-label">{{ item.label }}</span>
        <strong class="stat-value">{{ item.value }}</strong>
      </article>
    </div>

    <form class="filter-bar" @submit.prevent="reload">
      <label v-for="field in filterFields" :key="field" class="filter-item">
        <span>{{ field }}</span>
        <input v-model="filters[field]" :placeholder="`按${field}检索`" />
      </label>
      <button class="btn" type="submit">查询</button>
      <button class="btn ghost" type="button" @click="resetFilters">重置条件</button>
    </form>

    <table class="data-table">
      <thead>
        <tr>
          <th v-for="column in columns" :key="column">{{ column }}</th>
          <th>可执行动作</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="row in rows" :key="String(row.id)">
          <td v-for="column in columns" :key="column" :title="cellHint(row, column)">{{ row[column] ?? '—' }}</td>
          <td class="row-actions">
            <button
              v-for="action in actions"
              :key="action"
              class="link"
              type="button"
              @click="runAction(action, row)"
            >
              {{ action }}
            </button>
          </td>
        </tr>
        <tr v-if="!rows.length">
          <td :colspan="columns.length + 1" class="empty-state">暂无竣工验收数据，可先登记验收单</td>
        </tr>
      </tbody>
    </table>

    <footer class="page-foot">
      <span>共 {{ total }} 条竣工验收记录</span>
      <span v-if="errorMessage" class="error-text">{{ errorMessage }}</span>
    </footer>
  </section>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'

import { request } from '@/api/client'

type Row = Record<string, string | number | null | string[]>

// 后端统一判定结果（app/services/accept_judgment.py），前端只展示、不自行判定
type Judgment = {
  材料齐套: string
  项目合格: string
  判定结论: string
  材料缺项: string[]
}

const ENDPOINT = '/api/accept'
const columns = ["验收单号", "关联施工", "验收项目", "验收标准", "验收结论", "验收人员", "验收日期", "验收状态", "材料齐套", "项目合格", "判定结论"]
const actions = ["开始验收", "确认通过", "下发返工"]
const statuses = ["待验收", "验收中", "已通过", "需返工"]
const stats = [{"label": "待验收单据", "value": 0}, {"label": "本月通过数", "value": 0}, {"label": "需返工项数", "value": 0}]

const rows = ref<Row[]>([])
const total = ref(0)
const errorMessage = ref('')
const filters = ref<Record<string, string>>({})
const filterFields = columns.slice(0, 3)

function resetFilters() {
  filters.value = {}
  void reload()
}

// 材料不齐套时在单元格悬停提示缺项，缺项清单同样来自后端判定
function cellHint(row: Row, column: string): string {
  if (column !== '材料齐套') {
    return ''
  }
  const missing = row['材料缺项']
  return Array.isArray(missing) && missing.length > 0 ? `缺少材料：${missing.join('、')}` : ''
}

function exportRows() {
  window.open(`${ENDPOINT}/export`, '_blank')
}

function openCreate() {
  errorMessage.value = '验收单登记入口尚未接入审批流'
}

async function runAction(action: string, row: Row) {
  errorMessage.value = ''
  try {
    const response = await request(`${ENDPOINT}/${row.id}/actions`, {
      method: 'POST',
      body: JSON.stringify({ action }),
    })
    if (!response.ok) {
      throw new Error('竣工验收动作未生效，请稍后重试')
    }
    await reload()
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '竣工验收操作失败'
  }
}

async function reload() {
  errorMessage.value = ''
  const query = new URLSearchParams(filters.value as Record<string, string>).toString()
  try {
    const response = await request(`${ENDPOINT}?${query}`)
    if (!response.ok) {
      throw new Error('验收单列表读取失败')
    }
    const payload = await response.json()
    const items: (Row & { 验收判定?: Judgment })[] = payload.items ?? []
    // 判定结果由后端统一给出，这里只把嵌套的判定字段平铺到行上供表格展示
    rows.value = items.map(({ 验收判定: judgment, ...row }) => ({ ...row, ...judgment }))
    total.value = payload.total ?? rows.value.length
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '竣工验收列表读取失败'
  }
}

onMounted(reload)
</script>
