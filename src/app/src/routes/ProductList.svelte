<script>
    import { onMount, onDestroy } from 'svelte';
    import SearchBar from '$components/SearchBar.svelte';
    import InfiniteScroll from '$components/InfiniteScroll.svelte';
    import ProductCard from '$components/ProductCard.svelte';
    import ProductCardSkeleton from '$components/ProductCardSkeleton.svelte';
    
    // Get table name from URL path
    $: tableName = window.location.pathname.split('/')[1] || 'anntaylor';
    
    let products = [];
    let searchQuery = '';
    let isSearchActive = false;
    let loading = true;
    let expandedProductId = null;
    let currentPage = 1;
    let totalPages = 1;
    let totalProducts = 0;
    let pageSize = 30;
    let errorMessage = '';
    let hasMoreItems = true;
    
    // Utility functions
    function toTitleCase(str) {
        if (!str) return '';
        return str
            .split(/[\s_-]+/)
            .map(word => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
            .join(' ');
    }
    
    function getProductUniqueId(product) {
        if (!product) return null;
        // Use the product's id if available, otherwise use a combination of name and other fields
        return product.id || `${product.name || 'unknown'}-${product.url || ''}`.replace(/[^a-zA-Z0-9-]/g, '-');
    }
    
    // Make loadProducts reactive to tableName changes
    $: {
        if (tableName) {
            resetResults();
            loadProducts(1);
        }
    }

    function resetResults() {
        products = [];
        currentPage = 1;
        hasMoreItems = true;
        expandedProductId = null;
    }

    async function loadProducts(page = 1, isNewQuery = false) {
        loading = true;
        
        try {
            let url;
            if (searchQuery && isSearchActive) {
                // Search query
                if (searchQuery.startsWith('filter:')) {
                    const [_, ...rest] = searchQuery.split(':');
                    const filter_string = rest.join(':');
                    url = `/api/${tableName}/filter?` + 
                        new URLSearchParams({
                            filter_string: filter_string,
                            page: page.toString(),
                            per_page: pageSize.toString()
                        });
                } else {
                    // Regular search query
                    url = `/api/${tableName}/search?query=${encodeURIComponent(searchQuery)}&page=${page}&per_page=${pageSize}`;
                }
            } else {
                // Default product list
                url = `/api/${tableName}/products?page=${page}&per_page=${pageSize}`;
            }
            
            const res = await fetch(url);
            
            if (!res.ok) {
                throw new Error('Failed to fetch products');
            }
            
            const data = await res.json();
            
            // If it's a new query, replace existing products
            if (isNewQuery) {
                products = data.products;
            } else {
                // Otherwise append to existing products
                products = [...products, ...data.products];
            }
            
            totalPages = data.total_pages;
            totalProducts = data.total;
            currentPage = data.page;
            hasMoreItems = currentPage < totalPages;
            
        } catch (error) {
            console.error('Error loading products:', error);
            errorMessage = error.message || 'An error occurred while loading products';
        } finally {
            loading = false;
        }
    }

    function parseHash() {
        const hash = window.location.hash.slice(1); // Remove the '#' character
        const params = new URLSearchParams(hash);
        
        const searchQuery = params.get('search') || null;
        // Don't extract product IDs from the URL hash
        
        return { searchQuery, expandedProductId: null };
    }

    function handleHashChange() {
        const { searchQuery: hashSearchQuery } = parseHash();

        if (hashSearchQuery !== null) {
            // Update searchQuery and initiate search
            searchQuery = hashSearchQuery;
            handleSearch({ type: 'hashchange' });
        } else {
            // Clear search if no search query in hash
            searchQuery = '';
            isSearchActive = false;
            resetResults();
            loadProducts(1, true);
        }
        
        // Don't update expanded product ID based on the hash
    }

    onMount(() => {
        // Handle initial hash if present
        handleHashChange();
        window.addEventListener('hashchange', handleHashChange);
    });
    
    onDestroy(() => {
        window.removeEventListener('hashchange', handleHashChange);
    });

    async function handleSearch(event) {
        if (event.type === 'keydown' && event.key !== 'Enter') {
            return;
        }
        
        if (!searchQuery.trim() || event.type === 'clear') {
            isSearchActive = false;
            // Remove search from the hash
            updateHash({ removeSearch: true });
            resetResults();
            loadProducts(1, true);
            return;
        }

        // Update the hash with the search query if this isn't triggered by a hash change
        if (event.type !== 'hashchange') {
            updateHash({ searchQuery });
        }
        
        // Reset and start a new search
        isSearchActive = true;
        resetResults();
        await loadProducts(1, true);
    }

    async function handleLoadMore() {
        if (!loading && hasMoreItems) {
            const nextPage = currentPage + 1;
            await loadProducts(nextPage);
        }
    }
  
    function handleToggleExpand(product) {
        const productId = getProductUniqueId(product);
        expandedProductId = expandedProductId === productId ? null : productId;
        
        // Don't update the URL hash when a product is expanded/collapsed
        // This prevents product URLs from appearing in the browser address bar
    }

    function updateHash({ searchQuery: newSearchQuery = null, removeSearch = false }) {
        const params = new URLSearchParams(window.location.hash.slice(1)); // Remove '#'

        if (removeSearch) {
            params.delete('search');
        } else if (newSearchQuery !== null) {
            params.set('search', newSearchQuery);
        }

        // Always remove any product parameter from the URL
        params.delete('product');

        // Update the hash without adding a new entry to the browser history
        const newHash = params.toString();
        history.replaceState(null, '', newHash ? '#' + newHash : window.location.pathname);
    }
</script>

<div class="max-w-7xl mx-auto">
    <h1 class="text-3xl font-bold mb-8">
        {toTitleCase(tableName)} Product Catalog
    </h1>
    
    <SearchBar
        bind:value={searchQuery}
        isLoading={loading && currentPage === 1}
        on:search={handleSearch}
        on:clear={() => {
            searchQuery = '';
            isSearchActive = false;
            resetResults();
            loadProducts(1, true);
            updateHash({ removeSearch: true });
        }}
    />

    <div class="mb-4 flex justify-between items-center">
        <div class="flex items-center gap-2">
            <h2 class="text-2xl font-semibold">
                {#if searchQuery && isSearchActive}
                    Search Results for "{searchQuery}"
                {:else}
                    All Products
                {/if}
            </h2>
        </div>
        <span class="text-gray-600">Total: {totalProducts} products</span>
    </div>

    {#if errorMessage}
        <div class="bg-red-100 border-l-4 border-red-500 text-red-700 p-4 mb-4" role="alert">
            <p>{errorMessage}</p>
        </div>
    {/if}

    <InfiniteScroll 
        loading={loading && currentPage > 1} 
        hasMore={hasMoreItems}
        on:loadMore={handleLoadMore}
    >
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {#if loading && products.length === 0}
                {#each Array(pageSize) as _}
                    <ProductCardSkeleton />
                {/each}
            {:else if products.length === 0 && !loading}
                <div class="col-span-3 text-center py-10">
                    <p class="text-gray-500 text-lg">No products found</p>
                </div>
            {:else}
                {#each products as product}
                    {@const productId = getProductUniqueId(product)}
                    <ProductCard
                        {product}
                        initialExpanded={expandedProductId === productId}
                        on:click={() => handleToggleExpand(product)}
                    />
                {/each}
            {/if}
        </div>
    </InfiniteScroll>
</div> 