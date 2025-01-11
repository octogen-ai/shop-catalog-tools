<script>
    import { onMount } from 'svelte';
    import ProductCard from '../components/ProductCard.svelte';
    import Pagination from '../components/Pagination.svelte';
    import CatalogSelector from '../components/CatalogSelector.svelte';
    import ProductCardSkeleton from '../components/ProductCardSkeleton.svelte';
    import { toTitleCase } from '../utils.js';
    
    // Get table name from URL path
    $: tableName = window.location.pathname.split('/')[1] || 'anntaylor';
    
    let products = [];
    let searchQuery = '';
    let searchResults = [];
    let loading = true;
    let searching = false;
    let expandedProductId = null;
    let currentPage = 1;
    let totalPages = 1;
    let searchCurrentPage = 1;
    let searchTotalPages = 1;
    let totalProducts = 0;
    let perListPage = 100;
    let perSearchPage = 9;
    let pageSizeOptions = [100, 200, 300, 400];
    let totalSearchResults = 0;
    let searchAttempted = false;
    let isLoadingProducts = false;
    let isLoadingSearch = false;

    // Make loadProducts reactive to tableName changes
    $: {
        if (tableName) {
            loadProducts(1);
        }
    }

    async function loadProducts(page = 1) {
        isLoadingProducts = true;
        const res = await fetch(`/api/${tableName}/products?page=${page}&per_page=${perListPage}`);
        const data = await res.json();
        products = data.products;
        totalPages = data.total_pages;
        totalProducts = data.total;
        currentPage = data.page;
        isLoadingProducts = false;
    }

    async function handlePageChange(event) {
        const newPage = event.detail;
        await loadProducts(newPage);
    }

    async function handleSearch(event, page = 1) {
        if (event.type === 'keydown' && event.key !== 'Enter') {
            return;
        }
        
        if (!searchQuery.trim()) {
            searchResults = [];
            searchAttempted = false;
            return;
        }
        isLoadingSearch = true;
        const res = await fetch(`/api/${tableName}/search?query=${encodeURIComponent(searchQuery)}&page=${page}&per_page=${perSearchPage}`);
        const data = await res.json();
        searchResults = data.products;
        totalSearchResults = data.total;
        searchTotalPages = data.total_pages;
        searchCurrentPage = data.page;
        isLoadingSearch = false;
        searchAttempted = true;
    }

    async function handleSearchPageChange(event) {
        const newPage = event.detail;
        await handleSearch({ type: 'click' }, newPage);
        window.scrollTo({ top: 0, behavior: 'smooth' });
    }
  
    function handleToggleExpand(product) {
        expandedProductId = expandedProductId === product.id ? null : product.id;
    }

    async function handlePageSizeChange(event) {
        perListPage = parseInt(event.target.value);
        await loadProducts(1);
    }
</script>

<div class="max-w-7xl mx-auto">
    <h1 class="text-3xl font-bold mb-8">
        {toTitleCase(tableName)} Product Catalog
    </h1>
    
    <div class="mb-8">
        <div class="flex gap-2">
            <input
                type="text"
                bind:value={searchQuery}
                placeholder="Search products..."
                class="flex-1 px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                on:keydown={handleSearch}
            />
            <button
                on:click={handleSearch}
                class="px-6 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 focus:outline-none focus:ring-2 focus:ring-blue-500"
                disabled={searching}
            >
                {searching ? 'Searching...' : 'Search'}
            </button>
        </div>
    </div>

    {#if searchQuery && (searchResults.length > 0 || isLoadingSearch)}
        <!-- Search results section -->
        <div class="mb-8">
            <div class="mt-6">
                <Pagination 
                    currentPage={searchCurrentPage}
                    totalPages={searchTotalPages}
                    on:pageChange={handleSearchPageChange}
                />
            </div>
            <div class="flex justify-between items-center mb-4">
                <h2 class="text-2xl font-semibold">Search Results</h2>
                <span class="text-gray-600">Found {totalSearchResults} products</span>
            </div>
            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {#if isLoadingSearch}
                    {#each Array(perSearchPage) as _}
                        <ProductCardSkeleton />
                    {/each}
                {:else}
                    {#each searchResults as product}
                        <ProductCard 
                            {product} 
                            expanded={expandedProductId === product.id}
                            onToggleExpand={handleToggleExpand}
                        />
                    {/each}
                {/if}
            </div>
            <div class="mt-6">
                <Pagination 
                    currentPage={searchCurrentPage}
                    totalPages={searchTotalPages}
                    on:pageChange={handleSearchPageChange}
                />
            </div>
        </div>
    {:else if searching}
        <p class="text-gray-600 mb-8">Searching...</p>
    {:else if searchAttempted && searchQuery}
        <p class="text-gray-600 mb-8">No results found for "{searchQuery}"</p>
    {/if}

    <!-- All products section -->
    <div class="flex justify-between items-center mb-4">
        <h2 class="text-2xl font-semibold">All Products</h2>
        <span class="text-gray-600">Total: {totalProducts} products</span>
    </div>

    <div class="mb-6">
        <Pagination 
            currentPage={currentPage}
            totalPages={totalPages}
            on:pageChange={handlePageChange}
        />
    </div>

    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {#if isLoadingProducts}
            {#each Array(perListPage) as _}
                <ProductCardSkeleton />
            {/each}
        {:else}
            {#each products as product}
                <ProductCard 
                    {product} 
                    expanded={expandedProductId === product.id}
                    onToggleExpand={handleToggleExpand}
                />
            {/each}
        {/if}
    </div>

    <div class="mt-6">
        <Pagination 
            currentPage={currentPage}
            totalPages={totalPages}
            on:pageChange={handlePageChange}
        />
    </div>

    <div class="flex justify-end mb-4">
        <select 
            value={perListPage} 
            on:change={handlePageSizeChange}
            class="px-3 py-1 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
            {#each pageSizeOptions as size}
                <option value={size}>{size} per page</option>
            {/each}
        </select>
    </div>
</div> 