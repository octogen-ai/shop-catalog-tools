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
        {:else}
            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
                <AnalyticsCard 
                    title="Total Products" 
                    value={basicAnalytics.total_records} 
                    type="number" 
                />
                
                <AnalyticsCard 
                    title="Unique Brands" 
                    value={basicAnalytics.uniqueness_analysis.brand_name.unique_values} 
                    type="number" 
                />
                
                <AnalyticsCard 
                    title="Data Completeness" 
                    value={100 - basicAnalytics.null_analysis.description.null_percentage} 
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
                            {#each Object.entries(basicAnalytics.null_analysis) as [field, analysis]}
                                <tr class="border-t">
                                    <td class="px-6 py-4">{field}</td>
                                    <td class="px-6 py-4">{analysis.null_percentage}%</td>
                                    <td class="px-6 py-4">
                                        {basicAnalytics.uniqueness_analysis[field].unique_values}
                                    </td>
                                </tr>
                            {/each}
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
                                    {#each advancedAnalytics.variant_analysis.distribution as variant}
                                        <tr class="border-t">
                                            <td class="px-4 py-2">{variant.variant_count}</td>
                                            <td class="px-4 py-2">{variant.product_count}</td>
                                            <td class="px-4 py-2">{variant.percentage}%</td>
                                        </tr>
                                    {/each}
                                </tbody>
                            </table>
                        </div>

                        <!-- Price Distribution -->
                        <div>
                            <h3 class="text-lg font-medium mb-3">Price Distribution</h3>
                            <table class="min-w-full">
                                <tbody>
                                    {#each Object.entries(advancedAnalytics.price_distribution.statistics) as [metric, value]}
                                        <tr class="border-t">
                                            <td class="px-4 py-2 font-medium">{metric}</td>
                                            <td class="px-4 py-2">${value}</td>
                                        </tr>
                                    {/each}
                                </tbody>
                            </table>
                        </div>
                    </div>

                    <!-- Color Combinations -->
                    <div class="mt-8">
                        <h3 class="text-lg font-medium mb-3">Popular Color Combinations</h3>
                        <div class="overflow-x-auto">
                            <table class="min-w-full">
                                <thead>
                                    <tr class="bg-gray-50">
                                        <th class="px-4 py-2 text-left">Color</th>
                                        <th class="px-4 py-2 text-left">Color Families</th>
                                        <th class="px-4 py-2 text-left">Frequency</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {#each advancedAnalytics.color_combinations.popular_combinations as combo}
                                        <tr class="border-t">
                                            <td class="px-4 py-2">{combo.color}</td>
                                            <td class="px-4 py-2">{combo.color_families}</td>
                                            <td class="px-4 py-2">{combo.frequency}</td>
                                        </tr>
                                    {/each}
                                </tbody>
                            </table>
                        </div>
                    </div>

                    <!-- Size Availability -->
                    <div class="mt-8">
                        <h3 class="text-lg font-medium mb-3">Size Availability</h3>
                        <div class="overflow-x-auto">
                            <table class="min-w-full">
                                <thead>
                                    <tr class="bg-gray-50">
                                        <th class="px-4 py-2 text-left">Size</th>
                                        <th class="px-4 py-2 text-left">Total Count</th>
                                        <th class="px-4 py-2 text-left">In Stock</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {#each advancedAnalytics.size_availability.distribution as size}
                                        <tr class="border-t">
                                            <td class="px-4 py-2">{size.size}</td>
                                            <td class="px-4 py-2">{size.total_count}</td>
                                            <td class="px-4 py-2">{size.in_stock_count}</td>
                                        </tr>
                                    {/each}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            {/if}
        {/if}
    </div>
</main> 