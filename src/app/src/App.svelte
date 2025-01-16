<script>
    import { onMount } from 'svelte';
    import AppRouter from "$components/AppRouter.svelte";
    
    export let url = "";
    let currentCatalog = window.location.pathname.split('/')[1] || 'anntaylor';
    let currentPath = window.location.pathname;

    $: {
        currentPath = window.location.pathname;
    }

    onMount(() => {
        // Handle root path redirect
        if (window.location.pathname === '/') {
            window.location.href = '/anntaylor';
            return;
        }
    });
</script>

<AppRouter {url} {currentCatalog} {currentPath} />

<style>
    :global(html) {
        background-color: #f9fafb;
    }
</style>