<script>
    import { fade } from 'svelte/transition';
    import RatingDisplay from './RatingDisplay.svelte';
    import ReviewList from './ReviewList.svelte';
    import ColorPicker from './ColorPicker.svelte';
    import SizePicker from './SizePicker.svelte';
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
    let selectedColor = null;
    let selectedSize = null;
    
    // Add this computed property to define variants
    $: variants = product.hasVariant 
      ? Object.values(groupVariantsByImage(product.hasVariant))[0]
      : null;

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

    // Helper function to group variants by image URL
    function groupVariantsByImage(variants) {
      // Collect all colors and sizes, and track which are in stock
      const inStockColors = new Set();
      const inStockSizes = new Set();
      const allColors = new Set();
      const allSizes = new Set();
      
      variants.forEach(variant => {
        const isInStock = variant.offers?.availability === 'http://schema.org/InStock';
        
        // Add colors
        if (variant.color_info?.colors) {
          variant.color_info.colors.forEach(color => {
            allColors.add(color);
            if (isInStock) inStockColors.add(color);
          });
        }
        
        // Add sizes
        if (variant.sizes) {
          variant.sizes.forEach(size => {
            allSizes.add(size);
            if (isInStock) inStockSizes.add(size);
          });
        }
      });

      const outOfStockColors = Array.from(allColors).filter(c => !inStockColors.has(c));
      const outOfStockSizes = Array.from(allSizes).filter(s => !inStockSizes.has(s));
      
      return variants.reduce((acc, variant) => {
        const imageUrl = variant.image?.url;
        if (!acc[imageUrl]) {
          acc[imageUrl] = {
            ...variant,
            inStockColors: Array.from(inStockColors),
            outOfStockColors,
            inStockSizes: Array.from(inStockSizes),
            outOfStockSizes,
          };
        }
        return acc;
      }, {});
    }

    function handleBackgroundClick(event) {
      // Only close if clicking the background overlay
      if (event.target === event.currentTarget) {
        onToggleExpand(product);
      }
      return;
    }

    function handleEscape(event) {
      // console.log('Key pressed:', event.key); // Debug log
      if (event.key === 'Escape') {
        console.log('Escape key detected!'); // Debug log
        onToggleExpand(product);
      }
      return;
    }

    $: {
      if (expanded) {
        console.log('Adding escape listener'); // Debug log
        document.addEventListener('keydown', handleEscape);
      } else {
        console.log('Removing escape listener'); // Debug log
        document.removeEventListener('keydown', handleEscape);
      }
    }

    function handleColorSelect(color) {
      selectedColor = color;
      // Add any additional logic needed when color changes
    }
    
    function handleSizeSelect(size) {
      selectedSize = size;
      // Add any additional logic needed when size changes
    }
  </script>
  
  <div class="bg-white">
    {#if !expanded}
      <button 
        type="button"
        class="w-full h-full text-left cursor-pointer"
        on:click={() => onToggleExpand(product)}
        aria-expanded={expanded}
        transition:fade={{ duration: 500 }}
      >
        <div class="bg-white rounded-lg shadow-md overflow-hidden h-full flex flex-col">
          <div class="relative">
            {#if allImages && allImages.length > 0}
              <img 
                in:fade={{ duration: 500 }}
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

          <div class="p-4 flex-1 flex flex-col" in:fade={{ duration: 500 }}>
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
            <div class="flex-1 flex flex-col justify-between">
              <div>
                {#if product.rating}
                  <div class="mb-2">
                    <RatingDisplay rating={product.rating} size="sm" />
                  </div>
                {/if}
                <p class="text-gray-600 mb-2">${product.price_info?.price}</p>
                {#if product.availability}
                  {@const availInfo = getAvailabilityInfo(product.availability)}
                  <p class={availInfo.color}>
                    {availInfo.icon} {availInfo.text}
                  </p>
                {/if}
              </div>
            </div>
          </div>
        </div>
      </button>
    {:else}
      <!-- Full screen overlay -->
      <button 
        class="fixed inset-0 bg-black bg-opacity-50 z-50 overflow-y-auto w-full border-none"
        on:click={handleBackgroundClick}
        on:keydown={(e) => e.key === 'Escape' && onToggleExpand(product)}
        aria-label="Product details"
        transition:fade={{ duration: 500 }}
      >
        <div role="dialog" aria-modal="true" class="min-h-screen px-4 flex items-center justify-center">
          <div class="bg-white w-full max-w-7xl rounded-lg shadow-xl">
            <!-- Close button -->
            <div class="flex justify-end p-4">
              <button
                class="text-gray-500 hover:text-gray-700"
                on:click={() => onToggleExpand(product)}
              >
                <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            <!-- Existing expanded content -->
            <div class="pb-16 pt-6 sm:pb-24">
              <!-- Breadcrumb -->
              {#if product.categories && product.categories.length > 0}
                <nav aria-label="Breadcrumb" class="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
                  <ol role="list" class="flex items-center space-x-4">
                    {#each product.categories as category, i}
                      <li>
                        <div class="flex items-center">
                          <a href={category.url} class="mr-4 text-sm font-medium text-gray-900">{category.name}</a>
                          {#if i < product.categories.length - 1}
                            <svg viewBox="0 0 6 20" aria-hidden="true" class="h-5 w-auto text-gray-300">
                              <path d="M4.878 4.34H3.551L.27 16.532h1.327l3.281-12.19z" fill="currentColor" />
                            </svg>
                          {/if}
                        </div>
                      </li>
                    {/each}
                  </ol>
                </nav>
              {/if}

              <div class="mx-auto mt-8 max-w-2xl px-4 sm:px-6 lg:max-w-7xl lg:px-8">
                <div class="lg:grid lg:auto-rows-min lg:grid-cols-12 lg:gap-x-8">
                  <!-- Product info -->
                  <div class="lg:col-span-5 lg:col-start-8">
                    <div class="flex justify-between">
                      <h1 class="text-xl font-medium text-gray-900">{product.name}</h1>
                      <p class="text-xl font-medium text-gray-900">${product.price_info?.price}</p>
                    </div>

                    {#if product.rating}
                      <div class="mt-2">
                        <RatingDisplay rating={product.rating} size="md" />
                      </div>
                    {/if}

                    {#if product.availability}
                      {@const availInfo = getAvailabilityInfo(product.availability)}
                      <p class={`mt-2 ${availInfo.color}`}>
                        {availInfo.icon} {availInfo.text}
                      </p>
                    {/if}
                  </div>

                  <!-- Image gallery -->
                  <div class="mt-8 lg:col-span-7 lg:col-start-1 lg:row-span-3 lg:row-start-1 lg:mt-0">
                    <div class="grid grid-cols-1 lg:grid-cols-2 lg:grid-rows-3 lg:gap-8">
                      {#if allImages && allImages.length > 0}
                        <img 
                          src={allImages[currentImageIndex].url}
                          alt={product.name}
                          class="rounded-lg lg:col-span-2 lg:row-span-2"
                        />
                        {#each allImages as image}
                          <img 
                            src={image.url}
                            alt={product.name}
                            class="hidden rounded-lg lg:block"
                          />
                        {/each}
                      {/if}
                    </div>
                  </div>

                  <!-- Product details -->
                  <div class="mt-8 lg:col-span-5">
                    {#if product.hasVariant}
                      <!-- Color and Size Pickers -->
                      <div class="mt-4 flex flex-wrap gap-4">
                        <!-- In-stock colors -->
                        {#if variants?.inStockColors?.length}
                          <div class="w-full">
                            <ColorPicker 
                              colors={variants.inStockColors}
                              selectedColor={selectedColor}
                              onColorSelect={handleColorSelect}
                              title="In-Stock Colors"
                            />
                          </div>
                        {/if}

                        <!-- Out-of-stock colors -->
                        {#if variants?.outOfStockColors?.length}
                          <div class="w-full">
                            <ColorPicker 
                              colors={variants.outOfStockColors}
                              selectedColor={selectedColor}
                              onColorSelect={handleColorSelect}
                              title="Out of Stock Colors"
                              disabled={true}
                            />
                          </div>
                        {/if}

                        <!-- In-stock sizes -->
                        {#if variants?.inStockSizes?.length}
                          <div class="w-full">
                            <SizePicker 
                              sizes={variants.inStockSizes}
                              selectedSize={selectedSize}
                              onSizeSelect={handleSizeSelect}
                              title="In-Stock Sizes"
                            />
                          </div>
                        {/if}

                        <!-- Out-of-stock sizes -->
                        {#if variants?.outOfStockSizes?.length}
                          <div class="w-full">
                            <SizePicker 
                              sizes={variants.outOfStockSizes}
                              selectedSize={selectedSize}
                              onSizeSelect={handleSizeSelect}
                              title="Out of Stock Sizes"
                              disabled={true}
                            />
                          </div>
                        {/if}
                      </div>

                      <!-- Description -->
                      {#if product.description}
                        <div class="mt-10">
                          <h2 class="text-sm font-medium text-gray-900">Description</h2>
                          <div class="mt-4 space-y-4 text-sm/6 text-gray-500">
                            <p>{product.description}</p>
                          </div>
                        </div>
                      {/if}

                      <!-- Materials -->
                      {#if product.materials && product.materials.length > 0}
                        <div class="mt-8 border-t border-gray-200 pt-8">
                          <h2 class="text-sm font-medium text-gray-900">Materials</h2>
                          <div class="mt-4">
                            <ul role="list" class="list-disc space-y-1 pl-5 text-sm/6 text-gray-500 marker:text-gray-300">
                              {#each product.materials as material}
                                <li class="pl-2">{material}</li>
                              {/each}
                            </ul>
                          </div>
                        </div>
                      {/if}

                      <!-- Additional Attributes -->
                      {#if product.additional_attributes}
                        <div class="mt-8 border-t border-gray-200 pt-8">
                          <h2 class="text-sm font-medium text-gray-900">Additional Details</h2>
                          <div class="mt-4">
                            <dl class="divide-y divide-gray-100">
                              {#each Object.entries(product.additional_attributes) as [key, value]}
                                {#if value !== null}
                                  <div class="px-2 py-3 sm:grid sm:grid-cols-3 sm:gap-4">
                                    <dt class="text-sm font-medium text-gray-900 capitalize">{key}</dt>
                                    <dd class="mt-1 text-sm text-gray-500 sm:col-span-2 sm:mt-0">
                                      {#if typeof value === 'object' && value.text}
                                        <ul class="list-disc pl-5">
                                          {#each value.text as item}
                                            <li>{item}</li>
                                          {/each}
                                        </ul>
                                      {:else if typeof value === 'object'}
                                        {JSON.stringify(value)}
                                      {:else}
                                        {value}
                                      {/if}
                                    </dd>
                                  </div>
                                {/if}
                              {/each}
                            </dl>
                          </div>
                        </div>
                      {/if}

                      <!-- Customer Reviews -->
                      {#if product.review && product.review.length > 0}
                        <div class="mt-8 border-t border-gray-200 pt-8">
                          <div class="flex items-center justify-between">
                            <h2 class="text-sm font-medium text-gray-900">Customer Reviews</h2>
                            <span class="text-sm text-gray-500">{product.review.length} reviews</span>
                          </div>
                          <div class="mt-4">
                            <ReviewList reviews={product.review} />
                          </div>
                        </div>
                      {/if}
                    {/if}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </button>
    {/if}
  </div>