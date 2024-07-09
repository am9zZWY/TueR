<template>
    <div
        class="p-2 border-b border-orange-200 cursor-pointer hover:bg-orange-300 rounded-lg transition duration-200 ease-in-out my-1">
        {{ result }}
    </div>
</template>

<script lang="ts" setup>
const props = defineProps<{
    result: string
}>()
</script>
