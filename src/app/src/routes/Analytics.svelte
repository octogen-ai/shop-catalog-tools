<script>
    import { onMount } from 'svelte';
    import AnalyticsCard from '../components/AnalyticsCard.svelte';
    import CatalogSelector from '../components/CatalogSelector.svelte';
    import { Chart } from 'chart.js/auto';
    import { toTitleCase } from '../utils.js';
    
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
                    <p class="mt-2">Analytics requires DuckDB database engine. Please configure your database settings accordingly.
                        by adding `DB_ENGINE=duckdb` to your .env file.
                    </p>
                {/if}
            </div>
        {:else if analytics?.basic_analytics}
            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
                <AnalyticsCard 
                    title="Total Products" 
                    value={analytics.basic_analytics.total_records} 
                    type="number" 
                />
                
                <AnalyticsCard 
                    title="Unique Brands" 
                    value={analytics.basic_analytics.uniqueness_analysis?.brand_name?.unique_values} 
                    type="number" 
                />
                
                <AnalyticsCard 
                    title="Data Completeness" 
                    value={analytics.basic_analytics.null_analysis?.description?.null_percentage ? 
                        100 - analytics.basic_analytics.null_analysis.description.null_percentage : 0} 
                    type="percentage" 
                />
            </div>

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
                                {#each Object.entries(analytics.basic_analytics.null_analysis) as [field, analysis]}
                                    <tr class="border-t">
                                        <td class="px-6 py-4">{field}</td>
                                        <td class="px-6 py-4">{analysis.null_percentage}%</td>
                                        <td class="px-6 py-4">
                                            {analytics.basic_analytics.uniqueness_analysis[field]?.unique_values ?? 'N/A'}
                                        </td>
                                    </tr>
                                {/each}
                            {/if}
                        </tbody>
                    </table>
                </div>
            </div>

            {#if analytics.advanced_analytics}
                <div class="bg-white rounded-lg shadow p-6 mb-8">
                    <h2 class="text-xl font-semibold mb-4">Advanced Analytics</h2>
                    
                    <!-- Variant Analysis -->
                    <div class="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
                        <div>
                            <h3 class="text-lg font-medium mb-3">Variant Distribution</h3>
                            <table class="min-w-full">
                                <thead>
                                    <tr class="bg-gray-50">
                                        <th class="px-4 py-2 text-left">Variant Count</th>
                                        <th class="px-4 py-2 text-left">Product Count</th>
                                        <th class="px-4 py-2 text-left">Average price</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {#if analytics.advanced_analytics?.variant_analysis?.variants}
                                        {#each analytics.advanced_analytics.variant_analysis.variants as variant}
                                            <tr class="border-t">
                                                <td class="px-4 py-2">{variant.variant_count}</td>
                                                <td class="px-4 py-2">{variant.product_count}</td>
                                                <td class="px-4 py-2">${variant.avg_price}</td>
                                            </tr>
                                        {/each}
                                    {/if}
                                </tbody>
                            </table>
                        </div>

                        <!-- Variant Statistics -->
                        <div>
                            <h3 class="text-lg font-medium mb-3">Variant Statistics</h3>
                            <table class="min-w-full">
                                <tbody>
                                    {#if analytics.advanced_analytics?.variant_analysis?.statistics}
                                        {#each Object.entries(analytics.advanced_analytics.variant_analysis.statistics) as [metric, value]}
                                            <tr class="border-t">
                                                <td class="px-4 py-2 font-medium">{metric.replace(/_/g, ' ')}</td>
                                                <td class="px-4 py-2">
                                                    {metric.includes('correlation') ? 
                                                        `${value} correlation` : 
                                                        metric.includes('total') ? 
                                                            value : 
                                                            value?.toFixed(2) ?? 'N/A'}
                                                </td>
                                            </tr>
                                        {/each}
                                    {/if}
                                </tbody>
                            </table>
                        </div>
                    </div>

                    <!-- Discount Analysis -->
                    <div class="mt-8">
                        <h3 class="text-lg font-medium mb-3">Discount Analysis</h3>
                        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                            <table class="min-w-full">
                                <thead>
                                    <tr class="bg-gray-50">
                                        <th class="px-4 py-2 text-left">Discount Range</th>
                                        <th class="px-4 py-2 text-left">Product Count</th>
                                        <th class="px-4 py-2 text-left">Avg Rating</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {#if analytics.advanced_analytics?.discount_analysis?.ranges}
                                        {#each analytics.advanced_analytics.discount_analysis.ranges as range}
                                            <tr class="border-t">
                                                <td class="px-4 py-2">{range.discount_range}</td>
                                                <td class="px-4 py-2">{range.product_count}</td>
                                                <td class="px-4 py-2">{range.avg_rating || 'N/A'}</td>
                                            </tr>
                                        {/each}
                                    {/if}
                                </tbody>
                            </table>
                        </div>
                    </div>

                    <!-- Rating Analysis -->
                    <div class="mt-8">
                        <h3 class="text-lg font-medium mb-3">Rating Analysis</h3>
                        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                            <table class="min-w-full">
                                <thead>
                                    <tr class="bg-gray-50">
                                        <th class="px-4 py-2 text-left">Metric</th>
                                        <th class="px-4 py-2 text-left">Value</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {#if analytics.advanced_analytics?.rating_analysis?.statistics}
                                        {#each Object.entries(analytics.advanced_analytics.rating_analysis.statistics) as [metric, value]}
                                            <tr class="border-t">
                                                <td class="px-4 py-2">{metric.replace(/_/g, ' ')}</td>
                                                <td class="px-4 py-2">
                                                    {metric.includes('correlation') ? `${value} correlation` : value}
                                                </td>
                                            </tr>
                                        {/each}
                                    {/if}
                                </tbody>
                            </table>
                        </div>
                    </div>

                    <!-- Material Analysis -->
                    <div class="mt-8">
                        <h3 class="text-lg font-medium mb-3">Material Analysis</h3>
                        <div class="overflow-x-auto">
                            <table class="min-w-full">
                                <thead>
                                    <tr class="bg-gray-50">
                                        <th class="px-4 py-2 text-left">Material</th>
                                        <th class="px-4 py-2 text-left">Count</th>
                                        <th class="px-4 py-2 text-left">Avg Price</th>
                                        <th class="px-4 py-2 text-left">Top Brands</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {#if analytics.advanced_analytics?.material_analysis?.popular_materials}
                                        {#each analytics.advanced_analytics.material_analysis.popular_materials as material}
                                            <tr class="border-t">
                                                <td class="px-4 py-2">{material.material}</td>
                                                <td class="px-4 py-2">{material.count}</td>
                                                <td class="px-4 py-2">${material.avg_price}</td>
                                                <td class="px-4 py-2">{material.brands.join(', ')}</td>
                                            </tr>
                                        {/each}
                                    {/if}
                                </tbody>
                            </table>
                        </div>
                    </div>

                    <!-- Brand Analysis -->
                    <div class="mt-8">
                        <h3 class="text-lg font-medium mb-3">Top Brands Analysis</h3>
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
                                    {#if analytics.advanced_analytics?.brand_analysis?.top_brands}
                                        {#each analytics.advanced_analytics.brand_analysis.top_brands as brand}
                                            <tr class="border-t">
                                                <td class="px-4 py-2">{brand.name}</td>
                                                <td class="px-4 py-2">{brand.product_count}</td>
                                                <td class="px-4 py-2">${brand.min_price} - ${brand.max_price}</td>
                                                <td class="px-4 py-2">{brand.avg_rating || 'N/A'}</td>
                                            </tr>
                                        {/each}
                                    {/if}
                                </tbody>
                            </table>
                        </div>
                    </div>

                    <!-- Audience Analysis -->
                    {#if analytics.advanced_analytics?.audience_analysis?.demographics}
                        <div class="mt-8">
                            <h3 class="text-lg font-medium mb-3">Audience Demographics</h3>
                            <div class="overflow-x-auto">
                                <table class="min-w-full">
                                    <thead>
                                        <tr class="bg-gray-50">
                                            <th class="px-4 py-2 text-left">Gender</th>
                                            <th class="px-4 py-2 text-left">Age Group</th>
                                            <th class="px-4 py-2 text-left">Product Count</th>
                                            <th class="px-4 py-2 text-left">Avg Price</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {#each analytics.advanced_analytics.audience_analysis.demographics as demo}
                                            <tr class="border-t">
                                                <td class="px-4 py-2">{demo.gender}</td>
                                                <td class="px-4 py-2">{demo.age_group}</td>
                                                <td class="px-4 py-2">{demo.product_count}</td>
                                                <td class="px-4 py-2">${demo.avg_price}</td>
                                            </tr>
                                        {/each}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    {/if}
                </div>
            {/if}
        {/if}
    </div>
</main> 