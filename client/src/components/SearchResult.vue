<template>
  <div
    class="flex bg-white rounded-lg border-gray-200 shadow-sm transition-all duration-300 hover:shadow-md overflow-hidden max-w-7xl">
    <!-- Left side: Content -->
    <div class="w-1/2 p-5">
      <div class="flex justify-between items-start">
        <div class="flex flex-col">
          <a :href="result.url"
             class="text-xl font-semibold text-primary-600 hover:text-primary-700 transition duration-300"
             target="_blank">
            {{ result.title }}
          </a>
          <a :href="result.url" target="_blank"
             class="text-sm text-gray-500 hover:text-gray-600 transition duration-300">
            {{ result.url }}
          </a>
        </div>
      </div>
      <p class="text-gray-600 mt-3">{{ result.description }}</p>
      <div class="mt-4 flex flex-wrap gap-2">
        <span v-for="tag in result.tags" :key="tag"
              class="px-3 py-1 bg-primary-100 text-primary-600 rounded-full text-xs font-medium">
          {{ tag }}
        </span>
      </div>
      <div class="mt-4" v-if="!showSummary">
        <button @click="showSummary = true"
                class="text-sm text-primary-600 hover:text-primary-700 font-medium focus:outline-none">
          Generate Summary
        </button>
      </div>
      <transition
        enter-active-class="transition ease-out duration-200"
        enter-from-class="opacity-0 transform scale-95"
        enter-to-class="opacity-100 transform scale-100"
        leave-active-class="transition ease-in duration-150"
        leave-from-class="opacity-100 transform scale-100"
        leave-to-class="opacity-0 transform scale-95"
      >
        <p v-if="showSummary" class="text-sm text-gray-500 mt-3 leading-relaxed">
          {{ result.summary }}
        </p>
      </transition>
    </div>

    <!-- Right side: Preview -->
    <div class="w-1/2 p-5">
      <div class="flex justify-end" v-if="preview == ''">
        <button @click="downloadPreview"
                class="text-sm text-primary-600 hover:text-primary-700 font-medium focus:outline-none">
          Show Preview
        </button>
      </div>
      <div class="rounded-2xl h-full flex items-center justify-center" v-if="preview">
        <iframe :src="preview" class="w-full h-full rounded-2xl" />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import type { SearchResult } from '@/types'
import { ENGINE_ENDPOINT } from '@/configuration'

interface SearchResultProps {
  result: SearchResult
}

const { result } = defineProps<SearchResultProps>()

const showSummary = ref(false)
const preview = ref('')

const downloadPreview = async () => {
  const response = await fetch(`${ENGINE_ENDPOINT}/preview?url=${result.url}`)
  preview.value = URL.createObjectURL(await response.blob())
}

//watch(() => result.url, downloadPreview, { immediate: true })
</script>
