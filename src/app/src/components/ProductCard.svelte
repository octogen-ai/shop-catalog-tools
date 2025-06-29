<script>
    import { createEventDispatcher } from 'svelte';
    import RatingDisplay from './RatingDisplay.svelte';
    import { getFormattedPrice } from '../utils/price-utils';
    
    const dispatch = createEventDispatcher();

    export let product;
    export let initialExpanded = false;
    const hideDebugLink = true;
    
    let expanded = initialExpanded;
    let imgError = false;
    let currentImageIndex = 0;
    
    function toggleExpand() {
        expanded = !expanded;
        dispatch('click');
    }

    // Get product name
    function getProductName(product) {
        if (!product) return "Unknown Product";
        return product.name || "Unnamed Product";
    }

    // Get product images - reverting to original logic
    function getProductImages(product) {
        if (!product) return [];
        
        // Original implementation was accessing images differently
        if (product.images && Array.isArray(product.images)) {
            // The original implementation expected objects with url property
            return product.images.filter(img => img && img.url);
        }
        
        return [];
    }
    
    // Get safe image URL with error handling
    function getSafeImageUrl() {
        if (imgError || !productImages || productImages.length === 0) return "/placeholder.jpg";
        return productImages[currentImageIndex].url;
    }

    function nextImage() {
        if (productImages.length > 0) {
            currentImageIndex = (currentImageIndex + 1) % productImages.length;
        }
    }

    function previousImage() {
        if (productImages.length > 0) {
            currentImageIndex = (currentImageIndex - 1 + productImages.length) % productImages.length;
        }
    }
    
    // Get rating for display
    function getRatingForDisplay(product) {
        if (!product || !product.rating) return null;
        
        if (typeof product.rating === 'object' && product.rating !== null) {
            return product.rating;
        } else if (typeof product.rating === 'number') {
            return { average_rating: product.rating };
        }

        return null;
    }
    
    $: productImages = getProductImages(product);
    $: productName = getProductName(product);
    $: price = getFormattedPrice(product);
</script>

{#if !product}
    <div class="bg-white rounded-lg shadow-md p-4">
        Product data unavailable
    </div>
{:else if !expanded}
    <!-- Collapsed view (card) -->
    <div class="bg-white rounded-lg shadow-md overflow-hidden h-full flex flex-col cursor-pointer relative hover:shadow-lg transition-shadow duration-200" 
        on:click={toggleExpand}
        on:keydown={e => e.key === 'Enter' && toggleExpand()}
        tabindex="0"
        role="button"
        aria-label="Show product details">
        <!-- Product Image -->
        <div class="relative">
            <div class="w-full h-64 relative">
            <img 
                    src={getSafeImageUrl()}
                    alt={productName}
              class="w-full h-64 object-cover"
                    on:error={() => { imgError = true; }}
                />
            </div>
        </div>

        <!-- Product Info -->
        <div class="p-4 flex-1 flex flex-col">
            <!-- Top section with product name -->
            <div class="mb-2">
                <h3 class="text-lg font-semibold mb-2">{productName}</h3>
            </div>
            
            <!-- Rating and price section -->
            <div class="mb-4">
                <!-- Rating section -->
                {#if product.rating !== undefined}
                <div class="mb-2">
                        <RatingDisplay
                            rating={getRatingForDisplay(product)}
                            size="sm"
                            showCount={true}
                        />
                </div>
              {/if}

                <!-- Price section -->
                {#if price.final}
                <p class="text-gray-600 mb-2">
                        {price.final}
                        {#if price.original}
                            <span class="text-gray-500 line-through ml-2">
                                {price.original}
                    </span>
                  {/if}
                </p>
              {/if}
            </div>
            
            <!-- Subtle text indicator -->
            <div class="mt-auto text-right">
                <span class="text-xs text-indigo-600">Click for details</span>
          </div>
        </div>
      </div>
  {:else}
    <!-- Expanded view - using ProductOverview component -->
    <div class="fixed inset-0 bg-black bg-opacity-50 z-50 overflow-y-auto w-full" 
        role="dialog"
        aria-modal="true"
        aria-label="Product details">
        <div class="min-h-screen px-4 flex items-center justify-center">
            <section class="bg-white w-full max-w-7xl rounded-lg shadow-xl">
                <!-- Close button -->
                <div class="flex justify-end p-4">
                    <button
                        class="text-gray-500 hover:text-gray-700"
                        on:click={() => expanded = false}
                        aria-label="Close"
                    >
                        <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                        </svg>
                    </button>
                </div>

                {#await import('./ProductOverview.svelte') then { default: ProductOverview }}
                    <ProductOverview {product} />
                {/await}
            </section>
        </div>
    </div>
  {/if}