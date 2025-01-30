<script>
    import { fade } from 'svelte/transition';
    import RatingDisplay from './RatingDisplay.svelte';
    import ReviewList from './ReviewList.svelte';
    import ColorPicker from './ColorPicker.svelte';
    import SizePicker from './SizePicker.svelte';
    import ImageGallery from './ImageGallery.svelte';
    import AdditionalAttributes from './AdditionalAttributes.svelte';
    import { getProductUniqueId } from '$lib/utils.js';

    export let product;
    export let expanded = false;
    export let onToggleExpand = () => {};

    const productId = getProductUniqueId(product);

    /**
     * The product now stores current_price (finalPrice) and original_price
     * at the top level, plus availability in product.offers?.availability.
     */

    // Combine primary image with additional images and remove duplicates
    $: allImages = product.image 
      ? [product.image.url, ...(product.images?.map(img => img.url) || [])].filter((url, index, self) => 
          index === self.findIndex(t => t === url)
        )
      : product.images?.map(img => img.url) || [];

    // Collect all unique image URLs from variants
    $: variantImages = product.hasVariant
      ? product.hasVariant.reduce((acc, variant) => {
          if (variant.image?.url) acc.push(variant.image.url);
          if (variant.images?.length > 0) {
            variant.images.forEach(img => acc.push(img.url));
          }
          return acc;
        }, [])
        .filter((url, index, self) => index === self.findIndex(t => t === url))
      : [];

    // Combine all unique image URLs
    $: combinedImages = [...allImages, ...variantImages]
      .filter((url, index, self) => index === self.findIndex(t => t === url))
      .map(url => ({ url })); // Convert back to object format for template compatibility

    let currentImageIndex = 0;
    let selectedColor = null;
    let selectedSize = null;
    
    // Helper function to interpret schema.org availability strings
    function schemaToLocalAvailability(schemaUrl) {
      if (!schemaUrl) return 'UNKNOWN';
      if (schemaUrl.includes('InStock')) return 'IN_STOCK';
      if (schemaUrl.includes('OutOfStock')) return 'OUT_OF_STOCK';
      if (schemaUrl.includes('PreOrder')) return 'PREORDER';
      if (schemaUrl.includes('BackOrder')) return 'BACKORDER';
      return 'UNKNOWN';
    }

    // Original helper to get icon/color for our local availability codes
    function getAvailabilityInfo(availability) {
      switch (availability) {
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

    // For variants
    function groupVariantsByImage(variants) {
      const inStockColors = new Set();
      const inStockSizes = new Set();
      const allColors = new Set();
      const allSizes = new Set();
      
      variants.forEach(variant => {
        let isInStock = true;
        if (variant.offers?.availability) {
          const localAvail = schemaToLocalAvailability(variant.offers.availability);
          isInStock = localAvail === 'IN_STOCK';
        }
        if (variant.color_info?.colors) {
          variant.color_info.colors.forEach(color => {
            allColors.add(color);
            if (isInStock) inStockColors.add(color);
          });
        }
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

    $: variants = product.hasVariant 
      ? Object.values(groupVariantsByImage(product.hasVariant))[0]
      : null;

    function nextImage() {
      if (combinedImages.length > 0) {
        currentImageIndex = (currentImageIndex + 1) % combinedImages.length;
      }
    }

    function previousImage() {
      if (combinedImages.length > 0) {
        currentImageIndex = (currentImageIndex - 1 + combinedImages.length) % combinedImages.length;
      }
    }

    $: {
      if (currentImageIndex >= combinedImages.length) {
        currentImageIndex = combinedImages.length - 1;
      }
      if (currentImageIndex < 0) {
        currentImageIndex = 0;
      }
    }

    function handleBackgroundClick(event) {
      if (event.target === event.currentTarget) {
        onToggleExpand();
      }
    }

    function handleEscape(event) {
      if (event.key === 'Escape') {
        onToggleExpand();
      }
    }
    function getOriginalPrice(product) {
      if (!product.offers) return null;

      // Handle Offer with CompoundPriceSpecification
      if (product.offers.priceSpecification?.priceComponent) {
        const regularPriceComponent = product.offers.priceSpecification.priceComponent.find(
          (component) => component.priceType === 'https://schema.org/RegularPrice'
        );
        if (regularPriceComponent) {
          return regularPriceComponent.price;
        }
      }

      // Handle AggregateOffer
      if (product.offers.highPrice) {
        return product.offers.highPrice;
      }

      // Handle single Offer
      if (product.offers.priceSpecification?.price) {
        return product.offers.priceSpecification.price;
      }

      // Handle list of Offers
      if (Array.isArray(product.offers.offers)) {
        const prices = product.offers.offers
          .map((offer) => {
            // Check for CompoundPriceSpecification within each Offer
            if (offer.priceSpecification?.priceComponent) {
              const regularPriceComponent = offer.priceSpecification.priceComponent.find(
                (component) => component.priceType === 'https://schema.org/RegularPrice'
              );
              if (regularPriceComponent) {
                return regularPriceComponent.price;
              }
            }
            // Fallback to price in PriceSpecification
            return offer.priceSpecification?.price;
          })
          .filter((price) => price != null);

        return prices.length > 0 ? Math.max(...prices) : null;
      }

      return null;
    }
    function getFinalPrice(product) {
      if (!product.offers) return null;

      // Handle Offer with CompoundPriceSpecification
      if (product.offers.priceSpecification?.priceComponent) {
        const salePriceComponent = product.offers.priceSpecification.priceComponent.find(
          (component) => component.priceType === 'https://schema.org/SalePrice'
        );
        if (salePriceComponent) {
          return salePriceComponent.price;
        }
        // If no sale price found, check for regular price
        const regularPriceComponent = product.offers.priceSpecification.priceComponent.find(
          (component) => component.priceType === 'https://schema.org/RegularPrice'
        );
        if (regularPriceComponent) {
          return regularPriceComponent.price;
        }
      }

      // Handle AggregateOffer
      if (product.offers.lowPrice) {
        return product.offers.lowPrice;
      }

      // Handle single Offer
      if (product.offers.priceSpecification?.price) {
        return product.offers.priceSpecification.price;
      }

      // Handle list of Offers
      if (Array.isArray(product.offers.offers)) {
        const prices = product.offers.offers
          .map((offer) => {
            // Check for CompoundPriceSpecification within each Offer
            if (offer.priceSpecification?.priceComponent) {
              const salePriceComponent = offer.priceSpecification.priceComponent.find(
                (component) => component.priceType === 'https://schema.org/SalePrice'
              );
              if (salePriceComponent) {
                return salePriceComponent.price;
              }
              const regularPriceComponent = offer.priceSpecification.priceComponent.find(
                (component) => component.priceType === 'https://schema.org/RegularPrice'
              );
              if (regularPriceComponent) {
                return regularPriceComponent.price;
              }
            }
            // Fallback to price in PriceSpecification
            return offer.priceSpecification?.price;
          })
          .filter((price) => price != null);

        return prices.length > 0 ? Math.min(...prices) : null;
      }

      return null;
    }
    $: {
      if (expanded) {
        document.addEventListener('keydown', handleEscape);
      } else {
        document.removeEventListener('keydown', handleEscape);
      }
    }

    function handleColorSelect(color) {
      selectedColor = color;
    }
    
    function handleSizeSelect(size) {
      selectedSize = size;
    }

    // Derived availability
    $: productLocalAvailability = product?.offers?.availability
      ? schemaToLocalAvailability(product.offers.availability)
      : 'UNKNOWN';
    $: availabilityInfo = getAvailabilityInfo(productLocalAvailability);

    function formatPrice(amount, currency = 'USD') {
      const currencyCode = currency || 'USD';
      return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: currencyCode,
      }).format(amount);
    }

    // Derived price
    $: finalPrice = getFinalPrice(product);
    $: originalPrice = getOriginalPrice(product);

    // Ensure the currency code defaults to 'USD' if undefined or null
    $: priceCurrency = product.offers?.priceCurrency || 'USD';

    $: finalPriceFormatted = finalPrice ? formatPrice(finalPrice, priceCurrency) : null;
    $: originalPriceFormatted = originalPrice ? formatPrice(originalPrice, priceCurrency) : null;
</script>

<div class="bg-white">
  {#if !expanded}
    <button 
      type="button"
      class="w-full h-full text-left cursor-pointer"
      on:click={onToggleExpand}
      aria-expanded={expanded}
      transition:fade={{ duration: 500 }}
    >
      <div class="bg-white rounded-lg shadow-md overflow-hidden h-full flex flex-col">
        <div class="relative">
          {#if combinedImages && combinedImages.length > 0}
            <img 
              in:fade={{ duration: 500 }}
              src={combinedImages[currentImageIndex].url} 
              alt={product.name} 
              class="w-full h-64 object-cover"
              on:error|stopPropagation
            />
            {#if combinedImages.length > 1}
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
          {:else}
            <div class="w-full h-64 flex items-center justify-center bg-gray-100">
              <p class="text-gray-500">No image available</p>
            </div>
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
                href={`/${product.catalog}/product/${product.productGroupID}`}
                class="text-gray-500 hover:text-gray-700"
                title="View Raw Data"
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
              <a
              href={`/${product.catalog}/product/${product.productGroupID}/crawls?url=${encodeURIComponent(product.url)}`}
              class="text-gray-500 hover:text-gray-700"
              title="View Crawl History"
              on:click|stopPropagation
              >
                <div class="relative group">
                  <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                    <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-12a1 1 0 10-2 0v4a1 1 0 00.293.707l2.828 2.829a1 1 0 101.415-1.415L11 9.586V6z" clip-rule="evenodd" />
                  </svg>
                  <div class="absolute hidden group-hover:block bg-gray-800 text-white text-sm rounded px-2 py-1 -mt-1 left-1/2 transform -translate-x-1/2 -translate-y-full z-[100]">
                    View crawl history
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

              <!-- Price section with optional strike-through original price -->
              {#if finalPriceFormatted}
                <p class="text-gray-600 mb-2">
                  {finalPriceFormatted}
                  {#if originalPriceFormatted && originalPrice > finalPrice}
                    <span class="text-gray-500 line-through ml-2">{originalPriceFormatted}</span>
                  {/if}
                </p>
              {:else}
                <p class="text-gray-600 mb-2">Price not available</p>
              {/if}

              <!-- Availability -->
              {#if productLocalAvailability !== 'UNKNOWN'}
                <p class={availabilityInfo.color}>
                  {availabilityInfo.icon} {availabilityInfo.text}
                  {#if variants}
                    <span class="text-sm text-gray-600">
                      ({variants.inStockColors.length + variants.inStockSizes.length} in stock, 
                      {variants.outOfStockColors.length + variants.outOfStockSizes.length} out of stock)
                    </span>
                  {/if}
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
      on:keydown={(e) => e.key === 'Escape' && onToggleExpand()}
      aria-label="Product details"
      transition:fade={{ duration: 500 }}
    >
      <div role="dialog" aria-modal="true" class="min-h-screen px-4 flex items-center justify-center">
        <div class="bg-white w-full max-w-7xl rounded-lg shadow-xl">
          <!-- Close button -->
          <div class="flex justify-end p-4">
            <button
              class="text-gray-500 hover:text-gray-700"
              on:click={() => onToggleExpand()}
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

                    <!-- Price section with optional strike-through original price -->
                    {#if finalPriceFormatted}
                      <p class="text-xl font-medium text-gray-900">
                        {finalPriceFormatted}
                        {#if originalPriceFormatted && originalPrice > finalPrice}
                          <span class="text-gray-500 line-through ml-2">{originalPriceFormatted}</span>
                        {/if}
                      </p>
                    {:else}
                      <p class="text-xl text-gray-600">Price not available</p>
                    {/if}
                  </div>

                  {#if product.rating}
                    <div class="mt-2">
                      <RatingDisplay rating={product.rating} size="md" />
                    </div>
                  {/if}

                  {#if productLocalAvailability !== 'UNKNOWN'}
                    <p class={`mt-2 ${availabilityInfo.color}`}>
                      {availabilityInfo.icon} {availabilityInfo.text}
                      {#if variants}
                        <span class="text-sm text-gray-600">
                          ({variants.inStockColors.length + variants.inStockSizes.length} in stock, 
                          {variants.outOfStockColors.length + variants.outOfStockSizes.length} out of stock)
                        </span>
                      {/if}
                    </p>
                  {/if}
                </div>

                <!-- Image gallery -->
                <ImageGallery 
                  images={combinedImages}
                  currentIndex={currentImageIndex}
                  productName={product.name}
                />

                <!-- Product details -->
                <div class="mt-8 lg:col-span-5">
                  {#if product.hasVariant}
                    <!-- Color and Size Pickers -->
                    <div class="mt-4 flex flex-wrap gap-4">
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

                    {#if product.description}
                      <div class="mt-10">
                        <h2 class="text-sm font-medium text-gray-900">Description</h2>
                        <div class="mt-4 space-y-4 text-sm/6 text-gray-500">
                          <p>{product.description}</p>
                        </div>
                      </div>
                    {/if}

                    {#if product.additional_attributes}
                      <AdditionalAttributes attributes={product.additional_attributes} />
                    {/if}
                  {:else}
                    <!-- No variants, just a single product -->
                    {#if product.description}
                      <div class="mt-10">
                        <h2 class="text-sm font-medium text-gray-900">Description</h2>
                        <div class="mt-4 space-y-4 text-sm/6 text-gray-500">
                          <p>{product.description}</p>
                        </div>
                      </div>
                    {/if}
                  {/if}

                  <!-- Review Section -->
                  {#if product.review?.length}
                    <div class="mt-10">
                      <ReviewList reviews={product.review} />
                    </div>
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