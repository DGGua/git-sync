import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { repositoriesApi, configApi, keysApi, syncApi } from '@/api'

export const useRepositoryStore = defineStore('repositories', () => {
  const repositories = ref([])
  const loading = ref(false)
  const error = ref(null)

  async function fetchRepositories() {
    loading.value = true
    error.value = null
    try {
      const response = await repositoriesApi.list()
      repositories.value = response.data
    } catch (e) {
      error.value = e.message
    } finally {
      loading.value = false
    }
  }

  async function createRepository(data) {
    const response = await repositoriesApi.create(data)
    await fetchRepositories()
    return response.data
  }

  async function updateRepository(name, data) {
    const response = await repositoriesApi.update(name, data)
    await fetchRepositories()
    return response.data
  }

  async function deleteRepository(name) {
    await repositoriesApi.delete(name)
    await fetchRepositories()
  }

  async function reorderRepositories(orderedNames) {
    await repositoriesApi.reorder(orderedNames)
    await fetchRepositories()
  }

  return {
    repositories,
    loading,
    error,
    fetchRepositories,
    createRepository,
    updateRepository,
    deleteRepository,
    reorderRepositories,
  }
})

export const useConfigStore = defineStore('config', () => {
  const config = ref(null)
  const loading = ref(false)
  const error = ref(null)

  async function fetchConfig() {
    loading.value = true
    error.value = null
    try {
      const response = await configApi.get()
      config.value = response.data
    } catch (e) {
      error.value = e.message
    } finally {
      loading.value = false
    }
  }

  async function updateConfig(data) {
    const response = await configApi.update(data)
    config.value = response.data
    return response.data
  }

  return {
    config,
    loading,
    error,
    fetchConfig,
    updateConfig,
  }
})

export const useKeyStore = defineStore('keys', () => {
  const keys = ref([])
  const loading = ref(false)
  const error = ref(null)

  async function fetchKeys() {
    loading.value = true
    error.value = null
    try {
      const response = await keysApi.list()
      keys.value = response.data
    } catch (e) {
      error.value = e.message
    } finally {
      loading.value = false
    }
  }

  async function generateKey(data) {
    const response = await keysApi.generate(data)
    await fetchKeys()
    return response.data
  }

  async function deleteKey(name) {
    await keysApi.delete(name)
    await fetchKeys()
  }

  return {
    keys,
    loading,
    error,
    fetchKeys,
    generateKey,
    deleteKey,
  }
})

export const useSyncStore = defineStore('sync', () => {
  const syncResults = ref(null)
  const syncing = ref(false)
  const error = ref(null)

  async function runSync(repository = null, dryRun = false) {
    syncing.value = true
    error.value = null
    try {
      const response = await syncApi.run(repository, dryRun)
      syncResults.value = response.data
      return response.data
    } catch (e) {
      error.value = e.response?.data?.detail || e.message
      throw e
    } finally {
      syncing.value = false
    }
  }

  async function runSingleSync(name, dryRun = false) {
    syncing.value = true
    error.value = null
    try {
      const response = await syncApi.runSingle(name, dryRun)
      return response.data
    } catch (e) {
      error.value = e.response?.data?.detail || e.message
      throw e
    } finally {
      syncing.value = false
    }
  }

  return {
    syncResults,
    syncing,
    error,
    runSync,
    runSingleSync,
  }
})
