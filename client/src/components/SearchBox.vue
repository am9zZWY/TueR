<template>
  <div>
    <input v-model="message" @keydown.enter="searchEnter" />
    <div v-if="suggestionResults.length > 0">
      <div v-for="result in suggestionResults" :key="result">
        <div>{{ result }}</div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useSearchStore } from '@/stores/search'

const message = ref('')
const suggestionResults = ref<string[]>([
  'Apple',
  'Banana',
  'Cherry'
])
const searchStore = useSearchStore()
const searchEnter = () => {
  searchStore.search(message.value)
}
</script>
