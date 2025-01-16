<script>
    export let attributes = {};

    function formatAttributeName(name) {
        return name
            .split('_')[0] // Remove any _grp_xxx suffix
            .split(' ')
            .map(word => word.charAt(0).toUpperCase() + word.slice(1))
            .join(' ');
    }

    function formatAttributeValue(attribute) {
        if (!attribute) return '';
        
        let values = [];
        
        // Handle text attributes
        if (attribute.text) {
            values.push(...attribute.text.map(text => {
                // If text contains a colon, only take the part after it
                const colonIndex = text.indexOf(':');
                return colonIndex !== -1 ? text.slice(colonIndex + 1).trim() : text;
            }));
        }
        
        // Handle numeric attributes
        if (attribute.numbers) {
            values.push(...attribute.numbers.map(num => num.toString()));
        }
        
        // If attribute is a simple string
        if (typeof attribute === 'string') {
            values.push(attribute);
        }
        
        return values.join(', ');
    }

    // Filter out attributes with empty values
    $: validAttributes = Object.entries(attributes || {}).filter(([_, value]) => {
        if (typeof value === 'string') return value.length > 0;
        if (value.text) return value.text.length > 0;
        if (value.numbers) return value.numbers.length > 0;
        return false;
    });
</script>

{#if validAttributes.length > 0}
    <div class="mt-4">
        <h3 class="text-sm font-medium text-gray-900">Additional Details</h3>
        <dl class="mt-2 border-t border-gray-200">
            {#each validAttributes as [name, value]}
                <div class="border-b border-gray-200 py-3 flex justify-between">
                    <dt class="text-sm font-medium text-gray-500">
                        {formatAttributeName(name)}
                    </dt>
                    <dd class="text-sm text-gray-900 text-right">
                        {formatAttributeValue(value)}
                    </dd>
                </div>
            {/each}
        </dl>
    </div>
{/if} 