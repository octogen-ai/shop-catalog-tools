<script>
    import { createEventDispatcher } from 'svelte';
    const dispatch = createEventDispatcher();

    export let value = '';
    export let isLoading = false;
    export let placeholder = 'Search products...';

    function handleKeydown(event) {
        if (event.key === 'Enter') {
            dispatch('search', { type: 'keydown', key: 'Enter' });
        }
    }

    function handleClick() {
        dispatch('search', { type: 'click' });
    }
</script>

<div class="flex gap-2">
    <input
        type="text"
        bind:value
        {placeholder}
        class="flex-1 px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
        on:keydown={handleKeydown}
    />
    <button
        on:click={handleClick}
        class="px-6 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 focus:outline-none focus:ring-2 focus:ring-blue-500"
        disabled={isLoading}
    >
        {isLoading ? 'Searching...' : 'Search'}
    </button>
</div> 