<template>
  <div class="index-view">
    <nav class="navigation">
      <div class="nav-container">
        <router-link to="/" class="nav-brand">
          <img src="/logo.png" alt="World Alphabets" class="nav-logo" />
          <span class="nav-brand-text">World Alphabets</span>
        </router-link>
        <div class="nav-links">
          <router-link to="/" class="nav-link" :class="{ active: $route.name === 'index' }">
            Browse All
          </router-link>
          <router-link to="/explore" class="nav-link" :class="{ active: $route.name === 'explore' }">
            Language Explorer
          </router-link>
          <router-link to="/detect-language" class="nav-link" :class="{ active: $route.name === 'detect-language' }">
            Language Detection
          </router-link>
        </div>
      </div>
    </nav>
    
    <main class="main-content">
      <AlphabetIndex />
    </main>
  </div>
</template>

<script setup>
import AlphabetIndex from '../components/AlphabetIndex.vue';
</script>

<style scoped>
.index-view {
  min-height: 100vh;
  background: #f8f9fa;
}

.navigation {
  background: white;
  border-bottom: 1px solid #dee2e6;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.nav-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 1rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  height: 60px;
}

.nav-brand {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  font-size: 1.5rem;
  font-weight: 700;
  color: #007bff;
  text-decoration: none;
}

.nav-brand:hover {
  color: #0056b3;
}

.nav-logo {
  height: 40px;
  width: auto;
}

.nav-brand-text {
  font-size: 1.5rem;
  font-weight: 700;
}

.nav-links {
  display: flex;
  gap: 2rem;
}

.nav-link {
  color: #6c757d;
  text-decoration: none;
  font-weight: 500;
  padding: 0.5rem 1rem;
  border-radius: 4px;
  transition: all 0.2s;
}

.nav-link:hover {
  color: #007bff;
  background: #f8f9fa;
}

.nav-link.active {
  color: #007bff;
  background: #e3f2fd;
}

.main-content {
  padding-top: 2rem;
}

@media (max-width: 768px) {
  .nav-container {
    padding: 0 0.5rem;
    height: 50px;
  }
  
  .nav-logo {
    height: 32px;
  }

  .nav-brand-text {
    font-size: 1.2rem;
  }
  
  .nav-links {
    gap: 1rem;
  }
  
  .nav-link {
    padding: 0.25rem 0.5rem;
    font-size: 0.9rem;
  }
  
  .main-content {
    padding-top: 1rem;
  }
}
</style>
