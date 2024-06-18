<template>
    <div class="p-4 rounded-2xl shadow-sm bg-white w-full max-w-md mx-auto">
        <!-- Search Input -->
        <input type="search" v-model="message" :placeholder="placeholderSuggestions"
               class="w-full p-2 rounded-lg border border-gray-200 focus:outline-none
                   focus:border-gray-50 transition duration-200 ease-in-out" @keyup.enter="searchEnter"/>

        <!-- Search Suggestions -->
        <div class="mt-2">
            <template v-for="result in suggestionResults">
                <div @click="message = result"
                     class="p-2 border-b border-gray-200 cursor-pointer hover:bg-gray-300 rounded-lg transition duration-200 ease-in-out my-1">
                    {{ result }}
                </div>
            </template>
        </div>
    </div>
</template>

<script setup lang="ts">

const router = useRouter()

const message = ref('')
const placeholderSuggestions = ref<string>('')
const suggestionResults = ref<string[]>([
    'Apple',
    'Banana',
    'Cherry',
])
const searchEnter = () => {
    router.push(`/results?query=${message.value}`)
}
</script>
