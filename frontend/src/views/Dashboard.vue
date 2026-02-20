<template>
  <div class="container">
    <h1 class="page-title">Dashboard</h1>

    <div class="stats-grid">
      <div class="stat-card">
        <div class="stat-value">{{ repoStore.repositories.length }}</div>
        <div class="stat-label">Repositories</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">{{ enabledCount }}</div>
        <div class="stat-label">Enabled</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">{{ keyStore.keys.length }}</div>
        <div class="stat-label">SSH Keys</div>
      </div>
    </div>

    <div class="card">
      <div class="card-header">
        <h2 class="card-title">Quick Actions</h2>
      </div>
      <div class="actions-grid">
        <button
          class="btn btn-primary"
          @click="handleSyncAll"
          :disabled="syncStore.syncing"
        >
          {{ syncStore.syncing ? 'Syncing...' : 'Sync All' }}
        </button>
        <button
          class="btn btn-secondary"
          @click="handleDryRun"
          :disabled="syncStore.syncing"
        >
          Dry Run
        </button>
        <router-link to="/repositories/new" class="btn btn-primary">
          Add Repository
        </router-link>
      </div>
    </div>

    <div class="card" v-if="syncStore.syncResults">
      <div class="card-header">
        <h2 class="card-title">Last Sync Results</h2>
      </div>
      <div class="sync-results">
        <div
          v-for="result in syncStore.syncResults.results"
          :key="result.repository"
          class="sync-result-item"
        >
          <span :class="['status-badge', result.success ? 'success' : 'failed']">
            {{ result.success ? '✓' : '✗' }}
          </span>
          <span class="repo-name">{{ result.repository }}</span>
          <span class="message">{{ result.message }}</span>
        </div>
      </div>
    </div>

    <div class="card">
      <div class="card-header">
        <h2 class="card-title">Recent Repositories</h2>
        <router-link to="/repositories" class="btn btn-sm btn-secondary">
          View All
        </router-link>
      </div>
      <div v-if="repoStore.loading" class="loading">Loading...</div>
      <div v-else-if="repoStore.repositories.length === 0" class="empty-state">
        <div class="empty-state-icon">📁</div>
        <p>No repositories configured</p>
        <router-link to="/repositories/new" class="btn btn-primary">
          Add Your First Repository
        </router-link>
      </div>
      <ul v-else class="repo-list">
        <li
          v-for="repo in recentRepos"
          :key="repo.name"
          class="repo-item"
        >
          <div class="repo-info">
            <span class="repo-name">{{ repo.name }}</span>
            <span :class="['badge', repo.enabled ? 'badge-success' : 'badge-warning']">
              {{ repo.enabled ? 'Enabled' : 'Disabled' }}
            </span>
          </div>
          <div class="repo-actions">
            <button
              class="btn btn-sm btn-primary"
              @click="handleSyncOne(repo.name)"
              :disabled="syncStore.syncing"
            >
              Sync
            </button>
            <router-link :to="`/repositories/${repo.name}`" class="btn btn-sm btn-secondary">
              Edit
            </router-link>
          </div>
        </li>
      </ul>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted } from 'vue'
import { useRepositoryStore, useKeyStore, useSyncStore } from '@/stores'

const repoStore = useRepositoryStore()
const keyStore = useKeyStore()
const syncStore = useSyncStore()

const enabledCount = computed(() =>
  repoStore.repositories.filter(r => r.enabled).length
)

const recentRepos = computed(() =>
  [...repoStore.repositories].slice(0, 5)
)

onMounted(() => {
  repoStore.fetchRepositories()
  keyStore.fetchKeys()
})

async function handleSyncAll() {
  try {
    await syncStore.runSync(null, false)
  } catch (e) {
    console.error('Sync failed:', e)
  }
}

async function handleDryRun() {
  try {
    await syncStore.runSync(null, true)
  } catch (e) {
    console.error('Dry run failed:', e)
  }
}

async function handleSyncOne(name) {
  try {
    await syncStore.runSingleSync(name, false)
    alert(`Sync completed for ${name}`)
  } catch (e) {
    console.error('Sync failed:', e)
  }
}
</script>

<style scoped>
.page-title {
  font-size: 1.75rem;
  font-weight: 700;
  margin-bottom: 1.5rem;
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
  color: var(--primary-color);
}

.stat-label {
  color: var(--text-muted);
  font-size: 0.875rem;
  margin-top: 0.25rem;
}

.actions-grid {
  display: flex;
  gap: 1rem;
}

.sync-results {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.sync-result-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.5rem;
  background: var(--bg-color);
  border-radius: 4px;
}

.status-badge {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.75rem;
}

.status-badge.success {
  background: rgba(34, 197, 94, 0.1);
  color: var(--success-color);
}

.status-badge.failed {
  background: rgba(239, 68, 68, 0.1);
  color: var(--danger-color);
}

.message {
  color: var(--text-muted);
  font-size: 0.875rem;
  margin-left: auto;
}

@media (max-width: 768px) {
  .stats-grid {
    grid-template-columns: 1fr;
  }
}
</style>
