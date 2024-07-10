<template>
  <div>
    <div class="bg-white p-8 rounded-lg shadow-lg w-full max-w-6xl">
      <div class="flex items-center border-b border-pastel-green py-2 mb-6">
        <input
          class="appearance-none bg-transparent border-none w-full text-gray-700 mr-3 py-1 px-2 leading-tight focus:outline-none focus:ring-0 placeholder-gray-400"
          type="text"
          placeholder="Search..."
          aria-label="Search"
          v-model="query"
          @keyup.enter="search"
        />
        <button
          class="flex-shrink-0 bg-red-200 hover:bg-red-400 text-sm border-none text-white py-2 px-4 rounded-2xl transition duration-300"
          type="button"
          @click="search"
        >
          Search
        </button>
      </div>
      <div v-if="loading" class="text-center text-gray-600">
        Loading...
      </div>
      <div v-else>
        <ul>
          <li v-for="result in results" :key="result.id"
              class="mb-4 p-4 border rounded-lg shadow-sm bg-white hover:shadow-md transition-shadow duration-300">
            <a :href="result.url" class="text-blue-400 hover:text-blue-500 font-medium text-lg">{{ result.title }}</a>
            <p class="text-gray-600 mt-2">{{ result.description }}</p>
            <p>
              {{ result.summary }}
            </p>
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
