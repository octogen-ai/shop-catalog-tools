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

    // Helper function to group variants by image URL
    function groupVariantsByImage(variants) {
      return variants.reduce((acc, variant) => {
        const imageUrl = variant.image?.url;
        if (!acc[imageUrl]) {
          acc[imageUrl] = {
            ...variant,
            colors: variant.color_info?.colors || [],
            sizes: variant.sizes || [],
          };
        } else {
          // Merge colors and sizes
          if (variant.color_info?.colors) {
            acc[imageUrl].colors = [...new Set([...acc[imageUrl].colors, ...variant.color_info.colors])];
          }
          if (variant.sizes) {
            acc[imageUrl].sizes = [...new Set([...acc[imageUrl].sizes, ...variant.sizes])];
          }
        }
        return acc;
      }, {});
    }
  </script>
  
  <div class="bg-white rounded-lg shadow-md overflow-hidden {expanded ? 'col-span-full' : ''}">
    <button 
        type="button"
        class="w-full text-left cursor-pointer"
        on:click={() => onToggleExpand(product)}
        aria-expanded={expanded}
    >
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
        <div class="flex justify-between items-start mb-2">
          <h3 class="text-lg font-semibold">{product.name}</h3>
          <div class="flex gap-2">
            {#if product.url}
              <a
                href={product.url}
                target="_blank"
                rel="noopener noreferrer"
                class="text-gray-500 hover:text-gray-700"
                title="View on Retailer Site"
                on:click|stopPropagation
              >
                <div class="relative group">
                  <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                    <path d="M11 3a1 1 0 100 2h2.586l-6.293 6.293a1 1 0 101.414 1.414L15 6.414V9a1 1 0 102 0V4a1 1 0 00-1-1h-5z" />
                    <path d="M5 5a2 2 0 00-2 2v8a2 2 0 002 2h8a2 2 0 002-2v-3a1 1 0 10-2 0v3H5V7h3a1 1 0 000-2H5z" />
                  </svg>
                  <div class="absolute hidden group-hover:block bg-gray-800 text-white text-sm rounded px-2 py-1 -mt-1 left-1/2 transform -translate-x-1/2 -translate-y-full z-[100]">
                    View on retailer site
                  </div>
                </div>
              </a>
            {/if}
            <a
              href={`/api/${product.catalog}/product/${product.id}/raw?format=tree`}
              target="_blank"
              rel="noopener noreferrer"
              class="text-gray-500 hover:text-gray-700"
              title="View Raw JSON"
              on:click|stopPropagation
            >
            <div class="relative group">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                <path fill-rule="evenodd" d="M12.316 3.051a1 1 0 01.633 1.265l-4 12a1 1 0 11-1.898-.632l4-12a1 1 0 011.265-.633zM5.707 6.293a1 1 0 010 1.414L3.414 10l2.293 2.293a1 1 0 11-1.414 1.414l-3-3a1 1 0 010-1.414l3-3a1 1 0 011.414 0zm8.586 0a1 1 0 011.414 0l3 3a1 1 0 010 1.414l-3 3a1 1 0 11-1.414-1.414L16.586 10l-2.293-2.293a1 1 0 010-1.414z" clip-rule="evenodd" />
              </svg>
              <div class="absolute hidden group-hover:block bg-gray-800 text-white text-sm rounded px-2 py-1 -mt-1 left-1/2 transform -translate-x-1/2 -translate-y-full z-[100]">
                Raw product data
              </div>
            </div>
            </a>
          </div>
          
        </div>
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
    </button>

    {#if expanded && product.hasVariant}
      <div class="border-t p-4">
        {#if product.description}
          <div class="mb-4">
            <h4 class="text-lg font-semibold mb-2">Description</h4>
            <p class="text-gray-600">{product.description}</p>
          </div>
        {/if}

        {#if product.categories && product.categories.length > 0}
          <div class="mb-4">
            <h4 class="text-lg font-semibold mb-2">Categories</h4>
            <nav class="flex flex-wrap gap-2">
              {#each product.categories as category}
                <a
                  href={category.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  class="text-blue-600 hover:text-blue-800 hover:underline"
                >
                  {category.name}
                  {#if category !== product.categories[product.categories.length - 1]}
                    <span class="text-gray-400 mx-1">›</span>
                  {/if}
                </a>
              {/each}
            </nav>
          </div>
        {/if}

        {#if product.materials && product.materials.length > 0}
          <div class="mb-4">
            <h4 class="text-lg font-semibold mb-2">Materials</h4>
            <p class="text-gray-600">{product.materials.join(', ')}</p>
          </div>
        {/if}

        <h4 class="text-lg font-semibold mb-4">Available Variants</h4>
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {#each Object.values(groupVariantsByImage(product.hasVariant)) as variant}
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
                {#if variant.colors?.length > 0}
                  <p class="text-sm text-gray-500">Colors: {variant.colors.join(', ')}</p>
                {/if}
                {#if variant.sizes?.length > 0}
                  <p class="text-sm text-gray-500">Sizes: {variant.sizes.join(', ')}</p>
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