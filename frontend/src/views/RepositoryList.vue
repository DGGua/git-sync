<template>
  <div class="container">
    <!-- Toast Notification -->
    <div v-if="toast.show" :class="['toast', `toast-${toast.type}`]">
      {{ toast.message }}
    </div>

    <div class="page-header">
      <h1 class="page-title">Repositories</h1>
      <router-link to="/repositories/new" class="btn btn-primary">
        Add Repository
      </router-link>
    </div>

    <div class="card">
      <p class="help-text">Drag and drop to reorder repositories</p>
    </div>

    <div v-if="repoStore.loading" class="loading">Loading...</div>

    <div v-else-if="repoStore.repositories.length === 0" class="empty-state card">
      <div class="empty-state-icon">📁</div>
      <p>No repositories configured</p>
      <router-link to="/repositories/new" class="btn btn-primary">
        Add Your First Repository
      </router-link>
    </div>

    <draggable
      v-else
      :list="repositories"
      item-key="name"
      handle=".drag-handle"
      ghost-class="dragging"
      @end="onDragEnd"
    >
      <template #item="{ element: repo }">
        <div class="repo-item" :class="{ 'repo-syncing': syncingRepo === repo.name }">
          <div class="repo-drag-area">
            <span class="drag-handle">⋮⋮</span>
          </div>
          <div class="repo-info">
            <span class="repo-name">{{ repo.name }}</span>
            <span class="repo-url">{{ repo.source.url }} → {{ repo.target.url }}</span>
          </div>
          <div class="repo-meta">
            <span :class="['badge', repo.enabled ? 'badge-success' : 'badge-warning']">
              {{ repo.enabled ? 'Enabled' : 'Disabled' }}
            </span>
            <span v-if="repo.sync_tags" class="badge badge-success">Tags</span>
            <span v-if="syncingRepo === repo.name" class="badge badge-info">
              Syncing...
            </span>
          </div>
          <div class="repo-actions">
            <button
              class="btn btn-sm btn-primary"
              @click="handleSync(repo.name)"
              :disabled="syncStore.syncing"
            >
              {{ syncingRepo === repo.name ? 'Syncing...' : 'Sync' }}
            </button>
            <router-link :to="`/repositories/${repo.name}`" class="btn btn-sm btn-secondary">
              Edit
            </router-link>
            <button class="btn btn-sm btn-danger" @click="handleDelete(repo.name)">
              Delete
            </button>
          </div>
        </div>
      </template>
    </draggable>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, watch } from 'vue'
import draggable from 'vuedraggable'
import { useRepositoryStore, useSyncStore } from '@/stores'

const repoStore = useRepositoryStore()
const syncStore = useSyncStore()

const repositories = ref([])
const syncingRepo = ref(null)

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

// Sync local ref with store
watch(() => repoStore.repositories, (newRepos) => {
  repositories.value = [...newRepos].sort((a, b) => a.order - b.order)
}, { immediate: true })

onMounted(() => {
  repoStore.fetchRepositories()
})

async function onDragEnd() {
  const orderedNames = repositories.value.map(r => r.name)
  await repoStore.reorderRepositories(orderedNames)
}

async function handleSync(name) {
  syncingRepo.value = name
  try {
    const result = await syncStore.runSingleSync(name, false)
    if (result.success) {
      showToast(`Sync completed for ${name}`, 'success')
    } else {
      showToast(`Sync failed: ${result.message}`, 'error')
    }
  } catch (e) {
    showToast(`Sync failed: ${e.message}`, 'error')
  } finally {
    syncingRepo.value = null
  }
}

async function handleDelete(name) {
  if (confirm(`Are you sure you want to delete "${name}"?`)) {
    await repoStore.deleteRepository(name)
    showToast(`Repository "${name}" deleted`, 'success')
  }
}
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

.help-text {
  color: var(--text-muted);
  font-size: 0.875rem;
  margin-bottom: 1rem;
}

.repo-drag-area {
  padding-right: 1rem;
}

.drag-handle {
  cursor: grab;
  color: var(--text-muted);
  font-size: 1.25rem;
  user-select: none;
}

.drag-handle:hover {
  color: var(--text-color);
}

.repo-meta {
  display: flex;
  gap: 0.5rem;
  margin-left: auto;
  margin-right: 1rem;
}

.repo-syncing {
  background-color: rgba(59, 130, 246, 0.1);
}

.badge-info {
  background-color: #3b82f6;
  color: white;
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
</style>
