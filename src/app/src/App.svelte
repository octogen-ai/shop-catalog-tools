<script>
    import { Router, Link, Route } from "svelte-routing";
    import { onMount } from 'svelte';
    import CatalogSelector from "./components/CatalogSelector.svelte";
    import ProductList from "./routes/ProductList.svelte";
    import Analytics from "./routes/Analytics.svelte";
    
    export let url = "";
    let currentCatalog = window.location.pathname.split('/')[1] || 'anntaylor';
    let currentPath = window.location.pathname;
    let isAnalyticsPage;

    onMount(() => {
        // Handle root path redirect
        if (window.location.pathname === '/') {
            window.location.href = '/anntaylor';
            return;
        }
        isAnalyticsPage = window.location.pathname.includes('analytics');
    });

    function handleCatalogChange(event) {
        const catalog = event.detail;
        const path = window.location.pathname;
        if (path.includes('analytics')) {
            window.location.href = `/${catalog}/analytics`;
        } else {
            window.location.href = `/${catalog}`;
        }
    }

    function handleNavigate(isAnalytics) {
        isAnalyticsPage = isAnalytics;
        currentPath = window.location.pathname;
    }
</script>

<Router {url}>
    <nav class="bg-gray-800">
        <div class="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
            <div class="flex h-16 items-center justify-between">
                <div class="flex flex-1 items-center justify-start">
                    <div class="flex space-x-4">
                        <Link 
                            to="/{currentCatalog}" 
                            class="rounded-md px-3 py-2 text-sm font-medium {!isAnalyticsPage ? 'bg-gray-900 text-white' : 'text-gray-300 hover:bg-gray-700 hover:text-white'}"
                            on:click={() => handleNavigate(false)}
                        >
                            Products
                        </Link>
                        <Link 
                            to="/{currentCatalog}/analytics" 
                            class="rounded-md px-3 py-2 text-sm font-medium {isAnalyticsPage ? 'bg-gray-900 text-white' : 'text-gray-300 hover:bg-gray-700 hover:text-white'}"
                            on:click={() => handleNavigate(true)}
                        >
                            Analytics
                        </Link>
                    </div>
                    <div class="ml-6">
                        <CatalogSelector on:change={handleCatalogChange} />
                    </div>
                </div>
            </div>
        </div>
    </nav>

    <main class="container mx-auto px-4 py-8">
        <Route path="/:table/analytics" component={Analytics} />
        <Route path="/:table" component={ProductList} />
    </main>
</Router>

<style>
    :global(html) {
        background-color: #f9fafb;
    }
</style>