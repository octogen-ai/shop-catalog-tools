<script>
    import { onMount } from 'svelte';
    import AnalyticsCard from '../components/AnalyticsCard.svelte';
    import CatalogSelector from '../components/CatalogSelector.svelte';
    import { Chart } from 'chart.js/auto';
    import { toTitleCase } from '../utils.js';
    
    let basicAnalytics = null;
    let advancedAnalytics = null;
    let loading = true;
    let error = null;
    let isDuckDB = false;
    
    // Get table name from URL path
    $: tableName = window.location.pathname.split('/')[1] || 'anntaylor';

    async function loadAnalytics() {
        loading = true;
        error = null;
        
        try {
            // Load basic analytics
            const basicRes = await fetch(`/api/${tableName}/analytics`);
            basicAnalytics = await basicRes.json();
            
            // Try to load advanced analytics (DuckDB only)
            try {
                const advancedRes = await fetch(`/api/${tableName}/advanced-analytics`);
                if (advancedRes.ok) {
                    advancedAnalytics = await advancedRes.json();
                    isDuckDB = true;
                }
            } catch (e) {
                console.log('Advanced analytics not available (requires DuckDB)');
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
            <div class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
                {error}
            </div>
        {:else if basicAnalytics}
            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
                <AnalyticsCard 
                    title="Total Products" 
                    value={basicAnalytics?.total_records} 
                    type="number" 
                />
                
                <AnalyticsCard 
                    title="Unique Brands" 
                    value={basicAnalytics?.uniqueness_analysis?.brand_name?.unique_values} 
                    type="number" 
                />
                
                <AnalyticsCard 
                    title="Data Completeness" 
                    value={basicAnalytics?.null_analysis?.description?.null_percentage ? 
                        100 - basicAnalytics.null_analysis.description.null_percentage : 0} 
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
                            {#if basicAnalytics?.null_analysis && basicAnalytics?.uniqueness_analysis}
                                {#each Object.entries(basicAnalytics.null_analysis) as [field, analysis]}
                                    <tr class="border-t">
                                        <td class="px-6 py-4">{field}</td>
                                        <td class="px-6 py-4">{analysis.null_percentage}%</td>
                                        <td class="px-6 py-4">
                                            {basicAnalytics.uniqueness_analysis[field]?.unique_values ?? 'N/A'}
                                        </td>
                                    </tr>
                                {/each}
                            {/if}
                        </tbody>
                    </table>
                </div>
            </div>

            {#if isDuckDB && advancedAnalytics}
                <div class="bg-white rounded-lg shadow p-6 mb-8">
                    <h2 class="text-xl font-semibold mb-4">Advanced Analytics (DuckDB)</h2>
                    
                    <!-- Variant Analysis -->
                    <div class="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
                        <div>
                            <h3 class="text-lg font-medium mb-3">Variant Distribution</h3>
                            <table class="min-w-full">
                                <thead>
                                    <tr class="bg-gray-50">
                                        <th class="px-4 py-2 text-left">Variant Count</th>
                                        <th class="px-4 py-2 text-left">Product Count</th>
                                        <th class="px-4 py-2 text-left">Percentage</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {#if advancedAnalytics?.variant_analysis?.distribution}
                                        {#each advancedAnalytics.variant_analysis.distribution as variant}
                                            <tr class="border-t">
                                                <td class="px-4 py-2">{variant.variant_count}</td>
                                                <td class="px-4 py-2">{variant.product_count}</td>
                                                <td class="px-4 py-2">{variant.percentage}%</td>
                                            </tr>
                                        {/each}
                                    {/if}
                                </tbody>
                            </table>
                        </div>

                        <!-- Price Distribution -->
                        <div>
                            <h3 class="text-lg font-medium mb-3">Price Distribution</h3>
                            <table class="min-w-full">
                                <tbody>
                                    {#if advancedAnalytics?.price_distribution?.statistics}
                                        {#each Object.entries(advancedAnalytics.price_distribution.statistics) as [metric, value]}
                                            <tr class="border-t">
                                                <td class="px-4 py-2 font-medium">{metric}</td>
                                                <td class="px-4 py-2">${value}</td>
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
                                    {#if advancedAnalytics?.discount_analysis?.ranges}
                                        {#each advancedAnalytics.discount_analysis.ranges as range}
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
                                    {#if advancedAnalytics?.rating_analysis?.statistics}
                                        {#each Object.entries(advancedAnalytics.rating_analysis.statistics) as [metric, value]}
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
                                    {#if advancedAnalytics?.material_analysis?.popular_materials}
                                        {#each advancedAnalytics.material_analysis.popular_materials as material}
                                            <tr class="border-t">
                                                <td class="px-4 py-2">{material.name}</td>
                                                <td class="px-4 py-2">{material.count}</td>
                                                <td class="px-4 py-2">${material.avg_price}</td>
                                                <td class="px-4 py-2">{material.top_brands.join(', ')}</td>
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
                                    {#if advancedAnalytics?.brand_analysis?.top_brands}
                                        {#each advancedAnalytics.brand_analysis.top_brands as brand}
                                            <tr class="border-t">
                                                <td class="px-4 py-2">{brand.name}</td>
                                                <td class="px-4 py-2">{brand.product_count}</td>
                                                <td class="px-4 py-2">${brand.price_range.min} - ${brand.price_range.max}</td>
                                                <td class="px-4 py-2">{brand.avg_rating || 'N/A'}</td>
                                            </tr>
                                        {/each}
                                    {/if}
                                </tbody>
                            </table>
                        </div>
                    </div>

                    <!-- Audience Analysis -->
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
                                    {#if advancedAnalytics?.audience_analysis?.demographics}
                                        {#each advancedAnalytics.audience_analysis.demographics as demo}
                                            <tr class="border-t">
                                                <td class="px-4 py-2">{demo.gender}</td>
                                                <td class="px-4 py-2">{demo.age_group}</td>
                                                <td class="px-4 py-2">{demo.product_count}</td>
                                                <td class="px-4 py-2">${demo.avg_price}</td>
                                            </tr>
                                        {/each}
                                    {/if}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            {/if}
        {/if}
    </div>
</main> 