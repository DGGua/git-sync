<template>
  <div class="container">
    <h1 class="page-title">Settings</h1>

    <div v-if="configStore.loading" class="loading">Loading...</div>

    <form v-else @submit.prevent="handleSave" class="settings-form">
      <div v-if="success" class="alert alert-success">{{ success }}</div>
      <div v-if="error" class="alert alert-danger">{{ error }}</div>

      <div class="card">
        <div class="card-header">
          <h2 class="card-title">SSH Settings</h2>
        </div>

        <div class="form-group">
          <label class="form-label">Key Storage Directory</label>
          <input
            v-model="form.ssh.key_storage"
            type="text"
            class="form-input"
            placeholder=".ssh"
          />
          <p class="form-help">Directory where SSH keys are stored (relative to config directory)</p>
        </div>

        <div class="form-group">
          <label class="form-label">Default Key Type</label>
          <select v-model="form.ssh.default_key_type" class="form-input">
            <option value="ed25519">ED25519 (Recommended)</option>
            <option value="rsa">RSA</option>
            <option value="ecdsa">ECDSA</option>
          </select>
        </div>
      </div>

      <div class="card">
        <div class="card-header">
          <h2 class="card-title">Sync Settings</h2>
        </div>

        <div class="form-group">
          <label class="form-label">Temporary Directory</label>
          <input
            v-model="form.sync.temp_dir"
            type="text"
            class="form-input"
            placeholder="/tmp/git-sync"
          />
          <p class="form-help">Directory for temporary files during sync operations</p>
        </div>

        <div class="form-group">
          <label class="form-label">Timeout (seconds)</label>
          <input
            v-model.number="form.sync.timeout"
            type="number"
            class="form-input"
            min="30"
            max="3600"
          />
        </div>

        <div class="form-group">
          <label class="form-checkbox">
            <input v-model="form.sync.cleanup_after_sync" type="checkbox" />
            <span>Cleanup After Sync</span>
          </label>
          <p class="form-help">Remove temporary files after sync completes</p>
        </div>

        <div class="form-group">
          <label class="form-checkbox">
            <input v-model="form.sync.enable_mirror_cache" type="checkbox" />
            <span>Enable Mirror Cache</span>
          </label>
          <p class="form-help">Use local mirror cache for faster subsequent syncs</p>
        </div>

        <div class="form-group" v-if="form.sync.enable_mirror_cache">
          <label class="form-label">Mirror Cache Directory</label>
          <input
            v-model="form.sync.mirror_cache_dir"
            type="text"
            class="form-input"
            placeholder=".mirror-cache"
          />
        </div>
      </div>

      <div class="form-actions">
        <button type="submit" class="btn btn-primary" :disabled="saving">
          {{ saving ? 'Saving...' : 'Save Settings' }}
        </button>
      </div>
    </form>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useConfigStore } from '@/stores'

const configStore = useConfigStore()

const saving = ref(false)
const success = ref(null)
const error = ref(null)

const form = reactive({
  ssh: {
    key_storage: '.ssh',
    default_key_type: 'ed25519',
  },
  sync: {
    temp_dir: '/tmp/git-sync',
    timeout: 300,
    cleanup_after_sync: true,
    enable_mirror_cache: true,
    mirror_cache_dir: '.mirror-cache',
  },
})

onMounted(async () => {
  await configStore.fetchConfig()
  if (configStore.config) {
    Object.assign(form.ssh, configStore.config.ssh)
    Object.assign(form.sync, configStore.config.sync)
  }
})

async function handleSave() {
  saving.value = true
  success.value = null
  error.value = null

  try {
    await configStore.updateConfig({
      ssh: form.ssh,
      sync: form.sync,
    })
    success.value = 'Settings saved successfully!'
    setTimeout(() => {
      success.value = null
    }, 3000)
  } catch (e) {
    error.value = e.response?.data?.detail || e.message
  } finally {
    saving.value = false
  }
}
</script>

<style scoped>
.page-title {
  font-size: 1.75rem;
  font-weight: 700;
  margin-bottom: 1.5rem;
}

.settings-form {
  max-width: 800px;
}

.form-help {
  font-size: 0.75rem;
  color: var(--text-muted);
  margin-top: 0.25rem;
}

.form-actions {
  margin-top: 1rem;
}
</style>
