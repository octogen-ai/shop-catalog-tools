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

    function handleClear() {
        value = '';
        dispatch('clear');
        dispatch('search', { type: 'clear' });
    }
</script>

<div class="flex gap-2">
    <div class="flex-1 relative">
        <input
            type="text"
            bind:value
            {placeholder}
            class="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            on:keydown={handleKeydown}
        />
        {#if value}
            <button 
                class="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600"
                on:click={handleClear}
                aria-label="Clear search"
            >
                <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                    <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd" />
                </svg>
            </button>
        {/if}
    </div>
    <button
        on:click={handleClick}
        class="px-6 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 focus:outline-none focus:ring-2 focus:ring-blue-500"
        disabled={isLoading}
    >
        {isLoading ? 'Searching...' : 'Search'}
    </button>
</div> 