<script>
    export let product;
    export let expanded = false;
    export let onToggleExpand = () => {};
  
    // Combine primary image with additional images and remove duplicates
    $: allImages = product.image 
      ? [product.image, ...product.images].filter((img, index, self) => 
          index === self.findIndex(t => t.url === img.url)
        )
      : product.images;

    let currentImageIndex = 0;

    function nextImage() {
      currentImageIndex = (currentImageIndex + 1) % allImages.length;
    }

    function previousImage() {
      currentImageIndex = (currentImageIndex - 1 + allImages.length) % allImages.length;
    }

    // Helper function to get availability icon and color
    function getAvailabilityInfo(availability) {
      switch(availability) {
        case 'IN_STOCK':
          return { icon: '✓', color: 'text-green-500', text: 'In Stock' };
        case 'OUT_OF_STOCK':
          return { icon: '×', color: 'text-red-500', text: 'Out of Stock' };
        case 'PREORDER':
          return { icon: '⏰', color: 'text-blue-500', text: 'Pre-order' };
        case 'BACKORDER':
          return { icon: '⌛', color: 'text-yellow-500', text: 'Backordered' };
        default:
          return { icon: '?', color: 'text-gray-500', text: 'Unknown' };
      }
    }

    // Generate array of 5 stars for rating
    function getRatingStars(rating) {
      return Array(5).fill(null).map((_, index) => ({
        filled: index < Math.floor(rating),
        half: index === Math.floor(rating) && rating % 1 >= 0.5
      }));
    }
  </script>
  
  <div class="bg-white rounded-lg shadow-md overflow-hidden {expanded ? 'col-span-full' : ''}">
    <div class="cursor-pointer" on:click={() => onToggleExpand(product)}>
      <div class="relative">
        {#if allImages && allImages.length > 0}
          <img 
            src={allImages[currentImageIndex].url} 
            alt={product.name} 
            class="w-full h-64 object-cover"
          />
          {#if allImages.length > 1}
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
        {/if}
      </div>

      <div class="p-4">
        <h3 class="text-lg font-semibold mb-2">{product.name}</h3>
        <p class="text-gray-600 mb-2">${product.price_info?.price}</p>
        {#if product.availability}
          {@const availInfo = getAvailabilityInfo(product.availability)}
          <p class={availInfo.color}>
            {availInfo.icon} {availInfo.text}
          </p>
        {/if}
        {#if product.hasVariant?.length}
          <p class="text-sm text-blue-600 mt-2">
            {product.hasVariant.length} variants available
          </p>
        {/if}
      </div>
    </div>

    {#if expanded && product.hasVariant}
      <div class="border-t p-4">
        <h4 class="text-lg font-semibold mb-4">Available Variants</h4>
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {#each product.hasVariant as variant}
            {#if variant}
              <div class="border rounded p-4">
                {#if variant.image}
                  <img
                    src={variant.image.url}
                    alt={variant.name}
                    class="w-full h-48 object-cover mb-2"
                  />
                {/if}
                <h5 class="font-medium mb-1">{variant.name}</h5>
                <p class="text-gray-600 mb-1">${variant.price_info?.price}</p>
                {#if variant.color_info?.colors}
                  <p class="text-sm text-gray-500">Color: {variant.color_info.colors.join(', ')}</p>
                {/if}
                {#if variant.sizes}
                  <p class="text-sm text-gray-500">Size: {variant.sizes.join(', ')}</p>
                {/if}
                {#if variant.availability}
                  {@const availInfo = getAvailabilityInfo(variant.availability)}
                  <p class={availInfo.color}>
                    {availInfo.icon} {availInfo.text}
                  </p>
                {/if}
              </div>
            {/if}
          {/each}
        </div>
      </div>
    {/if}
  </div>