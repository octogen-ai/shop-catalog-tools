<script>
    import { onMount, onDestroy } from 'svelte';
    import ProductGrid from '$components/ProductGrid.svelte';
    import SearchBar from '$components/SearchBar.svelte';
    import { toTitleCase } from '$lib/utils.js';
    
    // Get table name from URL path
    $: tableName = window.location.pathname.split('/')[1] || 'anntaylor';
    
    let products = [];
    let searchQuery = '';
    let searchResults = [];
    let loading = true;
    let searching = false;
    let expandedProductIdSearch = null;
    let expandedProductIdAll = null;
    let currentPage = 1;
    let totalPages = 1;
    let searchCurrentPage = 1;
    let searchTotalPages = 1;
    let totalProducts = 0;
    let perListPage = 30;
    let perSearchPage = 9;
    let pageSizeOptions = [100, 200, 300, 400];
    let totalSearchResults = 0;
    let searchAttempted = false;
    let isLoadingProducts = false;
    let isLoadingSearch = false;
    let errorMessage = '';

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

    function parseHash() {
        const hash = window.location.hash.slice(1); // Remove the '#' character
        const params = new URLSearchParams(hash);
        
        const searchQuery = params.get('search') || null;
        const expandedProductId = params.get('product') || null;
        
        return { searchQuery, expandedProductId };
    }

    function handleHashChange() {
        const { searchQuery: hashSearchQuery, expandedProductId: hashExpandedProductId } = parseHash();

        if (hashSearchQuery !== null) {
            // Update searchQuery and initiate search
            searchQuery = hashSearchQuery;
            handleSearch({ type: 'hashchange' });
        } else {
            // Clear search if no search query in hash
            searchQuery = '';
            searchResults = [];
            searchAttempted = false;
        }

        // Update expanded product IDs based on the hash
        if (hashExpandedProductId) {
            if (searchQuery) {
                // If there's a search, expand in search results
                expandedProductIdSearch = hashExpandedProductId;
                expandedProductIdAll = null;
            } else {
                // Expand in all products
                expandedProductIdAll = hashExpandedProductId;
                expandedProductIdSearch = null;
            }
        } else {
            // No product expanded
            expandedProductIdSearch = null;
            expandedProductIdAll = null;
        }
    }

    onMount(() => {
        // Handle initial hash if present
        handleHashChange();
        window.addEventListener('hashchange', handleHashChange);
        return () => window.removeEventListener('hashchange', handleHashChange);
    });

    async function handleSearch(event, page = 1) {
        if (event.type === 'keydown' && event.key !== 'Enter') {
            return;
        }
        
        if (!searchQuery.trim()) {
            searchResults = [];
            searchAttempted = false;
            // Remove 'search' and 'product' from the hash
            updateHash({ removeSearch: true, removeProduct: true });
            return;
        }

        isLoadingSearch = true;
        errorMessage = ''; // Clear any previous error

        try {
            // Check if this is a filter query
            if (searchQuery.startsWith('filter:')) {
                const [_, ...rest] = searchQuery.split(':');
                const filter_string = rest.join(':');
                const res = await fetch(
                    `/api/${tableName}/filter?` + 
                    new URLSearchParams({
                        filter_string: filter_string,
                        page: page.toString(),
                        per_page: perSearchPage.toString()
                    })
                );
                
                if (!res.ok) {
                    const error = await res.json();
                    throw new Error(error.detail || 'Failed to filter products');
                }

                const data = await res.json();
                searchResults = data.products;
                totalSearchResults = data.total;
                searchTotalPages = data.total_pages;
                searchCurrentPage = data.page;
            } else {
                // Regular search query
                const res = await fetch(
                    `/api/${tableName}/search?query=${encodeURIComponent(searchQuery)}&page=${page}&per_page=${perSearchPage}`
                );
                const data = await res.json();
                searchResults = data.products;
                totalSearchResults = data.total;
                searchTotalPages = data.total_pages;
                searchCurrentPage = data.page;
            }
        } catch (error) {
            console.error('Search error:', error);
            errorMessage = error.message || 'An error occurred while searching';
            searchResults = [];
            totalSearchResults = 0;
            searchTotalPages = 0;
        }
        
        // Update the hash with the search query
        if (event.type !== 'hashchange') {
            updateHash({ searchQuery });
        }
        isLoadingSearch = false;
        searchAttempted = true;
    }

    async function handleSearchPageChange(event) {
        const newPage = event.detail;
        await handleSearch({ type: 'click' }, newPage);
        window.scrollTo({ top: 0, behavior: 'smooth' });
    }
  
    function handleToggleExpand(product, gridType) {
        const productId = product.id;
        if (gridType === 'search') {
            expandedProductIdSearch = expandedProductIdSearch === productId ? null : productId;
            expandedProductIdAll = null; // Ensure only one is expanded
        } else {
            expandedProductIdAll = expandedProductIdAll === productId ? null : productId;
            expandedProductIdSearch = null;
        }

        // Update the hash with the expanded product ID
        if (expandedProductIdSearch || expandedProductIdAll) {
            updateHash({ expandedProductId: productId });
        } else {
            updateHash({ removeProduct: true });
        }
    }

    function updateHash({ searchQuery: newSearchQuery = null, expandedProductId: newExpandedProductId = null, removeSearch = false, removeProduct = false }) {
        const params = new URLSearchParams(window.location.hash.slice(1)); // Remove '#'

        if (removeSearch) {
            params.delete('search');
        } else if (newSearchQuery !== null) {
            params.set('search', newSearchQuery);
        }

        if (removeProduct) {
            params.delete('product');
        } else if (newExpandedProductId !== null) {
            params.set('product', newExpandedProductId);
        }

        // Update the hash without adding a new entry to the browser history
        const newHash = params.toString();
        history.replaceState(null, '', newHash ? '#' + newHash : window.location.pathname);
    }

    async function handlePageSizeChange(event) {
        perListPage = event.detail;
        await loadProducts(1);
    }
</script>

<div class="max-w-7xl mx-auto">
    <h1 class="text-3xl font-bold mb-8">
        {toTitleCase(tableName)} Product Catalog
    </h1>
    
    <SearchBar
        bind:value={searchQuery}
        isLoading={isLoadingSearch}
        on:search={handleSearch}
    />

    {#if searchQuery && (searchResults.length > 0 || isLoadingSearch)}
        <!-- Search results section -->
        <ProductGrid
        products={searchResults}
        isLoading={isLoadingSearch}
        itemsPerPage={perSearchPage}
        currentPage={searchCurrentPage}
        totalPages={searchTotalPages}
        totalItems={totalSearchResults}
        title="Search Results"
        bind:expandedProductId={expandedProductIdSearch}
        on:pageChange={handleSearchPageChange}
        on:toggleExpand={(event) => handleToggleExpand(event.detail.product, 'search')}
        showPageSizeSelector={false}
    />
    {:else if searching}
        <p class="text-gray-600 mb-8">Searching...</p>
    {:else if searchAttempted && searchQuery}
        <p class="text-gray-600 mb-8">No results found for "{searchQuery}"</p>
    {/if}

    {#if errorMessage}
        <div class="bg-red-50 border-l-4 border-red-400 p-4 mb-8">
            <div class="flex">
                <div class="flex-shrink-0">
                    <svg class="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                        <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd" />
                    </svg>
                </div>
                <div class="ml-3">
                    <p class="text-sm text-red-700">
                        {errorMessage}
                    </p>
                </div>
            </div>
        </div>
    {/if}

    <ProductGrid
        products={products}
        isLoading={isLoadingProducts}
        itemsPerPage={perListPage}
        currentPage={currentPage}
        {totalPages}
        totalItems={totalProducts}
        title="All Products"
        bind:expandedProductId={expandedProductIdAll}
        on:pageChange={handlePageChange}
        on:toggleExpand={(event) => handleToggleExpand(event.detail.product, 'all')}
        on:pageSizeChange={(e) => handlePageSizeChange(e)}
        pageSizeOptions={[100, 200, 300, 400]}
    />
</div> 