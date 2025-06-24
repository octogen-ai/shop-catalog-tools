<script>
    import { createEventDispatcher } from 'svelte';
    import RatingDisplay from './RatingDisplay.svelte';
    
    const dispatch = createEventDispatcher();

    export let product;
    export let initialExpanded = false;
    export let hideDebugLink = true;
    
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

    // Get formatted price
    function getFormattedPrice(product) {
        // Try to use current_price/original_price fields first
        if (typeof product.current_price === 'number') {
            const price = {
                final: new Intl.NumberFormat("en-US", {
                    style: "currency",
                    currency: product.priceCurrency || 'USD',
                }).format(product.current_price),
                original: product.original_price && product.original_price > product.current_price 
                    ? new Intl.NumberFormat("en-US", {
                        style: "currency",
                        currency: product.priceCurrency || 'USD',
                    }).format(product.original_price)
                    : null
            };
            return price;
      }

        // If current_price is not available, try to extract from offers
        if (product.offers) {
            const offers = product.offers;
            
            if ('priceSpecification' in offers && offers.priceSpecification) {
                // Handle PriceSpecification
                const priceSpec = offers.priceSpecification;
                if ('price' in priceSpec && typeof priceSpec.price === 'number') {
                    return {
                        final: new Intl.NumberFormat("en-US", {
                            style: "currency",
                            currency: priceSpec.priceCurrency || 'USD',
                        }).format(priceSpec.price),
                        original: null
                    };
    }
            } else if ('lowPrice' in offers && typeof offers.lowPrice === 'number') {
                // Handle AggregateOffer
                return {
                    final: new Intl.NumberFormat("en-US", {
                        style: "currency",
                        currency: offers.priceCurrency || 'USD',
                    }).format(offers.lowPrice),
                    original: offers.highPrice && offers.highPrice > offers.lowPrice
                        ? new Intl.NumberFormat("en-US", {
                            style: "currency",
                            currency: offers.priceCurrency || 'USD',
                        }).format(offers.highPrice)
                        : null
                };
            } else if ('offers' in offers && Array.isArray(offers.offers) && offers.offers.length > 0) {
                // Handle Offers array
                const firstOffer = offers.offers[0];
                if (firstOffer && firstOffer.priceSpecification && 'price' in firstOffer.priceSpecification && 
                    typeof firstOffer.priceSpecification.price === 'number') {
                    return {
                        final: new Intl.NumberFormat("en-US", {
                            style: "currency",
                            currency: firstOffer.priceSpecification.priceCurrency || 'USD',
                        }).format(firstOffer.priceSpecification.price),
                        original: null
                    };
                }
            }
        }

        // Fallback
        return { final: "Price unavailable", original: null };
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
    <div class="bg-white rounded-lg shadow-md overflow-hidden h-full flex flex-col cursor-pointer relative hover:shadow-lg transition-shadow duration-200" on:click={toggleExpand}>
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
    <div class="fixed inset-0 bg-black bg-opacity-50 z-50 overflow-y-auto w-full" on:click={() => expanded = false}>
        <div class="min-h-screen px-4 flex items-center justify-center">
            <div class="bg-white w-full max-w-7xl rounded-lg shadow-xl" on:click|stopPropagation>
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
                    <ProductOverview {product} {hideDebugLink} />
                {/await}
          </div>
        </div>
      </div>
  {/if}