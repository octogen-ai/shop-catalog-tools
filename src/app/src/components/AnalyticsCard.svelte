<script>
    export let title;
    export let value;
    export let type = 'number';  // 'number' or 'percentage'
    export let href = null;  // New prop for optional link
    
    $: formattedValue = value != null 
        ? type === 'percentage' 
            ? `${Number(value).toFixed(1)}%`
            : Number(value).toLocaleString()
        : 'N/A';
</script>

{#if href}
    <a {href} class="block bg-white rounded-lg shadow p-6 hover:shadow-lg text-blue-600 cursor-pointer transition-all duration-200">
        <h3 class="text-blue-600 text-sm font-medium">{title}</h3>
        <p class="text-3xl font-bold mt-2">{formattedValue}</p>
    </a>
{:else}
    <div class="bg-white rounded-lg shadow p-6">
        <h3 class="text-gray-500 text-sm font-medium">{title}</h3>
        <p class="text-3xl font-bold mt-2">{formattedValue}</p>
    </div>
{/if} 