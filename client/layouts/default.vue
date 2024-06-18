<template>
    <main class="w-full">
        <Header/>
        <div class="h-full items-center space-y-5">
            <slot/>
        </div>
    </main>
</template>

<script setup lang="ts">
import Header from "~/components/Header.vue";
</script>
