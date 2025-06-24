<script>
    import { onMount, onDestroy, createEventDispatcher } from 'svelte';
    
    export let loading = false;
    export let hasMore = true;
    export let threshold = 200; // pixels from bottom to trigger loading
    
    const dispatch = createEventDispatcher();
    let observer;
    let loadingElement;
    
    function handleIntersection(entries) {
        const entry = entries[0];
        if (entry.isIntersecting && hasMore && !loading) {
            dispatch('loadMore');
        }
    }
    
    onMount(() => {
        observer = new IntersectionObserver(handleIntersection, {
            rootMargin: `0px 0px ${threshold}px 0px`
        });
        
        if (loadingElement) {
            observer.observe(loadingElement);
        }
    });
    
    onDestroy(() => {
        if (observer) {
            observer.disconnect();
        }
    });
</script>

<div>
    <slot />
    
    <div bind:this={loadingElement} class="mt-6 py-4 text-center">
        {#if loading}
            <div class="flex justify-center items-center">
                <svg class="animate-spin h-5 w-5 mr-3 text-indigo-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                    <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                <span>Loading more items...</span>
            </div>
        {:else if hasMore}
            <div class="h-8"></div>
        {:else}
            <div class="text-gray-500">No more items to load</div>
        {/if}
    </div>
</div> 