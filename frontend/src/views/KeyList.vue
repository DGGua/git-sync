<template>
  <div class="container">
    <div class="page-header">
      <h1 class="page-title">SSH Keys</h1>
      <button class="btn btn-primary" @click="showGenerateModal = true">
        Generate Key
      </button>
    </div>

    <div v-if="keyStore.loading" class="loading">Loading...</div>

    <div v-else-if="keyStore.keys.length === 0" class="empty-state card">
      <div class="empty-state-icon">🔑</div>
      <p>No SSH keys configured</p>
      <button class="btn btn-primary" @click="showGenerateModal = true">
        Generate Your First Key
      </button>
    </div>

    <div v-else class="key-list">
      <div v-for="key in keyStore.keys" :key="key.name" class="key-item">
        <div class="key-info">
          <span class="key-name">{{ key.name }}</span>
          <span class="key-meta">{{ key.key_type }} • {{ key.path }}</span>
        </div>
        <div class="key-actions">
          <button class="btn btn-sm btn-secondary" @click="showPublicKey(key)">
            View Public Key
          </button>
          <button class="btn btn-sm btn-danger" @click="handleDelete(key.name)">
            Delete
          </button>
        </div>
      </div>
    </div>

    <!-- Generate Key Modal -->
    <div v-if="showGenerateModal" class="modal-overlay" @click.self="showGenerateModal = false">
      <div class="modal">
        <div class="modal-header">
          <h3>Generate SSH Key</h3>
          <button class="modal-close" @click="showGenerateModal = false">&times;</button>
        </div>
        <form @submit.prevent="handleGenerate">
          <div class="modal-body">
            <div v-if="generateError" class="alert alert-danger">{{ generateError }}</div>

            <div class="form-group">
              <label class="form-label">Key Name *</label>
              <input
                v-model="generateForm.name"
                type="text"
                class="form-input"
                placeholder="my-key"
                required
              />
            </div>

            <div class="form-group">
              <label class="form-label">Key Type</label>
              <select v-model="generateForm.key_type" class="form-input">
                <option value="ed25519">ED25519 (Recommended)</option>
                <option value="rsa">RSA</option>
                <option value="ecdsa">ECDSA</option>
              </select>
            </div>

            <div class="form-group">
              <label class="form-label">Comment (optional)</label>
              <input
                v-model="generateForm.comment"
                type="text"
                class="form-input"
                placeholder="user@example.com"
              />
            </div>
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" @click="showGenerateModal = false">
              Cancel
            </button>
            <button type="submit" class="btn btn-primary" :disabled="generating">
              {{ generating ? 'Generating...' : 'Generate' }}
            </button>
          </div>
        </form>
      </div>
    </div>

    <!-- View Public Key Modal -->
    <div v-if="showViewModal" class="modal-overlay" @click.self="showViewModal = false">
      <div class="modal">
        <div class="modal-header">
          <h3>Public Key: {{ viewingKey?.name }}</h3>
          <button class="modal-close" @click="showViewModal = false">&times;</button>
        </div>
        <div class="modal-body">
          <pre class="key-display">{{ viewingKey?.public_key }}</pre>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="copyPublicKey">
            Copy to Clipboard
          </button>
          <button class="btn btn-primary" @click="showViewModal = false">
            Close
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useKeyStore } from '@/stores'

const keyStore = useKeyStore()

const showGenerateModal = ref(false)
const showViewModal = ref(false)
const generating = ref(false)
const generateError = ref(null)
const viewingKey = ref(null)

const generateForm = reactive({
  name: '',
  key_type: 'ed25519',
  comment: '',
})

onMounted(() => {
  keyStore.fetchKeys()
})

async function handleGenerate() {
  generateError.value = null
  generating.value = true

  try {
    await keyStore.generateKey(generateForm)
    showGenerateModal.value = false
    generateForm.name = ''
    generateForm.comment = ''
  } catch (e) {
    generateError.value = e.response?.data?.detail || e.message
  } finally {
    generating.value = false
  }
}

async function showPublicKey(key) {
  viewingKey.value = { ...key, public_key: 'Loading...' }
  showViewModal.value = true

  try {
    const response = await fetch(`/api/keys/${key.name}/public`)
    if (!response.ok) {
      throw new Error('Failed to fetch public key')
    }
    const data = await response.json()
    viewingKey.value = { ...key, public_key: data.message }
  } catch (e) {
    viewingKey.value = { ...key, public_key: `Error: ${e.message}` }
  }
}

function copyPublicKey() {
  if (viewingKey.value?.public_key) {
    navigator.clipboard.writeText(viewingKey.value.public_key)
    alert('Public key copied to clipboard!')
  }
}

async function handleDelete(name) {
  if (confirm(`Are you sure you want to delete the key "${name}"?`)) {
    await keyStore.deleteKey(name)
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

.key-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.key-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1rem 1.5rem;
  background: var(--card-bg);
  border: 1px solid var(--border-color);
  border-radius: 8px;
}

.key-actions {
  display: flex;
  gap: 0.5rem;
}

/* Modal Styles */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal {
  background: var(--card-bg);
  border-radius: 8px;
  width: 100%;
  max-width: 500px;
  max-height: 90vh;
  overflow: auto;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 1.5rem;
  border-bottom: 1px solid var(--border-color);
}

.modal-header h3 {
  font-size: 1.125rem;
  font-weight: 600;
}

.modal-close {
  background: none;
  border: none;
  font-size: 1.5rem;
  cursor: pointer;
  color: var(--text-muted);
  line-height: 1;
}

.modal-close:hover {
  color: var(--text-color);
}

.modal-body {
  padding: 1.5rem;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 1rem;
  padding: 1rem 1.5rem;
  border-top: 1px solid var(--border-color);
}

.key-display {
  background: var(--bg-color);
  padding: 1rem;
  border-radius: 4px;
  font-size: 0.75rem;
  word-break: break-all;
  white-space: pre-wrap;
  max-height: 200px;
  overflow: auto;
}
</style>
