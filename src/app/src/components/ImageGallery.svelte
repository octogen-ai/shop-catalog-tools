<script>
  import { fade } from 'svelte/transition';
  
  export let images = [];
  export let currentIndex = 0;
  export let productName = '';
  export let compact = false;
  export let showThumbnails = true;

  function nextImage() {
    if (images.length > 0) {
      currentIndex = (currentIndex + 1) % images.length;
    }
  }

  function previousImage() {
    if (images.length > 0) {
      currentIndex = (currentIndex - 1 + images.length) % images.length;
    }
  }

  $: {
    if (currentIndex >= images.length) {
      currentIndex = images.length - 1;
    }
    if (currentIndex < 0) {
      currentIndex = 0;
    }
  }
</script>

<div class={compact ? "relative" : "mt-8 lg:col-span-7 lg:col-start-1 lg:row-span-3 lg:row-start-1 lg:mt-0"}>
  <div class={compact ? "" : "grid grid-cols-1 lg:grid-cols-2 lg:grid-rows-3 gap-4"}>
    {#if images && images.length > 0}
      {#if compact}
        <div class="relative h-64 bg-gray-50">
          <img 
            in:fade={{ duration: 500 }}
            src={images[currentIndex].url}
            alt={productName}
            class="w-full h-full object-contain p-2"
            on:error|stopPropagation
          />
          
          {#if images.length > 1}
            <button 
              class="absolute left-2 top-1/2 transform -translate-y-1/2 bg-black bg-opacity-50 text-white p-2 rounded-full"
              on:click|stopPropagation={previousImage}
            >
              ←
            </button>
            <button 
              class="absolute right-2 top-1/2 transform -translate-y-1/2 bg-black bg-opacity-50 text-white p-2 rounded-full"
              on:click|stopPropagation={nextImage}
            >
              →
            </button>
          {/if}
        </div>
      {:else}
        <!-- Main large image -->
        <img 
          in:fade={{ duration: 500 }}
          src={images[0].url}
          alt={productName}
          class="rounded-lg lg:col-span-2 lg:row-span-2 w-full h-full min-h-[32rem] object-contain bg-gray-50 p-2"
          on:error|stopPropagation
        />

        {#if showThumbnails && images.length > 1}
          <!-- Thumbnails -->
          {#each images.slice(1) as image}
            <img 
              src={image.url}
              alt={productName}
              class="hidden rounded-lg lg:block w-full h-full min-h-[16rem] object-contain bg-gray-50 p-2"
            />
          {/each}
        {/if}
      {/if}
    {:else}
      <div class="w-full h-64 flex items-center justify-center bg-gray-100">
        <p class="text-gray-500">No image available</p>
      </div>
    {/if}
  </div>
</div>