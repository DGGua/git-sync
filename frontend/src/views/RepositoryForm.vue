<template>
  <div class="container">
    <div class="page-header">
      <h1 class="page-title">{{ isEdit ? 'Edit Repository' : 'New Repository' }}</h1>
      <router-link to="/repositories" class="btn btn-secondary">
        Back to List
      </router-link>
    </div>

    <div v-if="loading" class="loading">Loading...</div>

    <form v-else @submit.prevent="handleSubmit" class="card form-card">
      <div v-if="error" class="alert alert-danger">{{ error }}</div>

      <div class="form-section">
        <h3 class="section-title">Basic Information</h3>

        <div class="form-group">
          <label class="form-label">Repository Name *</label>
          <input
            v-model="form.name"
            type="text"
            class="form-input"
            placeholder="my-repo"
            :disabled="isEdit"
            required
          />
          <p class="form-help">Unique identifier for this repository</p>
        </div>

        <div class="form-group">
          <label class="form-checkbox">
            <input v-model="form.enabled" type="checkbox" />
            <span>Enabled</span>
          </label>
        </div>
      </div>

      <div class="form-section">
        <h3 class="section-title">Source Repository</h3>

        <div class="form-group">
          <label class="form-label">Source URL *</label>
          <input
            v-model="form.source.url"
            type="text"
            class="form-input"
            placeholder="git@github.com:user/repo.git"
            required
          />
        </div>

        <div class="form-group">
          <label class="form-label">SSH Key for Source *</label>
          <select v-model="form.source.ssh_key" class="form-input" required>
            <option value="">Select a key...</option>
            <option v-for="key in keyStore.keys" :key="key.name" :value="key.name">
              {{ key.name }}
            </option>
          </select>
        </div>
      </div>

      <div class="form-section">
        <h3 class="section-title">Target Repository</h3>

        <div class="form-group">
          <label class="form-label">Target URL *</label>
          <input
            v-model="form.target.url"
            type="text"
            class="form-input"
            placeholder="git@gitlab.com:user/repo.git"
            required
          />
        </div>

        <div class="form-group">
          <label class="form-label">SSH Key for Target *</label>
          <select v-model="form.target.ssh_key" class="form-input" required>
            <option value="">Select a key...</option>
            <option v-for="key in keyStore.keys" :key="key.name" :value="key.name">
              {{ key.name }}
            </option>
          </select>
        </div>
      </div>

      <div class="form-section">
        <h3 class="section-title">Sync Options</h3>

        <div class="form-group">
          <label class="form-label">Branches to Sync</label>
          <input
            v-model="branchesInput"
            type="text"
            class="form-input"
            placeholder="main, develop, feature/*"
          />
          <p class="form-help">Comma-separated list of branches. Leave empty to sync all branches.</p>
        </div>

        <div class="form-group">
          <label class="form-checkbox">
            <input v-model="form.sync_tags" type="checkbox" />
            <span>Sync Tags</span>
          </label>
        </div>
      </div>

      <div class="form-actions">
        <button type="submit" class="btn btn-primary" :disabled="submitting">
          {{ submitting ? 'Saving...' : (isEdit ? 'Update' : 'Create') }}
        </button>
        <router-link to="/repositories" class="btn btn-secondary">Cancel</router-link>
      </div>
    </form>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useRepositoryStore, useKeyStore } from '@/stores'

const router = useRouter()
const route = useRoute()
const repoStore = useRepositoryStore()
const keyStore = useKeyStore()

const isEdit = computed(() => !!route.params.name)
const loading = ref(false)
const submitting = ref(false)
const error = ref(null)

const form = ref({
  name: '',
  enabled: true,
  source: {
    url: '',
    ssh_key: '',
  },
  target: {
    url: '',
    ssh_key: '',
  },
  sync_branches: [],
  sync_tags: true,
})

const branchesInput = computed({
  get: () => form.value.sync_branches.join(', '),
  set: (val) => {
    form.value.sync_branches = val
      .split(',')
      .map(s => s.trim())
      .filter(s => s.length > 0)
  }
})

onMounted(async () => {
  loading.value = true
  try {
    await keyStore.fetchKeys()

    if (isEdit.value) {
      await repoStore.fetchRepositories()
      const repo = repoStore.repositories.find(r => r.name === route.params.name)
      if (repo) {
        form.value = {
          name: repo.name,
          enabled: repo.enabled,
          source: { ...repo.source },
          target: { ...repo.target },
          sync_branches: [...repo.sync_branches],
          sync_tags: repo.sync_tags,
        }
      } else {
        error.value = 'Repository not found'
      }
    }
  } finally {
    loading.value = false
  }
})

async function handleSubmit() {
  error.value = null
  submitting.value = true

  try {
    if (isEdit.value) {
      await repoStore.updateRepository(route.params.name, form.value)
    } else {
      await repoStore.createRepository(form.value)
    }
    router.push('/repositories')
  } catch (e) {
    error.value = e.response?.data?.detail || e.message || 'Failed to save repository'
  } finally {
    submitting.value = false
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

.form-card {
  max-width: 800px;
}

.form-section {
  margin-bottom: 2rem;
  padding-bottom: 1.5rem;
  border-bottom: 1px solid var(--border-color);
}

.form-section:last-of-type {
  border-bottom: none;
  margin-bottom: 1rem;
}

.section-title {
  font-size: 1.125rem;
  font-weight: 600;
  margin-bottom: 1rem;
}

.form-help {
  font-size: 0.75rem;
  color: var(--text-muted);
  margin-top: 0.25rem;
}

.form-actions {
  display: flex;
  gap: 1rem;
}
</style>
