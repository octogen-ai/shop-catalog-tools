<script>
    import { createEventDispatcher, onMount } from 'svelte';
    const dispatch = createEventDispatcher();
    
    let catalogs = [];
    let loading = true;
    let statusMessage = '';
    
    $: currentCatalog = window.location.pathname.split('/')[1] || '';

    onMount(async () => {
        await fetchCatalogs();
    });
    
    async function fetchCatalogs() {
        try {
            const response = await fetch('/api/catalogs');
            const data = await response.json();
            catalogs = data.catalogs;
            loading = false;
            
            if (catalogs.length === 0) {
                statusMessage = 'No catalogs available. Please restart the application if you expect catalogs to be available.';
            }
        } catch (error) {
            console.error('Error fetching catalogs:', error);
            catalogs = [];
            loading = false;
            statusMessage = 'Error loading catalogs. Please check server logs.';
        }
    }

    function switchCatalog(catalog) {
        dispatch('change', catalog);
    }
</script>

<div class="flex flex-col gap-2">
    <div class="flex items-center gap-2">
        <select 
            bind:value={currentCatalog} 
            on:change={() => switchCatalog(currentCatalog)}
            class="block w-full rounded-md border-0 bg-gray-700 py-1.5 pl-3 pr-10 text-gray-300 focus:ring-2 focus:ring-white sm:text-sm sm:leading-6"
            disabled={loading}
        >
            {#if loading}
                <option>Loading catalogs...</option>
            {:else if catalogs.length === 0}
                <option value="">No catalogs available</option>
            {:else}
                {#each catalogs as catalog}
                    <option value={catalog}>{catalog}</option>
                {/each}
            {/if}
        </select>
    </div>
    
    {#if statusMessage}
        <div class="text-sm text-gray-300 mt-1">{statusMessage}</div>
    {/if}
</div>