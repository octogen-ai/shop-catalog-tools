<script>
    import { onMount } from 'svelte';
    import '$styles/product-viewer.css';
    import InteractiveDataView from '$components/InteractiveDataView.svelte';

    // Get parameters from URL using window.location
    $: {
        const pathParts = window.location.pathname.split('/');
        tableName = pathParts[1] || '';
    }
    
    let tableName;
    let crawlData = null;
    let format = 'json';
    let loading = true;
    let productUrl = null;

    // Get the product URL from the query parameters
    $: {
        const urlParams = new URLSearchParams(window.location.search);
        productUrl = urlParams.get('url');
    }

    async function loadCrawlData() {
        if (!tableName || !productUrl) {
            console.warn('Missing required parameters');
            return;
        }

        try {
            loading = true;
            const url = `/api/${tableName}/crawls?product_url=${encodeURIComponent(productUrl)}`;
            console.log('Fetching crawls from:', url);
            const response = await fetch(url);
            const data = await response.json();
            crawlData = data;
            console.log('Loaded crawl data:', crawlData);
        } catch (error) {
            console.error('Error loading crawl data:', error);
        } finally {
            loading = false;
        }
    }

    onMount(() => {
        loadCrawlData();
    });

    const formats = [
        { id: 'json', label: 'JSON' },
        { id: 'yaml', label: 'YAML' }
    ];

    function handleKeyClick(path) {
        console.log('Clicked path:', path);
    }
</script>

<div class="container mx-auto px-4 py-8">
    <div class="mb-4">
        <a href="../" class="text-blue-500 hover:text-blue-700">← Back to Product</a>
    </div>

    {#if loading}
        <p>Loading crawl data...</p>
    {:else if crawlData}
        <h1 class="text-2xl font-bold mb-4">Crawl History</h1>
        <p class="mb-4">Found {crawlData.crawl_count} crawls for this product</p>

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

        {#if format === 'json'}
            <InteractiveDataView 
                data={crawlData} 
                format="json"
                onKeyClick={handleKeyClick}
            />
        {:else if format === 'yaml'}
            <InteractiveDataView 
                data={crawlData} 
                format="yaml"
                onKeyClick={handleKeyClick}
            />
        {/if}
    {:else}
        <p>No crawl data available</p>
    {/if}
</div> 