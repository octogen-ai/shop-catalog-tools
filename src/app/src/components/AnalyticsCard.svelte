<script>
    export let title;
    export let value;
    export let type = 'number';  // 'number' or 'percentage'
    
    $: formattedValue = value != null 
        ? type === 'percentage' 
            ? `${Number(value).toFixed(1)}%`
            : Number(value).toLocaleString()
        : 'N/A';
</script>

<div class="bg-white rounded-lg shadow p-6">
    <h3 class="text-gray-500 text-sm font-medium">{title}</h3>
    <p class="text-3xl font-bold mt-2">{formattedValue}</p>
</div> 