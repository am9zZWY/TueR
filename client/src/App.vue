<script setup lang="ts">
import { RouterView } from 'vue-router'
import { useConfigStore } from '@/stores/config'

const configStore = useConfigStore()
</script>

<template>
  <div class="min-h-screen flex flex-col">
    <header class="shadow-sm p-4 sticky top-0 z-10 bg-gradient-to-br from-orange-200 to-purple-300 text-black">
      <div class="flex justify-between items-center">
        <ul class="flex justify-center space-x-4">
          <li>
            <router-link to="/">Home</router-link>
          </li>
        </ul>
        <ul class="flex justify-center space-x-4">
          <li>
            <button class="py-2 px-4 rounded-lg transition duration-300"
                    @click="configStore.toggleConfig('bionicReading')">
              {{ configStore.getConfig('bionicReading') ? 'Disable' : 'Enable' }} bionic reading
            </button>
          </li>
          <li>
            <button class="py-2 px-4 rounded-lg transition duration-300"
                    @click="configStore.toggleConfig('dyslexicFont')">
              {{ configStore.getConfig('dyslexicFont') ? 'Disable' : 'Enable' }} dyslexic font
            </button>
          </li>
        </ul>
      </div>
    </header>
    <main class="min-h-screen bg-gray-50 flex items-center justify-center">
      <RouterView />
    </main>
  </div>
</template>
