<template>
  <div
    class="flex bg-white rounded-lg border-gray-200 shadow-sm transition-all duration-300 hover:shadow-md overflow-hidden max-w-7xl">
    <!-- Left side: Content -->
    <div class="w-1/2 p-5">
      <div class="flex justify-between items-start">
        <div class="flex flex-col">
          <a :href="result.url"
             class="text-xl font-semibold text-primary-600 hover:text-primary-700 transition duration-300 hover:underline underline-offset-2"
             target="_blank">
            {{ result.title }}
          </a>
          <a :href="result.url" target="_blank"
             class="text-sm text-gray-500 hover:text-gray-600 transition duration-300">
            {{ result.url }}
          </a>
        </div>
      </div>
      <p class="text-gray-600 mt-3 leading-relaxed truncate max-h-24 overflow-hidden"
         v-if="result.description">
        {{ result.description.length > 100 ? result.description.slice(0, 100) + '...' : result.description }}</p>
      <div class="mt-4 flex flex-wrap gap-2">
        <span v-for="tag in result.tags" :key="tag"
              class="px-3 py-1 bg-primary-100 text-primary-600 rounded-full text-xs font-medium">
          {{ tag }}
        </span>
        <!-- <span class="px-3 py-1 bg-primary-100 text-primary-600 rounded-full text-xs font-medium" v-if="result.score">
          {{ Math.round((result.score ?? 0) * 100) / 100 }}%
        </span> -->
      </div>
      <div class="mt-4">
        <button @click="toggleSummary" :disabled="loadingSummary"
                class="text-sm text-primary-600 hover:text-primary-700 font-medium focus:outline-none">
          {{ showSummary ? 'Hide' : 'Show' }} Summary
        </button>
        <div v-if="loadingSummary"
             class="animate-spin rounded-full h-4 w-4 border-t-2 border-b-2 border-primary-500 mx-2">
        </div>
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
          {{ summary }}
        </p>
      </transition>
    </div>

    <!-- Right side: Preview -->
    <div class="w-1/2 p-10">
      <div class="flex justify-end">
        <button @click="togglePreview"
                class="text-sm text-primary-600 hover:text-primary-700 font-medium focus:outline-none">
          {{ preview ? 'Hide' : 'Show' }} Preview
        </button>
      </div>
      <div class="rounded-2xl h-full flex items-center justify-center" v-if="showPreview">
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


const showPreview = ref(false)
const preview = ref('')
const togglePreview = async () => {
  showPreview.value = !showPreview.value
  if (preview.value) {
    return
  }

  const response = await fetch(`${ENGINE_ENDPOINT}/preview?url=${result.url}`)
  preview.value = URL.createObjectURL(await response.blob())
}

const loadingSummary = ref(false)
const showSummary = ref(false)
const summary = ref('')
const toggleSummary = async () => {
  loadingSummary.value = true
  showSummary.value = !showSummary.value
  if (summary.value) {
    loadingSummary.value = false
    return
  }

  summary.value = await fetch(`${ENGINE_ENDPOINT}/summary/${result.id}`)
    .then((res) => res.json())
    .then((data) => {
      loadingSummary.value = false
      return data.summary
    })
}

//watch(() => result.url, downloadPreview, { immediate: true })
</script>
