<script>
    import { createEventDispatcher } from 'svelte';
    
    export let currentPage = 1;
    export let totalPages = 1;
    
    const dispatch = createEventDispatcher();
    
    function changePage(page) {
        if (page >= 1 && page <= totalPages) {
            dispatch('pageChange', page);
        }
    }
    
    $: pages = Array.from({ length: totalPages }, (_, i) => i + 1);
    $: visiblePages = pages.filter(page => {
        if (totalPages <= 7) return true;
        if (page === 1 || page === totalPages) return true;
        if (page >= currentPage - 1 && page <= currentPage + 1) return true;
        return false;
    });
</script>

<div class="flex justify-center items-center gap-2">
    <button
        class="px-3 py-1 rounded-lg border {currentPage === 1 ? 'bg-gray-100 text-gray-400' : 'hover:bg-gray-100'}"
        on:click={() => changePage(currentPage - 1)}
        disabled={currentPage === 1}
    >
        Previous
    </button>
    
    {#each visiblePages as page, i}
        {#if i > 0 && page - visiblePages[i - 1] > 1}
            <span class="px-2">...</span>
        {/if}
        <button
            class="px-3 py-1 rounded-lg border {currentPage === page ? 'bg-blue-500 text-white' : 'hover:bg-gray-100'}"
            on:click={() => changePage(page)}
        >
            {page}
        </button>
    {/each}
    
    <button
        class="px-3 py-1 rounded-lg border {currentPage === totalPages ? 'bg-gray-100 text-gray-400' : 'hover:bg-gray-100'}"
        on:click={() => changePage(currentPage + 1)}
        disabled={currentPage === totalPages}
    >
        Next
    </button>
</div> 