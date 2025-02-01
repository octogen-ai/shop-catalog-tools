<script>
  export let colors = []; // Array of {label, swatch_url} objects
  export let colorSizeAvailability = {};
  export let selectedColor = null;
  export let selectedSize = null;
  export let onColorSelect = (color) => {};
  export let onSizeSelect = (size) => {};
  export let title = "";
  export let disabled = false;

  // Add logging to see what data we're working with
  $: console.log('Selected Color:', selectedColor);
  $: console.log('Color Size Availability for selected:', selectedColor ? colorSizeAvailability[selectedColor] : null);

  // Derive available sizes for the selected color
  $: availableSizes = selectedColor && colorSizeAvailability[selectedColor]
    ? colorSizeAvailability[selectedColor].inStock
    : [];
    
  $: unavailableSizes = selectedColor && colorSizeAvailability[selectedColor]
    ? colorSizeAvailability[selectedColor].outOfStock
    : [];

  $: console.log('Available Sizes:', availableSizes);
  $: console.log('Unavailable Sizes:', unavailableSizes);
</script>

<div>
  <h2 class="text-sm font-medium text-gray-900">{title}</h2>
  
  <!-- Color Selection -->
  <fieldset aria-label="Choose a color" class="mt-2">
    <div class="flex flex-wrap items-center gap-3">
      {#each colors as colorObj}
        <label 
          aria-label={colorObj.label}
          class="relative -m-0.5 flex cursor-pointer items-center justify-center rounded-full p-0.5 ring-gray-900 focus:outline-none group"
          class:opacity-50={disabled}
          class:cursor-not-allowed={disabled}
          class:ring-2={selectedColor === colorObj.label}
        >
          <input 
            type="radio" 
            name="color-choice" 
            value={colorObj.label} 
            checked={selectedColor === colorObj.label}
            on:change={() => {
              console.log('Color selected:', colorObj.label);
              onColorSelect(colorObj.label);
            }}
            {disabled}
            class="sr-only"
          >
          {#if colorObj.swatch_url}
            <img 
              src={colorObj.swatch_url} 
              alt={colorObj.label}
              class="size-8 rounded-full border border-black/10"
            />
          {:else}
            <span aria-hidden="true" class="size-8 rounded-full border border-black/10 bg-gray-900"></span>
          {/if}
          <div class="absolute hidden group-hover:block bg-gray-800 text-white text-xs rounded px-2 py-1 -mt-1 bottom-full transform -translate-x-1/2 left-1/2 mb-2">
            {colorObj.label}{disabled ? ' (unavailable)' : ''}
          </div>
        </label>
      {/each}
    </div>
  </fieldset>

  <!-- Size Selection -->
  {#if selectedColor}
    <div class="mt-6">
      <h3 class="text-sm font-medium text-gray-900">Available Sizes</h3>
      <div class="grid grid-cols-4 gap-2 mt-2">
        {#each availableSizes as size}
          <button
            type="button"
            class="border rounded px-4 py-2 text-sm font-medium
              {selectedSize === size ? 'border-black bg-black text-white' : 'border-gray-200 text-gray-900 hover:bg-gray-50'}"
            on:click={() => onSizeSelect(size)}
          >
            {size}
          </button>
        {/each}
      </div>

      {#if unavailableSizes.length > 0}
        <h3 class="text-sm font-medium text-gray-900 mt-4">Out of Stock</h3>
        <div class="grid grid-cols-4 gap-2 mt-2">
          {#each unavailableSizes as size}
            <button
              type="button"
              disabled
              class="border border-gray-200 rounded px-4 py-2 text-sm font-medium text-gray-400 cursor-not-allowed"
            >
              {size}
            </button>
          {/each}
        </div>
      {/if}

      {#if availableSizes.length === 0 && unavailableSizes.length === 0}
        <p class="text-sm text-gray-500">No sizes available for this color</p>
      {/if}
    </div>
  {/if}
</div> 