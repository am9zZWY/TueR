<template>
  <div class="min-h-screen flex items-center justify-center p-4 w-full">
    <div class="p-8 rounded-2xl shadow-2xl w-full max-w-3xl bg-white">
      <h1
        class="text-4xl font-bold text-center text-transparent bg-clip-text bg-gradient-to-r from-primary-700 to-secondary-400">
        {{ TITLE }}
      </h1>
      <h2 class="text-2xl font-semibold text-center text-tertiary-800 mb-8">
        {{ SUBTITLE }}
      </h2>
      <div class="relative mb-8">
        <input
          class="w-full bg-gray-100 rounded-full py-3 px-6 pr-12 text-gray-700 leading-tight focus:outline-none focus:ring-2 focus:ring-tertiary-800 focus:bg-white transition duration-300"
          type="text"
          placeholder="Search the coolness..."
          aria-label="Search"
          v-model="query"
          @keyup.enter="search"
        />
        <button
          class="absolute right-1.5 top-0.5 bg-gradient-to-bl from-primary-700 to-secondary-400 text-white rounded-full p-2 hover:from-primary-700 hover:to-tertiary-800 transition duration-300"
          type="button"
          @click="search"
        >
          <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                  d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
        </button>
      </div>
      <div v-if="loading" class="text-center text-gray-600">
        <div class="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-tertiary-500 mx-auto"></div>
        <p class="mt-4">{{ TITLE }}</p>
      </div>
      <div v-else>
        <!-- Search Results -->
        <ul class="space-y-6">
          <transition-group
            tag="ul"
            class="space-y-6"
            :css="false"
            @before-enter="onBeforeEnter"
            @enter="onEnter"
            @leave="onLeave"
          >
            <li v-for="result in results" :key="result.id"
                class="bg-white rounded-lg border border-gray-200 shadow-sm transition-all duration-300 hover:shadow-md overflow-hidden">
              <SearchResult :result="result" :key="result.id" :data-index="results.indexOf(result)" />
            </li>
          </transition-group>
        </ul>
      </div>
    </div>
  </div>
</template>


<script setup lang="ts">
import { storeToRefs } from 'pinia'
import { ref } from 'vue'
import { useSearchStore } from '@/stores/search'
import { SUBTITLE, TITLE } from '@/configuration'
import { gsap } from 'gsap'
import SearchResult from '@/components/SearchResult.vue'

const searchStore = useSearchStore()
const { results } = storeToRefs(searchStore)

const loading = false

const query = ref('')
const search = () => {
  searchStore.search(query.value)
}


// For animation of the search results
function onBeforeEnter(el: HTMLElement) {
  el.style.opacity = '0'
  el.style.height = '0'
}

function onEnter(el: HTMLElement, done: gsap.Callback) {
  gsap.to(el, {
    opacity: 1,
    height: 'auto',
    delay: parseInt(el.dataset.index || '0') * 0.25,
    onComplete: done
  })
}

function onLeave(el: HTMLElement, done: gsap.Callback) {
  gsap.to(el, {
    opacity: 0,
    height: 0,
    delay: parseInt(el.dataset.index || '0') * 0.15,
    onComplete: done
  })
}
</script>
