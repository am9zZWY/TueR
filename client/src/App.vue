<script setup lang="ts">
import { RouterView } from 'vue-router'
import { useConfigStore } from '@/stores/config'
import useDyslexic from '@/composables/useDyslexic'
import { TITLE } from './configuration'
const dyslexic = useDyslexic()

const configStore = useConfigStore()
</script>

<template>
  <div class="min-h-screen flex flex-col">
    <header class="shadow-lg p-4 sticky top-0 z-10 bg-gradient-to-br from-primary-300 to-secondary-400 text-black rounded-lg mx-4 mt-4 transform translate-y-2">
      <div class="flex justify-between items-center">
        <ul class="flex justify-center space-x-6">
          <li class="text-lg font-medium text-white">
            <router-link to="/">{{ TITLE }}</router-link>
          </li>
        </ul>
        <ul class="flex justify-center space-x-6">
          <li>
            <button class="py-2 px-6 rounded-full transition duration-300 bg-white text-black hover:bg-gray-100 shadow-md"
                    @click="configStore.toggleConfig('bionicReading')">
              {{ configStore.getConfig('bionicReading') ? 'Disable' : 'Enable' }} bionic reading
            </button>
          </li>
          <li>
            <button class="py-2 px-6 rounded-full transition duration-300 bg-white text-black hover:bg-gray-100 shadow-md"
                    @click="dyslexic.toggleDyslexicFont()">
              {{ dyslexic.isDyslexic ? 'Disable' : 'Enable' }} dyslexic font
            </button>
          </li>
        </ul>
      </div>
    </header>
    <main class="min-h-screen flex-1 bg-gray-50 flex items-center justify-center mt-4">
      <RouterView />
    </main>
  </div>
</template>
