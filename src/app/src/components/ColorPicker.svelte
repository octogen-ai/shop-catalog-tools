<script>
  export let colors = [];
  export let selectedColor = null;
  export let onColorSelect = (color) => {};
  export let title = "";
  export let disabled = false;
</script>

<div>
  <h2 class="text-sm font-medium text-gray-900">{title}</h2>
  <fieldset aria-label="Choose a color" class="mt-2">
    <div class="flex flex-wrap items-center gap-3">
      {#each colors as color}
        <label 
          aria-label={`${color}${disabled ? ' (unavailable)' : ''}`}
          class="relative -m-0.5 flex cursor-pointer items-center justify-center rounded-full p-0.5 ring-gray-900 focus:outline-none group"
          class:opacity-50={disabled}
          class:cursor-not-allowed={disabled}
        >
          <input 
            type="radio" 
            name="color-choice" 
            value={color} 
            checked={selectedColor === color}
            on:change={() => onColorSelect(color)}
            {disabled}
            class="sr-only"
          >
          <span aria-hidden="true" class="size-8 rounded-full border border-black/10 bg-gray-900"></span>
          <div class="absolute hidden group-hover:block bg-gray-800 text-white text-xs rounded px-2 py-1 -mt-1 bottom-full transform -translate-x-1/2 left-1/2 mb-2">
            {color}{disabled ? ' (unavailable)' : ''}
          </div>
        </label>
      {/each}
    </div>
  </fieldset>
</div> 