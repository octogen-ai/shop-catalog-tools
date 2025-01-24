<script>
    import ProductCard from './ProductCard.svelte';
    import ProductCardSkeleton from './ProductCardSkeleton.svelte';
    import Pagination from './Pagination.svelte';
    import { getProductUniqueId } from '$lib/utils.js';

    export let products = [];
    export let isLoading = false;
    export let itemsPerPage = 10;
    export let currentPage = 1;
    export let totalPages = 1;
    export let totalItems = 0;
    export let title = '';
    export let expandedProductId = null;
    export let pageSizeOptions = [30, 60, 90, 120];
    export let showPageSizeSelector = true;

    import { createEventDispatcher } from 'svelte';
    const dispatch = createEventDispatcher();

    function handleToggleExpand(product) {
        const productId = getProductUniqueId(product);
        expandedProductId = expandedProductId === productId ? null : productId;
        dispatch('toggleExpand', { product });
    }

    function handlePageSizeChange(event) {
        dispatch('pageSizeChange', parseInt(event.target.value));
    }
</script>

<div>
    <div class="flex justify-between items-center mb-4">
        <h2 class="text-2xl font-semibold">{title}</h2>
        <div class="flex items-center gap-4">
            {#if showPageSizeSelector}
                <div class="flex items-center gap-2">
                    <label class="text-sm text-gray-600" for="itemsPerPageSelect">Items per page:</label>
                    <select 
                        id="itemsPerPageSelect"
                        value={itemsPerPage} 
                        on:change={handlePageSizeChange}
                        class="border rounded p-1 text-sm"
                    >
                        {#each pageSizeOptions as size}
                            <option value={size}>{size}</option>
                        {/each}
                    </select>
                </div>
            {/if}
            <span class="text-gray-600">Total: {totalItems} products</span>
        </div>
    </div>

    <div class="mb-6">
        <Pagination 
            {currentPage}
            {totalPages}
            on:pageChange
        />
    </div>

    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {#if isLoading}
            {#each Array(itemsPerPage) as _}
                <ProductCardSkeleton />
            {/each}
        {:else}
            {#each products as product}
                <ProductCard
                    {product}
                    expanded={getProductUniqueId(product) === expandedProductId}
                    on:toggleExpand={() => handleToggleExpand(product)}
                />
            {/each}
        {/if}
    </div>

    <div class="mt-6">
        <Pagination 
            {currentPage}
            {totalPages}
            on:pageChange
        />
    </div>
</div> 