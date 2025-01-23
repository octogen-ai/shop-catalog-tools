<script>
    import AnalyticsCard from '$components/AnalyticsCard.svelte';
    import { toTitleCase } from '$lib/utils.js';

    let analytics = null;
    let loading = true;
    let error = null;

    // Get table name from URL path
    $: tableName = window.location.pathname.split('/')[1] || 'anntaylor';

    async function loadAnalytics() {
        loading = true;
        error = null;

        try {
            const res = await fetch(`/api/${tableName}/analytics`);
            analytics = await res.json();

            if (analytics.error) {
                error = analytics.error;
            }
        } catch (e) {
            error = 'Failed to load analytics';
            console.error(e);
        } finally {
            loading = false;
        }
    }

    $: {
        if (tableName) {
            loadAnalytics();
        }
    }

    $: {
        if (analytics) {
            console.log('Analytics response:', analytics);
        }
    }
</script>

<main class="container mx-auto px-4 py-8">
    <div class="max-w-7xl mx-auto">
        <h1 class="text-3xl font-bold mb-8">{toTitleCase(tableName)} Analytics</h1>

        {#if loading}
            <div class="flex justify-center items-center h-64">
                <div class="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-500"></div>
            </div>
        {:else if error}
            <div class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative" role="alert">
                <strong class="font-bold">Error: </strong>
                <span class="block sm:inline">{error}</span>
                {#if analytics?.requires_duckdb}
                    <p class="mt-2">Analytics requires DuckDB database engine. Please configure your database settings accordingly by adding `DB_ENGINE=duckdb` to your .env file.</p>
                {/if}
            </div>
        {:else if analytics?.basic_analytics}
            <!-- Basic Analytics Cards -->
            <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
                <AnalyticsCard
                    title="Total Products"
                    value={analytics.basic_analytics.total_records}
                    type="number"
                />

                <AnalyticsCard
                    title="Unique Brands"
                    value={analytics.basic_analytics.unique_brands}
                    type="number"
                />

                <AnalyticsCard
                    title="Price Completeness"
                    value={analytics.basic_analytics.price_completeness}
                    type="percentage"
                />
            </div>

            <!-- Field Analysis -->
            <div class="bg-white rounded-lg shadow p-6 mb-8">
                <h2 class="text-xl font-semibold mb-4">Field Analysis</h2>
                <div class="overflow-x-auto">
                    <table class="min-w-full">
                        <thead>
                            <tr class="bg-gray-50">
                                <th class="px-6 py-3 text-left">Field</th>
                                <th class="px-6 py-3 text-left">Null %</th>
                                <th class="px-6 py-3 text-left">Unique Values</th>
                            </tr>
                        </thead>
                        <tbody>
                            {#if analytics.basic_analytics?.null_analysis && analytics.basic_analytics?.uniqueness_analysis}
                                {#each Object.keys(analytics.basic_analytics.null_analysis) as field}
                                    <tr class="border-t">
                                        <td class="px-6 py-4">{field}</td>
                                        <td class="px-6 py-4">
                                            {#if analytics.basic_analytics.null_analysis[field]?.null_percentage != null}
                                                {analytics.basic_analytics.null_analysis[field].null_percentage}%
                                            {:else}
                                                N/A
                                            {/if}
                                        </td>
                                        <td class="px-6 py-4">
                                            {#if analytics.basic_analytics.uniqueness_analysis[field]?.unique_values != null}
                                                {analytics.basic_analytics.uniqueness_analysis[field].unique_values}
                                            {:else}
                                                N/A
                                            {/if}
                                        </td>
                                    </tr>
                                {/each}
                            {/if}
                        </tbody>
                    </table>
                </div>
            </div>

            <!-- Rating Analysis -->
            {#if analytics.advanced_analytics?.rating_analysis?.statistics.avg_rating}
                <div class="bg-white rounded-lg shadow p-6 mb-8">
                    <h2 class="text-xl font-semibold mb-4">Rating Analysis</h2>
                    <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                        <div>
                            <table class="min-w-full">
                                <tbody>
                                    {#each Object.entries(analytics.advanced_analytics.rating_analysis.statistics) as [metric, value]}
                                        <tr class="border-t">
                                            <td class="px-4 py-2 font-medium">{metric.replace(/_/g, ' ')}</td>
                                            <td class="px-4 py-2">{value != null ? value : 'N/A'}</td>
                                        </tr>
                                    {/each}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            {/if}

            <!-- Brand Analysis -->
            {#if analytics.advanced_analytics?.brand_analysis?.top_brands}
                <div class="bg-white rounded-lg shadow p-6 mb-8">
                    <h2 class="text-xl font-semibold mb-4">Top Brands Analysis</h2>
                    <div class="overflow-x-auto">
                        <table class="min-w-full">
                            <thead>
                                <tr class="bg-gray-50">
                                    <th class="px-4 py-2 text-left">Brand</th>
                                    <th class="px-4 py-2 text-left">Products</th>
                                    <th class="px-4 py-2 text-left">Price Range</th>
                                    <th class="px-4 py-2 text-left">Avg Rating</th>
                                </tr>
                            </thead>
                            <tbody>
                                {#each analytics.advanced_analytics.brand_analysis.top_brands as brand}
                                    <tr class="border-t">
                                        <td class="px-4 py-2">{brand.name}</td>
                                        <td class="px-4 py-2">{brand.product_count}</td>
                                        <td class="px-4 py-2">${brand.min_price} - ${brand.max_price}</td>
                                        <td class="px-4 py-2">{brand.avg_rating ?? 'N/A'}</td>
                                    </tr>
                                {/each}
                            </tbody>
                        </table>
                    </div>
                </div>
            {/if}
        {/if}
    </div>
</main>