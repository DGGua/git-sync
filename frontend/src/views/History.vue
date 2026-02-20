<template>
  <div class="container">
    <!-- Toast Notification -->
    <div v-if="toast.show" :class="['toast', `toast-${toast.type}`]">
      {{ toast.message }}
    </div>

    <div class="page-header">
      <h1 class="page-title">Sync History</h1>
      <button class="btn btn-danger" @click="handleClearHistory" :disabled="history.length === 0">
        Clear History
      </button>
    </div>

    <!-- Statistics Cards -->
    <div class="stats-grid">
      <div class="stat-card">
        <div class="stat-value">{{ stats.total }}</div>
        <div class="stat-label">Total Syncs</div>
      </div>
      <div class="stat-card stat-success">
        <div class="stat-value">{{ stats.successful }}</div>
        <div class="stat-label">Successful</div>
      </div>
      <div class="stat-card stat-error">
        <div class="stat-value">{{ stats.failed }}</div>
        <div class="stat-label">Failed</div>
      </div>
    </div>

    <div v-if="loading" class="loading">Loading...</div>

    <div v-else-if="history.length === 0" class="empty-state card">
      <div class="empty-state-icon">📋</div>
      <p>No sync history yet</p>
      <router-link to="/repositories" class="btn btn-primary">
        Go to Repositories
      </router-link>
    </div>

    <div v-else class="history-list">
      <div v-for="record in history" :key="record.id" class="history-item" :class="{ 'history-failed': !record.success }">
        <div class="history-icon">
          <span v-if="record.success">✅</span>
          <span v-else>❌</span>
        </div>
        <div class="history-info">
          <div class="history-header">
            <span class="history-repo">{{ record.repository }}</span>
            <span :class="['history-status', record.success ? 'status-success' : 'status-failed']">
              {{ record.success ? 'Success' : 'Failed' }}
            </span>
          </div>
          <div class="history-details">
            <span class="history-time">{{ formatTime(record.timestamp) }}</span>
            <span class="history-branches" v-if="record.branches_synced?.length">
              {{ record.branches_synced.length }} branches
            </span>
            <span class="history-tags" v-if="record.tags_synced">
              {{ record.tags_synced }} tags
            </span>
            <span class="history-duration">{{ record.duration.toFixed(1) }}s</span>
          </div>
          <div class="history-message" v-if="!record.success && record.error">
            {{ record.error }}
          </div>
        </div>
        <div class="history-actions">
          <button class="btn btn-sm btn-secondary" @click="handleDeleteRecord(record.id)">
            Delete
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'

const loading = ref(false)
const history = ref([])
const stats = ref({ total: 0, successful: 0, failed: 0, repositories: {} })

const toast = reactive({
  show: false,
  message: '',
  type: 'success'
})

function showToast(message, type = 'success') {
  toast.message = message
  toast.type = type
  toast.show = true
  setTimeout(() => {
    toast.show = false
  }, 3000)
}

function formatTime(timestamp) {
  const date = new Date(timestamp)
  return date.toLocaleString()
}

async function fetchHistory() {
  loading.value = true
  try {
    const response = await fetch('/api/history')
    history.value = await response.json()
  } catch (e) {
    showToast('Failed to load history', 'error')
  } finally {
    loading.value = false
  }
}

async function fetchStats() {
  try {
    const response = await fetch('/api/history/stats')
    stats.value = await response.json()
  } catch (e) {
    console.error('Failed to load stats', e)
  }
}

async function handleDeleteRecord(id) {
  if (!confirm('Are you sure you want to delete this record?')) return

  try {
    const response = await fetch(`/api/history/${id}`, { method: 'DELETE' })
    if (response.ok) {
      history.value = history.value.filter(r => r.id !== id)
      fetchStats()
      showToast('Record deleted', 'success')
    }
  } catch (e) {
    showToast('Failed to delete record', 'error')
  }
}

async function handleClearHistory() {
  if (!confirm('Are you sure you want to clear all history?')) return

  try {
    const response = await fetch('/api/history', { method: 'DELETE' })
    if (response.ok) {
      const data = await response.json()
      history.value = []
      stats.value = { total: 0, successful: 0, failed: 0, repositories: {} }
      showToast(data.message, 'success')
    }
  } catch (e) {
    showToast('Failed to clear history', 'error')
  }
}

onMounted(() => {
  fetchHistory()
  fetchStats()
})
</script>

<style scoped>
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
}

.page-title {
  font-size: 1.75rem;
  font-weight: 700;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.stat-card {
  background: var(--card-bg);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  padding: 1.5rem;
  text-align: center;
}

.stat-value {
  font-size: 2rem;
  font-weight: 700;
  color: var(--text-color);
}

.stat-label {
  color: var(--text-muted);
  font-size: 0.875rem;
  margin-top: 0.25rem;
}

.stat-success .stat-value {
  color: #10b981;
}

.stat-error .stat-value {
  color: #ef4444;
}

.history-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.history-item {
  display: flex;
  align-items: flex-start;
  gap: 1rem;
  padding: 1rem 1.5rem;
  background: var(--card-bg);
  border: 1px solid var(--border-color);
  border-radius: 8px;
}

.history-failed {
  border-left: 3px solid #ef4444;
}

.history-icon {
  font-size: 1.25rem;
  padding-top: 0.25rem;
}

.history-info {
  flex: 1;
}

.history-header {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 0.25rem;
}

.history-repo {
  font-weight: 600;
  font-size: 1rem;
}

.history-status {
  font-size: 0.75rem;
  padding: 0.125rem 0.5rem;
  border-radius: 4px;
}

.status-success {
  background: rgba(16, 185, 129, 0.1);
  color: #10b981;
}

.status-failed {
  background: rgba(239, 68, 68, 0.1);
  color: #ef4444;
}

.history-details {
  display: flex;
  gap: 1rem;
  color: var(--text-muted);
  font-size: 0.875rem;
}

.history-message {
  margin-top: 0.5rem;
  color: #ef4444;
  font-size: 0.875rem;
}

.history-actions {
  display: flex;
  gap: 0.5rem;
}

/* Toast styles */
.toast {
  position: fixed;
  top: 20px;
  right: 20px;
  padding: 12px 24px;
  border-radius: 8px;
  color: white;
  font-weight: 500;
  z-index: 2000;
  animation: slideIn 0.3s ease-out;
}

.toast-success {
  background-color: #10b981;
}

.toast-error {
  background-color: #ef4444;
}

@keyframes slideIn {
  from {
    transform: translateX(100%);
    opacity: 0;
  }
  to {
    transform: translateX(0);
    opacity: 1;
  }
}

@media (max-width: 640px) {
  .stats-grid {
    grid-template-columns: 1fr;
  }

  .history-details {
    flex-wrap: wrap;
    gap: 0.5rem;
  }
}
</style>
