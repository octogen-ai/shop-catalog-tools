<script>
    import { onMount } from 'svelte';
    import SvelteJSONTree from 'svelte-json-tree';
    import '$styles/product-viewer.css';
    import InteractiveDataView from '$components/InteractiveDataView.svelte';

    // Get parameters from URL using window.location
    $: {
        const pathParts = window.location.pathname.split('/');
        tableName = pathParts[1] || '';
        productId = pathParts[3] || '';
    }
    
    let tableName;
    let productId;
    let productData = null;
    let format = 'tree';
    let loading = true;

    async function loadProductData() {
        if (!tableName || !productId) {
            console.warn('Missing required parameters');
            return;
        }

        try {
            loading = true;
            const url = `/api/${tableName}/product/${productId}/data`;
            console.log('Fetching from:', url);
            const response = await fetch(url);
            const data = await response.json();
            productData = data;
            console.log('Loaded product data:', productData); // Debug log
        } catch (error) {
            console.error('Error loading product data:', error);
        } finally {
            loading = false;
        }
    }

    onMount(() => {
        loadProductData();
    });

    // Debug reactive statement
    $: console.log('Current format:', format, 'Product data:', productData);

    const formats = [
        { id: 'tree', label: 'Tree View' },
        { id: 'json', label: 'JSON' },
        { id: 'yaml', label: 'YAML' }
    ];

    function handleKeyClick(path) {
        console.log('Clicked path:', path);
        // Here you can implement any action you want when a key is clicked
        // For example, copying to clipboard or navigating to a specific view
    }
</script>

<div class="container mx-auto px-4 py-8">
    {#if loading}
        <p>Loading...</p>
    {:else if productData}
        <div class="mb-4 flex space-x-2">
            {#each formats as { id, label }}
                <button
                    class="format-button {format === id ? 'active' : 'bg-gray-800 text-gray-300'}"
                    on:click={() => format = id}
                >
                    {label}
                </button>
            {/each}
        </div>

        {#if format === 'tree'}
            <div id="json-tree" class="bg-[#272822] p-4 rounded">
                <SvelteJSONTree 
                    value={productData}
                />
            </div>
        {:else if format === 'json'}
            <InteractiveDataView 
                data={productData} 
                format="json"
                onKeyClick={handleKeyClick}
            />
        {:else if format === 'yaml'}
            <InteractiveDataView 
                data={productData} 
                format="yaml"
                onKeyClick={handleKeyClick}
            />
        {/if}
    {:else}
        <p>Product not found</p>
    {/if}
</div>
