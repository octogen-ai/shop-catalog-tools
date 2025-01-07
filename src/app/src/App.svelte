<script>
    import { onMount } from 'svelte';
    import ProductCard from './components/ProductCard.svelte';
    import Pagination from './components/Pagination.svelte';
    
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

    async function loadProducts(page = 1) {
        loading = true;
        const res = await fetch(`/api/products?page=${page}&per_page=${perPage}`);
        const data = await res.json();
        products = data.products;
        totalPages = data.total_pages;
        totalProducts = data.total;
        currentPage = data.page;
        loading = false;
    }

    onMount(() => {
        loadProducts();
    });

    async function handlePageChange(event) {
        const newPage = event.detail;
        await loadProducts(newPage);
        window.scrollTo({ top: 0, behavior: 'smooth' });
    }

    async function search() {
      if (!searchQuery.trim()) {
        searchResults = [];
        return;
      }
      searching = true;
      const res = await fetch(`/api/search?query=${encodeURIComponent(searchQuery)}`);
      const data = await res.json();
      searchResults = data.products;
      totalSearchResults = data.total;
      searching = false;
    }
  
    function handleToggleExpand(product) {
      expandedProductId = expandedProductId === product.id ? null : product.id;
    }

    async function handlePageSizeChange(event) {
        perPage = parseInt(event.target.value);
        await loadProducts(1); // Reset to first page when changing page size
    }
  </script>
  
  <main class="container mx-auto px-4 py-8">
    <div class="max-w-7xl mx-auto">
      <h1 class="text-3xl font-bold mb-8">Product Catalog</h1>
      
      <div class="mb-8">
        <div class="flex gap-2">
          <input
            type="text"
            bind:value={searchQuery}
            placeholder="Search products..."
            class="flex-1 px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <button
            on:click={search}
            class="px-6 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 focus:outline-none focus:ring-2 focus:ring-blue-500"
            disabled={searching}
          >
            {searching ? 'Searching...' : 'Search'}
          </button>
        </div>
      </div>
  
      {#if searchQuery && searchResults.length > 0}
        <div class="mb-8">
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
      {:else if searchQuery}
        <p class="text-gray-600 mb-8">No results found for "{searchQuery}"</p>
      {/if}
  
      <div class="flex justify-between items-center mb-4">
        <h2 class="text-2xl font-semibold">All Products</h2>
        <span class="text-gray-600">Total: {totalProducts} products</span>
      </div>
      {#if loading}
        <p class="text-gray-600">Loading products...</p>
      {:else}
        <div class="mb-6">
            <Pagination 
                {currentPage}
                {totalPages}
                on:pageChange={handlePageChange}
            />
        </div>

        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {#each products as product}
                <ProductCard 
                    {product} 
                    expanded={expandedProductId === product.id}
                    onToggleExpand={handleToggleExpand}
                />
            {/each}
        </div>

        <div class="mt-6">
            <Pagination 
                {currentPage}
                {totalPages}
                on:pageChange={handlePageChange}
            />
        </div>
      {/if}

      <div class="flex justify-end mb-4">
        <select 
            value={perPage} 
            on:change={handlePageSizeChange}
            class="px-3 py-1 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
            {#each pageSizeOptions as size}
                <option value={size}>{size} per page</option>
            {/each}
        </select>
      </div>
    </div>
  </main>
  
  <style>
    :global(html) {
      background-color: #f9fafb;
    }
  </style>