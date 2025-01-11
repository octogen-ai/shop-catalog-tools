<script>
    import { onMount } from 'svelte';
    import ProductCard from '../../components/ProductCard.svelte';
    import Pagination from '../../components/Pagination.svelte';
    import ProductCardSkeleton from '../../components/ProductCardSkeleton.svelte';
    
    // Get table name from URL path, similar to ProductList.svelte
    $: tableName = window.location.pathname.split('/')[1] || 'anntaylor';
    
    let products = [];
    let searchQuery = '';
    let searchResults = [];
    let loading = true;
    let searching = false;
    let expandedProductId = null;
    let currentPage = 1;
    let totalPages = 1;
    let totalProducts = 0;
    let perPage = 100;
    let pageSizeOptions = [100, 200, 300, 400];
    let totalSearchResults = 0;

    async function loadProducts() {
        loading = true;
        try {
            const response = await fetch(`/api/${tableName}/products?page=${currentPage}&per_page=${perPage}`);
            const data = await response.json();
            products = data.products;
            totalPages = data.total_pages;
            totalProducts = data.total_products;
        } catch (error) {
            console.error('Error loading products:', error);
        }
        loading = false;
    }

    async function handleSearch() {
        if (!searchQuery.trim()) return;
        
        searching = true;
        try {
            const response = await fetch(`/api/${tableName}/search?q=${encodeURIComponent(searchQuery)}`);
            const data = await response.json();
            searchResults = data.products;
            totalSearchResults = data.total_products;
        } catch (error) {
            console.error('Error searching products:', error);
        }
        searching = false;
    }

    function handleToggleExpand(productId) {
        expandedProductId = expandedProductId === productId ? null : productId;
    }

    onMount(() => {
        loadProducts();
    });

    $: {
        tableName;
        currentPage;
        perPage;
        loadProducts();
    }
</script>

<div class="space-y-8">
    <!-- Search Bar -->
    <div class="flex gap-4">
        <input
            type="text"
            bind:value={searchQuery}
            placeholder="Search products..."
            class="flex-1 px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
        <button
            on:click={handleSearch}
            class="px-6 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
            Search
        </button>
    </div>

    <!-- Product Grid -->
    {#if !searchQuery}
        <div>
            <div class="flex justify-between items-center mb-4">
                <h2 class="text-2xl font-semibold">All Products</h2>
                <span class="text-gray-600">{totalProducts} products</span>
            </div>
            
            <!-- Page Size Selector -->
            <div class="mb-4">
                <label class="mr-2">Items per page:</label>
                <select 
                    bind:value={perPage}
                    class="px-2 py-1 border rounded"
                >
                    {#each pageSizeOptions as size}
                        <option value={size}>{size}</option>
                    {/each}
                </select>
            </div>

            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {#if loading}
                    {#each Array(perPage) as _}
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
                    {currentPage}
                    {totalPages}
                    on:pageChange={(e) => currentPage = e.detail}
                />
            </div>
        </div>
    {:else if searchResults.length > 0}
        <div>
            <div class="flex justify-between items-center mb-4">
                <h2 class="text-2xl font-semibold">Search Results</h2>
                <span class="text-gray-600">Found {totalSearchResults} products</span>
            </div>
            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {#each searchResults as product}
                    <ProductCard 
                        {product} 
                        expanded={expandedProductId === product.id}
                        onToggleExpand={handleToggleExpand}
                    />
                {/each}
            </div>
        </div>
    {:else if searching}
        <p class="text-gray-600">Searching...</p>
    {:else}
        <p class="text-gray-600">No results found for "{searchQuery}"</p>
    {/if}
</div> 