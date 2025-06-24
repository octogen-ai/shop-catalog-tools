<script>
    import { onMount } from 'svelte';
    import AppRouter from "$components/AppRouter.svelte";
    import './global.css'; // Import the global styles here

    export let url = "";
    let currentCatalog = window.location.pathname.split('/')[1] || '';
    let currentPath = window.location.pathname;
    let isLoading = true;

    $: {
        currentPath = window.location.pathname;
    }

    async function fetchCatalogsAndRedirect() {
        try {
            const response = await fetch('/api/catalogs');
            const data = await response.json();
            
            if (data.catalogs && data.catalogs.length > 0) {
                // Get the first catalog from the list
                const firstCatalog = data.catalogs[0];
                
                // If we're at the root path, redirect to the first catalog
                if (window.location.pathname === '/') {
                    window.location.href = `/${firstCatalog}`;
                    return;
                }
            } else {
                // Fallback to a default if no catalogs are available
                console.warn('No catalogs available, using default');
                if (window.location.pathname === '/') {
                    window.location.href = '/anntaylor';
                    return;
                }
            }
        } catch (error) {
            console.error('Error fetching catalogs:', error);
            // Fallback to a default if there's an error
            if (window.location.pathname === '/') {
                window.location.href = '/anntaylor';
                return;
            }
        } finally {
            isLoading = false;
        }
    }

    onMount(() => {
        // Fetch catalogs and handle root path redirect
        fetchCatalogsAndRedirect();
    });
</script>

<AppRouter {url} {currentCatalog} {currentPath} />