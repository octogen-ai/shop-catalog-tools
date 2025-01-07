<script>
    import { onMount } from 'svelte';
    import ProductCard from './components/ProductCard.svelte';
    
    let products = [];
    let searchQuery = '';
    let searchResults = [];
    let loading = true;
    let searching = false;
    let expandedProductId = null;
  
    onMount(async () => {
      const res = await fetch('/api/products');
      products = await res.json();
      loading = false;
    });
  
    async function search() {
      if (!searchQuery.trim()) {
        searchResults = [];
        return;
      }
      searching = true;
      const res = await fetch(`/api/search?query=${encodeURIComponent(searchQuery)}`);
      searchResults = await res.json();
      searching = false;
    }
  
    function handleToggleExpand(product) {
      expandedProductId = expandedProductId === product.id ? null : product.id;
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
          <h2 class="text-2xl font-semibold mb-4">Search Results</h2>
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
  
      <h2 class="text-2xl font-semibold mb-4">All Products</h2>
      {#if loading}
        <p class="text-gray-600">Loading products...</p>
      {:else}
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {#each products as product}
            <ProductCard 
              {product} 
              expanded={expandedProductId === product.id}
              onToggleExpand={handleToggleExpand}
            />
          {/each}
        </div>
      {/if}
    </div>
  </main>
  
  <style>
    :global(html) {
      background-color: #f9fafb;
    }
  </style>