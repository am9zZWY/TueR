<script setup lang="ts">
import SearchBox from '@/components/SearchBox.vue'
import { storeToRefs } from 'pinia'
import { useSearchStore } from '@/stores/search'

const searchStore = useSearchStore()
const { results } = storeToRefs(searchStore)
</script>

<template>
  <main>
    <SearchBox />

    <div>
      <div v-for="(result, resultIndex) in results" :key="resultIndex">
        <a>{{ result.title }}</a>
        <div>{{ result.description }}</div>
      </div>
    </div>
  </main>
</template>
