<script setup lang="ts">
import { RouterView } from 'vue-router'
</script>

<template>
  <header class="bg-white shadow-sm p-4">
    <div class="flex justify-between items-center">
      <ul class="flex justify-center space-x-4">
        <li>
          <router-link to="/" class="text-gray-600 hover:text-gray-800">Home</router-link>
        </li>
      </ul>
      <ul class="flex justify-center space-x-4">
        <li>
          <button class="py-2 px-4 rounded-lg transition duration-300">
            Bionic Reading
          </button>
        </li>
        <li>
          <button class="py-2 px-4 rounded-lg transition duration-300">
            Speed Reading
          </button>
        </li>
      </ul>
    </div>
  </header>
  <main class="min-h-screen bg-gray-50 flex items-center justify-center">
    <RouterView />
  </main>
</template>
