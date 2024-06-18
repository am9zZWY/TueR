<template>
    <div class="w-max m-auto">
        <div class="min-h-80" />

        <h1 class="text-4xl font-bold text-center">
            <Logo>
                <span> Search</span>
            </Logo>
        </h1>
        <SearchBox/>
    </div>
</template>

<script lang="ts" setup>
import SearchBox from "~/components/SearchBox.vue";
import Logo from "~/components/Logo.vue";
</script>
