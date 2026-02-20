<template>
  <div id="app">
    <nav class="navbar">
      <div class="navbar-brand">
        <router-link to="/">Git Sync</router-link>
      </div>
      <div class="navbar-menu">
        <router-link to="/" class="nav-link">Dashboard</router-link>
        <router-link to="/repositories" class="nav-link">Repositories</router-link>
        <router-link to="/keys" class="nav-link">SSH Keys</router-link>
        <router-link to="/history" class="nav-link">History</router-link>
        <router-link to="/settings" class="nav-link">Settings</router-link>
      </div>
    </nav>
    <main class="main-content">
      <router-view />
    </main>
  </div>
</template>

<script setup>
</script>

<style scoped>
.navbar {
  background: var(--card-bg);
  border-bottom: 1px solid var(--border-color);
  padding: 0 2rem;
  display: flex;
  align-items: center;
  height: 60px;
  position: sticky;
  top: 0;
  z-index: 100;
}

.navbar-brand a {
  font-size: 1.25rem;
  font-weight: 700;
  color: var(--primary-color);
  text-decoration: none;
}

.navbar-menu {
  display: flex;
  gap: 1rem;
  margin-left: 2rem;
}

.nav-link {
  padding: 0.5rem 1rem;
  color: var(--text-muted);
  text-decoration: none;
  border-radius: 6px;
  transition: all 0.2s;
}

.nav-link:hover {
  color: var(--text-color);
  background: var(--bg-color);
}

.nav-link.router-link-active {
  color: var(--primary-color);
  background: rgba(59, 130, 246, 0.1);
}

.main-content {
  min-height: calc(100vh - 60px);
}
</style>
