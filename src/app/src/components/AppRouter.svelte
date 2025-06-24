<script>
    import { Router, Link, Route } from "svelte-routing";
    import { navigate } from "svelte-routing";
    import CatalogSelector from "./CatalogSelector.svelte";
    import ProductList from "../routes/ProductList.svelte";
    import ProductView from "../routes/[table]/product/[id]/+page.svelte";
    import CrawlsView from "../routes/[table]/product/[id]/crawls/+page.svelte";
    import { onMount } from "svelte";

    export let url = "";
    export let currentCatalog = "";
    export let currentPath;
    let availableCatalogs = [];
    let loading = true;

    onMount(async () => {
        await fetchCatalogs();
    });

    async function fetchCatalogs() {
        try {
            const response = await fetch('/api/catalogs');
            const data = await response.json();
            availableCatalogs = data.catalogs;
            
            // If we have catalogs but none selected, use the first one
            if (availableCatalogs.length > 0 && !currentCatalog) {
                currentCatalog = availableCatalogs[0];
                if (currentPath === "/") {
                    navigate(`/${currentCatalog}`);
                }
            }
        } catch (error) {
            console.error('Error fetching catalogs:', error);
        } finally {
            loading = false;
        }
    }

    function handleNavigate(path, e) {
        e.preventDefault();
        navigate(path);
        currentPath = path;
    }

    function handleCatalogChange(event) {
        const catalog = event.detail;
        currentCatalog = catalog;
        window.location.href = `/${catalog}`;
    }
</script>

<Router {url}>
    <nav class="bg-gray-800">
        <div class="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
            <div class="flex h-16 items-center justify-between">
                <div class="flex flex-1 items-center justify-start">
                    <div class="flex space-x-4">
                        {#if currentCatalog}
                            <Link 
                                to="/{currentCatalog}" 
                                class="rounded-md px-3 py-2 text-sm font-medium bg-gray-900 text-white"
                                on:click={(e) => handleNavigate(`/${currentCatalog}`, e)}
                            >
                                Products
                            </Link>
                        {/if}
                    </div>
                    <div class="ml-6 flex-grow max-w-xs">
                        <CatalogSelector on:change={handleCatalogChange} />
                    </div>
                </div>
            </div>
        </div>
    </nav>

    <main class="container mx-auto px-4 py-8">
        {#if loading}
            <div class="flex justify-center items-center h-64">
                <div class="text-xl text-gray-600">Loading...</div>
            </div>
        {:else if !currentCatalog || availableCatalogs.length === 0}
            <div class="flex flex-col items-center justify-center h-64 text-center">
                <h1 class="text-2xl font-bold mb-4">Welcome to Shop Catalog Tools</h1>
                
                {#if availableCatalogs.length === 0}
                    <p class="text-lg text-gray-600 mb-6">
                        No catalogs are currently available. Please restart the application if you expect catalogs to be available.
                    </p>
                {:else}
                    <p class="text-lg text-gray-600 mb-6">
                        Please select a catalog from the dropdown menu to get started.
                    </p>
                    <div class="flex gap-4">
                        {#each availableCatalogs as catalog}
                            <button 
                                class="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
                                on:click={() => {
                                    currentCatalog = catalog;
                                    navigate(`/${catalog}`);
                                }}
                            >
                                {catalog}
                            </button>
                        {/each}
                    </div>
                {/if}
            </div>
        {:else}
            <Route path="/:table/product/:id/crawls" component={CrawlsView} />
            <Route path="/:table/product/:id" component={ProductView} />
            <Route path="/:table" component={ProductList} />
            <Route path="/" component={ProductList} />
        {/if}
    </main>
</Router> 