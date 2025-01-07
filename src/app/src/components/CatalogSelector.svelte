<script>
    let catalogs = ['anntaylor', 'chairish', 'heydude'];
    $: currentCatalog = window.location.pathname.split('/')[1] || 'anntaylor';

    function switchCatalog(catalog) {
        window.location.href = `/${catalog}`;
    }
</script>

<div class="mb-4">
    <select 
        bind:value={currentCatalog} 
        on:change={() => switchCatalog(currentCatalog)}
        class="px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
    >
        {#each catalogs as catalog}
            <option value={catalog}>{catalog}</option>
        {/each}
    </select>
</div>