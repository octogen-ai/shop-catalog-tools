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
        const hash = window.location.hash.slice(1); // Remove the # character
        const parts = hash.split(':');
        if (parts[0] === 'search' && parts.length > 1) {
            // Rejoin the rest of parts in case the search query itself contains colons
            return decodeURIComponent(parts.slice(1).join(':'));
        }
        return null;
    }

    function handleHashChange() {
        const hash = decodeURIComponent(window.location.hash.slice(1));
        if (hash) {
            searchQuery = hash;
            handleSearch({ type: 'hashchange' });
        } else {
            searchQuery = '';
            searchResults = [];
            searchAttempted = false;
        }
    }

    onMount(() => {
        // Handle initial hash if present
        if (window.location.hash) {
            handleHashChange();
        }
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
            window.location.hash = '';
            return;
        }

        isLoadingSearch = true;
        errorMessage = ''; // Clear any previous error
        window.removeEventListener('hashchange', handleHashChange);
        
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
        
        if (event.type !== 'hashchange') {
            window.location.hash = encodeURIComponent(searchQuery);
        }
        window.addEventListener('hashchange', handleHashChange);
        isLoadingSearch = false;
        searchAttempted = true;
    }

    async function handleSearchPageChange(event) {
        const newPage = event.detail;
        await handleSearch({ type: 'click' }, newPage);
        window.scrollTo({ top: 0, behavior: 'smooth' });
    }
  
    function handleToggleExpand(product, gridType) {
        if (gridType === 'search') {
            expandedProductIdSearch = expandedProductIdSearch === product.id ? null : product.id;
        } else {
            expandedProductIdAll = expandedProductIdAll === product.id ? null : product.id;
        }
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
        on:toggleExpand={(event) => handleToggleExpand(event.detail, 'search')}
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
        on:toggleExpand={(event) => handleToggleExpand(event.detail, 'all')}
        on:pageSizeChange={(e) => handlePageSizeChange(e)}
        pageSizeOptions={[100, 200, 300, 400]}
    />
</div> 