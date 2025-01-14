<script>
  export let images = [];
  export let currentIndex = 0;
  export let productName = '';
</script>

<div class="mt-8 lg:col-span-7 lg:col-start-1 lg:row-span-3 lg:row-start-1 lg:mt-0">
  <div class="grid grid-cols-1 lg:grid-cols-2 lg:grid-rows-3 lg:gap-8">
    {#if images && images.length > 0}
      <img 
        src={images[currentIndex].url}
        alt={productName}
        class="rounded-lg lg:col-span-2 lg:row-span-2"
      />
      {#each images as image}
        <img 
          src={image.url}
          alt={productName}
          class="hidden rounded-lg lg:block"
        />
      {/each}
    {/if}
  </div>
</div>