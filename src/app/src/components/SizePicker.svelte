<script>
  export let sizes = [];
  export let selectedSize = null;
  export let onSizeSelect = (size) => {};
  export let title = "";
  export let disabled = false;
</script>

<div class="mt-8">
  <h2 class="text-sm font-medium text-gray-900">{title}</h2>
  <fieldset aria-label="Choose a size" class="mt-2">
    <div class="grid grid-cols-3 gap-3 sm:grid-cols-6">
      {#each sizes as size}
        <label 
          class="flex cursor-pointer items-center justify-center rounded-md border px-3 py-3 text-sm font-medium uppercase focus:outline-none sm:flex-1 relative group"
          class:opacity-50={disabled}
          class:cursor-not-allowed={disabled}
          aria-label={`${size}${disabled ? ' (unavailable)' : ''}`}
        >
          <input 
            type="radio" 
            name="size-choice" 
            value={size} 
            checked={selectedSize === size}
            on:change={() => onSizeSelect(size)}
            {disabled}
            class="sr-only"
          >
          <span>{size}</span>
          {#if disabled}
            <div class="absolute hidden group-hover:block bg-gray-800 text-white text-xs rounded px-2 py-1 -mt-1 bottom-full transform -translate-x-1/2 left-1/2 mb-2">
              Unavailable
            </div>
          {/if}
        </label>
      {/each}
    </div>
  </fieldset>
</div> 