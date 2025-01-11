<script>
    import { createEventDispatcher } from 'svelte';
    const dispatch = createEventDispatcher();
    
    let catalogs = ['anntaylor', 'chairish', 'heydude'];
    $: currentCatalog = window.location.pathname.split('/')[1] || 'anntaylor';

    function switchCatalog(catalog) {
        dispatch('change', catalog);
    }
</script>

<select 
    bind:value={currentCatalog} 
    on:change={() => switchCatalog(currentCatalog)}
    class="block w-full rounded-md border-0 bg-gray-700 py-1.5 pl-3 pr-10 text-gray-300 focus:ring-2 focus:ring-white sm:text-sm sm:leading-6"
>
    {#each catalogs as catalog}
        <option value={catalog}>{catalog}</option>
    {/each}
</select>