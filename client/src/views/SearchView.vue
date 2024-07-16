<template>
  <div class="min-h-screen flex items-center justify-center p-4 w-full">
    <div class="p-8 rounded-2xl shadow-2xl w-full max-w-3xl to-purple-600 ">
      <h1 class="text-4xl font-bold text-center mb-8 text-transparent bg-clip-text bg-gradient-to-r from-purple-400 to-pink-600">
        Search the coolness
      </h1>
      <div class="relative mb-8">
        <input
          class="w-full bg-gray-100 rounded-full py-3 px-6 pr-12 text-gray-700 leading-tight focus:outline-none focus:ring-2 focus:ring-purple-500 focus:bg-white transition duration-300"
          type="text"
          placeholder="Search the coolness..."
          aria-label="Search"
          v-model="query"
          @keyup.enter="search"
        />
        <button
          class="absolute right-1.5 top-0.5 bg-gradient-to-r from-purple-500 to-indigo-600 text-white rounded-full p-2 hover:from-purple-600 hover:to-indigo-700 transition duration-300"
          type="button"
          @click="search"
        >
          <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
        </button>
      </div>
      <div v-if="loading" class="text-center text-gray-600">
        <div class="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-purple-500 mx-auto"></div>
        <p class="mt-4">Searching for coolness...</p>
      </div>
      <div v-else>
        <ul>
          <li v-for="result in results" :key="result.id"
              class="mb-6 p-6 border border-gray-200 rounded-xl shadow-sm bg-white hover:shadow-lg transition-shadow duration-300">
            <div class="flex justify-between items-start">
              <a :href="result.url" class="text-xl font-semibold text-indigo-600 hover:text-indigo-800 transition duration-300">
                {{ result.title }}
              </a>
              <button class="text-gray-400 hover:text-yellow-500 transition duration-300">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z" />
                </svg>
              </button>
            </div>
            <p class="text-gray-600 mt-2">{{ result.description }}</p>
            <p class="text-sm text-gray-500 mt-4">
              {{ result.summary }}
            </p>
            <div class="mt-4 flex space-x-2">
              <span v-for="tag in result.tags" :key="tag" class="px-2 py-1 bg-gray-100 text-gray-600 rounded-full text-xs">
                {{ tag }}
              </span>
              <span class="px-2 py-1 bg-gray-100 text-gray-600 rounded-full text-xs">
                {{ result.score }}
              </span>
            </div>
          </li>
        </ul>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { storeToRefs } from 'pinia'
import { ref } from 'vue'
import { useSearchStore } from '@/stores/search'

const searchStore = useSearchStore()
const { results } = storeToRefs(searchStore)

const loading = false

const query = ref('')
const search = () => {
  searchStore.search(query.value)
}
</script>
