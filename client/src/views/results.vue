<template>
    <div class="flex flex-col items-start space-y-4 p-4">
        <template v-for="result in results">
            <div class="w-full max-w-2xl p-4 bg-white shadow-sm rounded-lg transition duration-200 ease-in-out">
                <!-- Title -->
                <h2 class="text-xl font-bold hover:underline cursor-pointer">{{ result.title }}</h2>
                <!-- URL -->
                <a :href="result.url" class="text-sm text-gray-500 hover:text-gray-700">{{ result.url }}</a>

                <!-- Categories -->
                <div class="mt-2 flex flex-wrap space-x-2">
                    <span v-for="category in result.categories"
                          class="bg-blue-100 text-xs font-semibold mr-2 px-2.5 py-0.5 rounded-full">{{
                            category
                        }}</span>
                </div>

                <!-- Meta Description -->
                <p class="mt-2 text-gray-700">{{ result.description }}</p>
            </div>
        </template>
    </div>
</template>

<script setup lang="ts">
const result = {
    id: 1,
    title: 'Result 1',
    description: 'Lorem ipsum dolor sit amet, consectetur adipiscing elit. Nullam nec purus. Donec ut nunc. Nulla facilisi. Nullam auctor, felis nec tempus.',
    url: 'https://example.com',
    categories: ['Category 1', 'Category 2']
}
const results = ref([result, result, result])
</script>
