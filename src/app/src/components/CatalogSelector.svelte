<script>
    import { createEventDispatcher, onMount } from 'svelte';
    const dispatch = createEventDispatcher();
    
    let catalogs = [];
    let loading = true;
    $: currentCatalog = window.location.pathname.split('/')[1] || 'anntaylor';

    onMount(async () => {
        try {
            const response = await fetch('/api/catalogs');
            const data = await response.json();
            catalogs = data.catalogs;
            loading = false;
        } catch (error) {
            console.error('Error fetching catalogs:', error);
            catalogs = ['anntaylor']; // Fallback to default
            loading = false;
        }
    });

    function switchCatalog(catalog) {
        dispatch('change', catalog);
    }
</script>

<select 
    bind:value={currentCatalog} 
    on:change={() => switchCatalog(currentCatalog)}
    class="block w-full rounded-md border-0 bg-gray-700 py-1.5 pl-3 pr-10 text-gray-300 focus:ring-2 focus:ring-white sm:text-sm sm:leading-6"
    disabled={loading}
>
    {#if loading}
        <option>Loading catalogs...</option>
    {:else}
        {#each catalogs as catalog}
            <option value={catalog}>{catalog}</option>
        {/each}
    {/if}
</select>