<script>
    import { onMount } from 'svelte';
    import AnalyticsCard from '../components/AnalyticsCard.svelte';
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
                    title="Missing Product Images" 
                    value={analytics?.basic_analytics?.image_analysis?.null_product_images_percentage}
                    type="percentage"
                    href={`/${tableName}#filter:product_image:is_null`}
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
                                        <td class="px-6 py-4">
                                            <a 
                                                href={`/${tableName}#filter:${field}:is_null`} 
                                                class="text-blue-600 hover:shadow-lg cursor-pointer transition-all duration-200"
                                            >
                                                {analysis.null_percentage}%
                                            </a>
                                        </td>
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

            <div class="bg-white rounded-lg shadow p-6 mb-8">
                <h2 class="text-xl font-semibold mb-4">Image Analysis</h2>
                <div class="overflow-x-auto">
                    <table class="min-w-full">
                        <thead>
                            <tr class="bg-gray-50">
                                <th class="px-6 py-3 text-left">Metric</th>
                                <th class="px-6 py-3 text-left">Value</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr class="border-t">
                                <td class="px-6 py-4">Products Missing Images</td>
                                <td class="px-6 py-4">{analytics?.basic_analytics?.image_analysis?.null_product_images ?? 0}</td>
                            </tr>
                            <tr class="border-t">
                                <td class="px-6 py-4">Average Variant Images</td>
                                <td class="px-6 py-4">{analytics.basic_analytics.image_analysis.avg_variant_images.toFixed(2)}</td>
                            </tr>
                            <tr class="border-t">
                                <td class="px-6 py-4">Max Variant Images</td>
                                <td class="px-6 py-4">{analytics.basic_analytics.image_analysis.max_variant_images}</td>
                            </tr>
                            <tr class="border-t">
                                <td class="px-6 py-4">Min Variant Images</td>
                                <td class="px-6 py-4">{analytics.basic_analytics.image_analysis.min_variant_images}</td>
                            </tr>
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
                    {#if analytics.advanced_analytics?.rating_analysis?.statistics.avg_rating}
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
                    {/if}

                    <!-- Material Analysis -->
                    {#if analytics.advanced_analytics?.material_analysis?.popular_materials}
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
                    {/if}

                    <!-- Brand Analysis -->
                    {#if analytics.advanced_analytics?.brand_analysis?.top_brands}
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
                    {/if}
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
                    <!-- Add this section after the Audience Analysis section -->
                    {#if analytics.advanced_analytics?.additional_attributes_analysis.attributes}
                        <div class="mt-8">
                            <h3 class="text-lg font-medium mb-3">Additional Attributes Analysis</h3>
                            
                            <!-- Overall Statistics Card Row -->
                            <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
                                <AnalyticsCard 
                                    title="Total Custom Attributes" 
                                    value={analytics.advanced_analytics.additional_attributes_analysis.statistics.total_attributes} 
                                    type="number" 
                                />
                                <AnalyticsCard 
                                    title="Avg Attributes per Product" 
                                    value={analytics.advanced_analytics.additional_attributes_analysis.statistics.avg_attributes_per_product} 
                                    type="number" 
                                />
                                <AnalyticsCard 
                                    title="Products with Attributes" 
                                    value={analytics.advanced_analytics.additional_attributes_analysis.statistics.products_with_attributes} 
                                    type="number" 
                                />
                            </div>

                            <!-- Attributes Table -->
                            <div class="overflow-x-auto">
                                <table class="min-w-full">
                                    <thead>
                                        <tr class="bg-gray-50">
                                            <th class="px-4 py-2 text-left">Attribute Name</th>
                                            <th class="px-4 py-2 text-left">Occurrence Count</th>
                                            <th class="px-4 py-2 text-left">Unique Values</th>
                                            <th class="px-4 py-2 text-left">Coverage %</th>
                                            <th class="px-4 py-2 text-left">Sample Values</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {#each analytics.advanced_analytics.additional_attributes_analysis.attributes as attr}
                                            <tr class="border-t">
                                                <td class="px-4 py-2 font-medium">{attr.name}</td>
                                                <td class="px-4 py-2">{attr.occurrence_count}</td>
                                                <td class="px-4 py-2">{attr.unique_values}</td>
                                                <td class="px-4 py-2">{attr.coverage_percentage}%</td>
                                                <td class="px-4 py-2">
                                                    <div class="flex flex-wrap gap-1">
                                                        {#each attr.value_samples.slice(0, 3) as sample}
                                                            <span class="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-gray-100 text-gray-800">
                                                                {sample}
                                                            </span>
                                                        {/each}
                                                        {#if attr.value_samples.length > 3}
                                                            <span class="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-gray-100 text-gray-500">
                                                                +{attr.value_samples.length - 3} more
                                                            </span>
                                                        {/if}
                                                    </div>
                                                </td>
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