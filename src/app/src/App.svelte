<script>
    import { onMount } from 'svelte';
    import AppRouter from "$components/AppRouter.svelte";
    import './global.css'; // Import the global styles here

    export let url = "";
    let currentCatalog = window.location.pathname.split('/')[1] || '';
    let currentPath = window.location.pathname;

    // Update currentPath when location changes
    onMount(() => {
        const handleLocationChange = () => {
            currentPath = window.location.pathname;
            currentCatalog = window.location.pathname.split('/')[1] || '';
        };
        
        // Listen for popstate events (browser back/forward)
        window.addEventListener('popstate', handleLocationChange);
        
        return () => {
            window.removeEventListener('popstate', handleLocationChange);
        };
    });
</script>

<AppRouter {url} {currentCatalog} {currentPath} />