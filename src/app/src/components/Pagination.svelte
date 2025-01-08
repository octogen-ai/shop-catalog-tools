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

<nav class="flex items-center justify-between border-t border-gray-200 px-4 sm:px-0">
  <div class="-mt-px flex w-0 flex-1">
    <button
      class="inline-flex items-center border-t-2 border-transparent pr-1 pt-4 text-sm font-medium text-gray-500 hover:border-gray-300 hover:text-gray-700"
      on:click={() => changePage(currentPage - 1)}
      disabled={currentPage === 1 || totalPages === 1}
    >
      <svg class="mr-3 size-5 text-gray-400" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
        <path fill-rule="evenodd" d="M18 10a.75.75 0 0 1-.75.75H4.66l2.1 1.95a.75.75 0 1 1-1.02 1.1l-3.5-3.25a.75.75 0 0 1 0-1.1l3.5-3.25a.75.75 0 1 1 1.02 1.1l-2.1 1.95h12.59A.75.75 0 0 1 18 10Z" clip-rule="evenodd" />
      </svg>
      Previous
    </button>
  </div>

  <div class="hidden md:-mt-px md:flex">
    {#each visiblePages as page, i}
      {#if i > 0 && page - visiblePages[i - 1] > 1}
        <span class="inline-flex items-center border-t-2 border-transparent px-4 pt-4 text-sm font-medium text-gray-500">...</span>
      {/if}
      <button
        class="inline-flex items-center border-t-2 {currentPage === page ? 'border-indigo-500 text-indigo-600' : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'} px-4 pt-4 text-sm font-medium"
        on:click={() => changePage(page)}
        aria-current={currentPage === page ? 'page' : undefined}
      >
        {page}
      </button>
    {/each}
  </div>

  <div class="-mt-px flex w-0 flex-1 justify-end">
    <button
      class="inline-flex items-center border-t-2 border-transparent pl-1 pt-4 text-sm font-medium text-gray-500 hover:border-gray-300 hover:text-gray-700"
      on:click={() => changePage(currentPage + 1)}
      disabled={currentPage === totalPages || totalPages === 1}
    >
      Next
      <svg class="ml-3 size-5 text-gray-400" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
        <path fill-rule="evenodd" d="M2 10a.75.75 0 0 1 .75-.75h12.59l-2.1-1.95a.75.75 0 1 1 1.02-1.1l3.5 3.25a.75.75 0 0 1 0 1.1l-3.5 3.25a.75.75 0 1 1-1.02-1.1l2.1-1.95H2.75A.75.75 0 0 1 2 10Z" clip-rule="evenodd" />
      </svg>
    </button>
  </div>
</nav> 