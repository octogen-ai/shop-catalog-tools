<script>
    import { onMount } from 'svelte';
    import RatingDisplay from './RatingDisplay.svelte';
    import { Star, ExternalLink, Code } from 'lucide-svelte';
    import { getFormattedPrice } from '../utils/price-utils';
    
    export let product;
    export let onAddToCart = null;
    export let brandLogo = null;
    const justification = null;
    const isStreaming = false;
    export const hideDebugLink = true;
    
    // State
    let selectedImageIndex = 0;
    let imageError = {};
    let swatchImgErrors = {};
    let showJsonData = false;
    let copySuccess = false;
    
    // Helper functions
    function getProductName(product) {
        if (!product) return "Unknown Product";
        return product.name || "Unnamed Product";
    }
    
    function getBrandName(product) {
        if (!product) return null;
        return product.brand || null;
    }
    
    function getProductImages(product) {
        if (!product) return [];
        
        // Original implementation expected objects with url property
        if (product.images && Array.isArray(product.images)) {
            // Filter for valid image objects with url property
            return product.images.filter(img => img && img.url);
        }
        
        return [];
    }
    
    function getRatingForDisplay(product) {
        if (!product || !product.rating) return null;
        
        if (typeof product.rating === 'object' && product.rating !== null) {
            return product.rating;
        } else if (typeof product.rating === 'number') {
            return { average_rating: product.rating };
        }
        
        return null;
    }
    
    function formatArrayFeature(arr) {
        if (!arr || !Array.isArray(arr)) return null;
        return arr.join(', ');
    }
    
    // Format reviews into a usable format
    function getFormattedReviews() {
        if (!product.review || !Array.isArray(product.review) || product.review.length === 0) {
            return [];
        }

        return product.review.map(review => {
            if (!review) return {
                id: `review-${Math.random().toString(36).substring(2, 9)}`,
                title: 'Review',
                rating: 5,
                content: '',
                author: 'Anonymous',
                date: new Date().toLocaleDateString(),
                datetime: new Date().toISOString()
            };

            // Extract rating from reviewRating safely
            const ratingValue = review.reviewRating 
                ? (review.reviewRating.average_rating ?? 5) 
                : 5;

            // Ensure review has all required fields
            return {
                id: `review-${Math.random().toString(36).substring(2, 9)}`,
                title: 'Review',
                rating: ratingValue,
                content: review.reviewBody || '',
                author: review.author?.name || 'Anonymous',
                date: review.datePublished || new Date().toLocaleDateString(),
                datetime: review.datePublished || new Date().toISOString()
            };
        });
    }
    
    // Get availability status
    function getAvailabilityInfo() {
        if (product.offers) {
            // Handle various forms of offers
            const availability = 
                (typeof product.offers === 'object' && 'availability' in product.offers) 
                    ? product.offers.availability 
                    : (Array.isArray(product.offers) && product.offers[0]?.availability) || '';

            if (String(availability).toLowerCase().includes('instock')) {
                return { text: 'In stock', inStock: true };
            } else if (String(availability).toLowerCase().includes('outofstock')) {
                return { text: 'Out of stock', inStock: false };
            }
        }

        return { text: 'Check availability', inStock: true };
    }
    
    const reviews = getFormattedReviews();
    const availability = getAvailabilityInfo();
    const price = getFormattedPrice(product);
    const productImages = getProductImages(product);
    
    const reviewCount = product.rating
        ? (typeof product.rating === 'object' && product.rating !== null && 'rating_count' in product.rating
            ? (product.rating.rating_count || 0)
            : reviews.length)
        : reviews.length;
    
    // Format JSON data with proper indentation
    function formatJsonData() {
        try {
            // Use 2 spaces for better readability and to avoid excessive width
            const formattedJson = JSON.stringify(product, null, 2);
            
            // Ensure we have a valid string to return
            if (!formattedJson) {
                return "No product data available";
            }
            
            return formattedJson;
        } catch (error) {
            console.error("Error formatting product JSON:", error);
            return "Error parsing product data";
        }
    }
    
    // Toggle JSON modal
    function toggleJsonModal(e) {
        e.stopPropagation();
        showJsonData = !showJsonData;
    }
    
    // Copy JSON data to clipboard
    function copyToClipboard() {
        try {
            navigator.clipboard.writeText(formatJsonData());
            copySuccess = true;
            
            // Reset copy success message after 2 seconds
            setTimeout(() => {
                copySuccess = false;
            }, 2000);
        } catch (error) {
            console.error("Failed to copy to clipboard:", error);
        }
    }
    
    // Navigation functions for the image gallery
    function goToNextImage() {
        if (productImages.length > 0) {
            selectedImageIndex = (selectedImageIndex + 1) % productImages.length;
        }
    }
    
    function goToPreviousImage() {
        if (productImages.length > 0) {
            selectedImageIndex = selectedImageIndex === 0 ? productImages.length - 1 : selectedImageIndex - 1;
        }
    }
    
    function classNames(...classes) {
        return classes.filter(Boolean).join(' ');
    }
</script>

{#if !product}
    <div class="p-4">Product data unavailable</div>
{:else}
    <div class="pb-16 pt-6 sm:pb-24">
        <div class="mx-auto max-w-2xl px-4 sm:px-6 lg:max-w-7xl lg:px-8">
            <!-- Breadcrumbs -->
            {#if product.breadcrumbList && product.breadcrumbList.itemListElement && product.breadcrumbList.itemListElement.length > 0}
                <nav class="flex mb-6" aria-label="Breadcrumb">
                    <ol class="flex items-center space-x-2">
                        {#each product.breadcrumbList.itemListElement as item, index}
                            <li>
                                <div class="flex items-center">
                                    {#if index > 0}
                                        <span class="mx-2 text-gray-400">/</span>
                                    {/if}
                                    <span class="text-sm font-medium text-gray-500 hover:text-gray-700">
                                        {item.item.name}
                                    </span>
                                </div>
                            </li>
                        {/each}
                    </ol>
                </nav>
            {/if}

            <div class="lg:grid lg:auto-rows-min lg:grid-cols-12 lg:gap-x-8">
                <!-- Product title, price, reviews -->
                <div class="lg:col-span-5 lg:col-start-8">
                    <div class="flex justify-between">
                        <h1 class="text-xl font-medium text-gray-900">{getProductName(product)}</h1>
                        <p class="text-xl font-medium text-gray-900">
                            {price.final}
                            {#if price.original}
                                <span class="text-gray-500 line-through ml-2">
                                    {price.original}
                                </span>
                            {/if}
                        </p>
                    </div>

                    <!-- View JSON Data button -->
                    <div class="mt-2 flex items-center space-x-3">
                        <button
                            type="button"
                            on:click={toggleJsonModal}
                            class="inline-flex items-center text-xs text-gray-500 hover:text-gray-700"
                        >
                            <Code size={12} class="mr-1" />
                            View raw data
                        </button>
                    </div>

                    <!-- JSON Data Modal -->
                    {#if showJsonData}
                        <div class="fixed inset-0 z-50 overflow-y-auto" aria-labelledby="modal-title" role="dialog" aria-modal="true">
                            <div class="flex items-center justify-center min-h-screen p-4">
                                <!-- Backdrop -->
                                <div class="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity" aria-hidden="true" on:click={toggleJsonModal}></div>

                                <!-- Modal panel -->
                                <div class="relative bg-white rounded-lg shadow-xl w-full max-w-4xl max-h-[90vh] overflow-hidden">
                                    <!-- Header -->
                                    <div class="bg-gray-50 px-6 py-4 border-b border-gray-200 flex justify-between items-center">
                                        <h3 class="text-lg font-semibold text-gray-900" id="modal-title">
                                            Raw Product Data (JSON)
                                        </h3>
                                        <button
                                            type="button"
                                            class="text-gray-400 hover:text-gray-500"
                                            on:click={toggleJsonModal}
                                            aria-label="Close"
                                        >
                                            <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                                            </svg>
                                        </button>
                                    </div>
                                    
                                    <!-- Content with light background -->
                                    <div class="bg-white p-4 overflow-auto" style="max-height: 70vh;">
                                        <!-- Copy button -->
                                        <div class="flex justify-end mb-2">
                                            <button
                                                type="button"
                                                on:click={copyToClipboard}
                                                class="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                                            >
                                                <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 mr-1.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7v8a2 2 0 002 2h6M8 7V5a2 2 0 012-2h4.586a1 1 0 01.707.293l4.414 4.414a1 1 0 01.293.707V15a2 2 0 01-2 2h-2" />
                                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 3v4a1 1 0 001 1h4" />
                                                </svg>
                                                {copySuccess ? "Copied!" : "Copy to clipboard"}
                                            </button>
                                        </div>
                                        
                                        <!-- JSON content -->
                                        <div class="bg-gray-50 p-4 rounded-md border border-gray-200">
                                            <pre class="text-sm font-mono text-gray-900 whitespace-pre leading-relaxed overflow-auto" style="max-height: 60vh;">{formatJsonData()}</pre>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    {/if}

                    <!-- Reviews summary -->
                    {#if product.rating !== undefined}
                        <div class="mt-4">
                            <h2 class="sr-only">Reviews</h2>
                            <div class="flex items-center">
                                <RatingDisplay
                                    rating={getRatingForDisplay(product)}
                                    size="md"
                                    showValue={true}
                                    showCount={true}
                                />

                                {#if reviewCount > 0}
                                    <div class="ml-4 flex">
                                        <a href="#reviews" class="text-sm font-medium text-indigo-600 hover:text-indigo-500">
                                            See all {reviewCount} reviews
                                        </a>
                                    </div>
                                {/if}
                            </div>
                        </div>
                    {/if}
                </div>

                <!-- Image gallery with brand logo overlay -->
                <div class="mt-8 lg:col-span-7 lg:col-start-1 lg:row-span-3 lg:row-start-1 lg:mt-0 relative">
                    <h2 class="sr-only">Product images</h2>

                    <!-- Brand logo overlay - positioned in the top right corner -->
                    {#if brandLogo}
                        <div class="absolute top-4 right-4 z-10 bg-white p-2 rounded-full shadow-md border border-gray-100 group">
                            <img 
                                src={brandLogo} 
                                alt={getBrandName(product) || 'Brand'} 
                                width="80" 
                                height="80" 
                                class="rounded-full"
                            />
                            <span class="absolute hidden group-hover:block bg-gray-800 text-white text-xs rounded px-2 py-1 -mt-1 bottom-full transform -translate-x-1/2 left-1/2 mb-2">
                                {getBrandName(product)}
                            </span>
                        </div>
                    {/if}

                    <!-- Full-size image gallery with navigation -->
                    {#if productImages.length > 0}
                        <div class="relative">
                            <!-- Current image -->
                            <div class="relative aspect-square w-full overflow-hidden rounded-lg">
                                <img
                                    src={imageError[selectedImageIndex] ? '/ai_pfp.png' : productImages[selectedImageIndex]?.url || '/ai_pfp.png'}
                                    alt="{getProductName(product)} - Image {selectedImageIndex + 1}"
                                    class="h-full w-full object-cover object-center"
                                    on:error={() => imageError = { ...imageError, [selectedImageIndex]: true }}
                                />
                            </div>
                            
                            <!-- Navigation buttons - only show if there are multiple images -->
                            {#if productImages.length > 1}
                                <!-- Previous button -->
                                <button
                                    type="button"
                                    class="absolute left-4 top-1/2 -translate-y-1/2 rounded-full bg-white/80 p-2 text-gray-800 shadow-md hover:bg-white"
                                    on:click={goToPreviousImage}
                                >
                                    <span class="sr-only">Previous</span>
                                    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-5 h-5">
                                        <path stroke-linecap="round" stroke-linejoin="round" d="M15.75 19.5L8.25 12l7.5-7.5" />
                                    </svg>
                                </button>
                                
                                <!-- Next button -->
                                <button
                                    type="button"
                                    class="absolute right-4 top-1/2 -translate-y-1/2 rounded-full bg-white/80 p-2 text-gray-800 shadow-md hover:bg-white"
                                    on:click={goToNextImage}
                                >
                                    <span class="sr-only">Next</span>
                                    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-5 h-5">
                                        <path stroke-linecap="round" stroke-linejoin="round" d="M8.25 4.5l7.5 7.5-7.5 7.5" />
                                    </svg>
                                </button>
                                
                                <!-- Image counter -->
                                <div class="absolute bottom-4 left-1/2 -translate-x-1/2 rounded-full bg-black/70 px-3 py-1 text-xs text-white">
                                    {selectedImageIndex + 1} / {productImages.length}
                                </div>
                            {/if}
                        </div>
                        
                        <!-- Thumbnail navigation -->
                        {#if productImages.length > 1}
                            <div class="mt-4 flex justify-center">
                                <div class="grid grid-cols-6 gap-4">
                                    {#each productImages as image, index}
                                        <button
                                            type="button"
                                            class="relative rounded overflow-hidden {selectedImageIndex === index ? 'outline outline-2 outline-indigo-500' : ''}"
                                            on:click={() => selectedImageIndex = index}
                                        >
                                            <span class="sr-only">View image {index + 1}</span>
                                            <img
                                                src={imageError[index] ? '/ai_pfp.png' : image?.url || '/ai_pfp.png'}
                                                alt="{getProductName(product)} - thumbnail {index + 1}"
                                                class="h-16 w-16 object-cover object-center"
                                                on:error={() => imageError = { ...imageError, [index]: true }}
                                            />
                                            {#if selectedImageIndex === index}
                                                <div class="absolute inset-0 bg-indigo-500/10"></div>
                                            {/if}
                                        </button>
                                    {/each}
                                </div>
                            </div>
                        {/if}
                    {/if}
                    
                    <!-- Videos section -->
                    {#if product?.videos && Array.isArray(product.videos) && product.videos.length > 0}
                        <div class="mt-10">
                            <h2 class="text-lg font-medium text-gray-900 mb-4">Product Videos</h2>
                            <div class="grid grid-cols-1 gap-4">
                                {#each product.videos as video, videoIndex}
                                    <div class="border border-gray-200 rounded-lg overflow-hidden">
                                        {#if video.embedUrl}
                                            <div class="aspect-video w-full">
                                                <iframe
                                                    src={video.embedUrl}
                                                    class="w-full h-full"
                                                    title={video.name || `Product video ${videoIndex + 1}`}
                                                    allowFullScreen
                                                    frameBorder="0"
                                                    allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                                                />
                                            </div>
                                        {:else if video.contentUrl}
                                            <div class="aspect-video w-full">
                                                <video
                                                    src={video.contentUrl}
                                                    class="w-full h-full object-cover"
                                                    controls
                                                    preload="metadata"
                                                    poster={video.thumbnailUrl?.[0]}
                                                >
                                                    <track kind="captions" src="" label="English" srclang="en" />
                                                    Your browser does not support the video element.
                                                </video>
                                            </div>
                                        {:else if video.thumbnailUrl && video.thumbnailUrl.length > 0}
                                            <div class="aspect-video w-full relative bg-gray-100 flex items-center justify-center">
                                                <img
                                                    src={video.thumbnailUrl[0]}
                                                    alt={video.name || `Video thumbnail ${videoIndex + 1}`}
                                                    class="w-full h-full object-cover"
                                                />
                                                <div class="absolute inset-0 flex items-center justify-center">
                                                    <div class="bg-black bg-opacity-50 rounded-full p-4">
                                                        <svg xmlns="http://www.w3.org/2000/svg" class="h-12 w-12 text-white" viewBox="0 0 24 24" fill="currentColor">
                                                            <path d="M8 5v14l11-7z" />
                                                        </svg>
                                                    </div>
                                                </div>
                                                <p class="absolute bottom-2 w-full text-center text-white bg-black bg-opacity-50 py-1">
                                                    Video preview not available
                                                </p>
                                            </div>
                                        {/if}
                                        
                                        <!-- Video info -->
                                        <div class="p-3">
                                            {#if video.name}
                                                <h3 class="font-medium text-gray-900">{video.name}</h3>
                                            {/if}
                                            {#if video.description}
                                                <p class="text-sm text-gray-500 mt-1">{video.description}</p>
                                            {/if}
                                            {#if video.uploadDate}
                                                <p class="text-xs text-gray-400 mt-2">
                                                    Uploaded: {new Date(video.uploadDate).toLocaleDateString()}
                                                </p>
                                            {/if}
                                        </div>
                                    </div>
                                {/each}
                            </div>
                        </div>
                    {/if}
                </div>

                <!-- Product details section -->
                <div class="mt-8 lg:col-span-5">
                    <form on:submit|preventDefault={() => onAddToCart && onAddToCart()}>
                        <!-- Color picker if available -->
                        {#if product.color_info?.colors && product.color_info.colors.length > 0}
                            <div>
                                <h2 class="text-sm font-medium text-gray-900">Color</h2>
                                <div class="mt-2 flex items-center space-x-3">
                                    {#each product.color_info.colors as color}
                                        <div
                                            class="relative flex items-center justify-center rounded-full p-0.5 group"
                                        >
                                            <span class="sr-only">{color.label}</span>
                                            {#if color.swatch_url}
                                                <img
                                                    src={swatchImgErrors[color.label || ''] ? '/ai_pfp.png' : color.swatch_url}
                                                    alt={color.label}
                                                    class="h-8 w-8 rounded-full border border-black/10"
                                                    on:error={() => swatchImgErrors = { ...swatchImgErrors, [color.label || '']: true }}
                                                />
                                            {:else}
                                                <span
                                                    class="h-8 w-8 rounded-full border border-black/10 bg-gray-400"
                                                />
                                            {/if}
                                            <span class="absolute hidden group-hover:block bg-gray-800 text-white text-xs rounded px-2 py-1 -mt-1 bottom-full transform -translate-x-1/2 left-1/2 mb-2">
                                                {color.label}
                                            </span>
                                        </div>
                                    {/each}
                                </div>
                            </div>
                        {/if}

                        <!-- Size selector if available -->
                        {#if product.sizes && product.sizes.length > 0}
                            <div class="mt-6">
                                <h2 class="text-sm font-medium text-gray-900">Size</h2>
                                <div class="mt-2 grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-2">
                                    {#each product.sizes as size}
                                        <div
                                            class="flex h-12 w-full items-center justify-center rounded-md border py-2 px-3 text-sm font-medium uppercase hover:bg-gray-50 focus:outline-none"
                                        >
                                            <span class="truncate">{size}</span>
                                        </div>
                                    {/each}
                                </div>
                            </div>
                        {/if}

                        <!-- External link -->
                        {#if product.url}
                            <div class="mt-8">
                                <a
                                    href={product.url}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    class="w-full bg-indigo-600 border border-transparent rounded-md py-3 px-8 flex items-center justify-center text-base font-medium text-white hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                                >
                                    <ExternalLink size={18} class="mr-2" />
                                    View on retailer site
                                </a>
                            </div>
                        {/if}
                    </form>

                    <!-- Product description -->
                    {#if product.description}
                        <div class="mt-10">
                            <h2 class="text-sm font-medium text-gray-900">Description</h2>
                            <div
                                class="mt-4 prose prose-sm text-gray-500"
                            >
                                {@html product.description}
                            </div>
                        </div>
                    {/if}

                    <!-- Product details -->
                    {#if (product.materials?.length || product.fit || product.dimensions)}
                        <div class="mt-6 border-t border-gray-200 pt-6">
                            <h2 class="text-sm font-medium text-gray-900">Product details</h2>
                            <dl class="mt-4 space-y-4">
                                {#if product.materials && product.materials.length > 0}
                                    <div>
                                        <dt class="text-sm font-medium text-gray-600">Materials</dt>
                                        <dd class="mt-1 text-sm text-gray-500">
                                            {formatArrayFeature(product.materials)}
                                        </dd>
                                    </div>
                                {/if}
                                
                                {#if typeof product.fit === 'string' && product.fit}
                                    <div>
                                        <dt class="text-sm font-medium text-gray-600">Fit</dt>
                                        <dd class="mt-1 text-sm text-gray-500">{product.fit}</dd>
                                    </div>
                                {/if}
                                
                                {#if Array.isArray(product.fit) && product.fit.length > 0}
                                    <div>
                                        <dt class="text-sm font-medium text-gray-600">Fit</dt>
                                        <dd class="mt-1 text-sm text-gray-500">
                                            {formatArrayFeature(product.fit)}
                                        </dd>
                                    </div>
                                {/if}
                                
                                {#if product.dimensions}
                                    <div>
                                        <dt class="text-sm font-medium text-gray-600">Dimensions</dt>
                                        <dd class="mt-1 text-sm text-gray-500">{product.dimensions}</dd>
                                    </div>
                                {/if}
                                
                                {#if product.patterns && product.patterns.length > 0}
                                    <div>
                                        <dt class="text-sm font-medium text-gray-600">Pattern</dt>
                                        <dd class="mt-1 text-sm text-gray-500">
                                            {formatArrayFeature(product.patterns)}
                                        </dd>
                                    </div>
                                {/if}
                            </dl>
                        </div>
                    {/if}

                    <!-- Tags section -->
                    {#if product.tags && product.tags.length > 0}
                        <div class="mt-6 border-t border-gray-200 pt-6">
                            <h2 class="text-sm font-medium text-gray-900">Tags</h2>
                            <div class="mt-3 flex flex-wrap gap-2">
                                {#each product.tags as tag}
                                    <span 
                                        class="inline-flex items-center rounded-full bg-indigo-50 px-2.5 py-1 text-xs font-medium text-indigo-700"
                                    >
                                        {tag}
                                    </span>
                                {/each}
                            </div>
                        </div>
                    {/if}

                    <!-- Additional Attributes section -->
                    {#if product.additional_attributes && Object.keys(product.additional_attributes).length > 0}
                        <div class="mt-6 border-t border-gray-200 pt-6">
                            <h2 class="text-sm font-medium text-gray-900">Additional Attributes</h2>
                            <dl class="mt-4 space-y-4">
                                {#each Object.entries(product.additional_attributes).filter(entry => entry[1] !== null) as [key, value]}
                                    <div>
                                        <dt class="text-sm font-medium text-gray-600">{key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}</dt>
                                        <dd class="mt-1 text-sm text-gray-500">
                                            {#if value?.text && value.text.length > 0}
                                                {value.text.join(', ')}
                                            {:else if value?.numbers && value.numbers.length > 0}
                                                {value.numbers.map(n => n.toString()).join(', ')}
                                            {:else}
                                                N/A
                                            {/if}
                                        </dd>
                                    </div>
                                {/each}
                            </dl>
                        </div>
                    {/if}

                    <!-- Reviews section -->
                    {#if reviews.length > 0}
                        <section id="reviews" aria-labelledby="reviews-heading" class="mt-8 border-t border-gray-200 pt-8">
                            <h2 id="reviews-heading" class="text-lg font-medium text-gray-900">
                                Customer Reviews
                            </h2>
                            <div class="mt-6 space-y-10">
                                {#each reviews as review}
                                    <div class="border-b border-gray-200 pb-6">
                                        <h3 class="sr-only">Review by {review.author}</h3>

                                        <div class="flex items-center mb-4">
                                            <div class="flex items-center">
                                                {#each [0, 1, 2, 3, 4] as rating}
                                                    <Star
                                                        size={16}
                                                        class={classNames(
                                                            review.rating > rating ? 'text-yellow-400 fill-yellow-400' : 'text-gray-300',
                                                            'shrink-0'
                                                        )}
                                                    />
                                                {/each}
                                            </div>
                                            <p class="ml-3 text-sm text-gray-600">
                                                {review.rating} out of 5 stars
                                            </p>
                                        </div>

                                        <div class="flex space-x-4 text-sm text-gray-500">
                                            <div class="flex-none py-2">
                                                <span class="font-medium text-gray-900">{review.author}</span>
                                            </div>
                                            <div class="py-2">
                                                <span class="text-gray-500">
                                                    {review.date}
                                                </span>
                                            </div>
                                        </div>

                                        <h4 class="mt-4 text-sm font-medium text-gray-900">{review.title}</h4>

                                        <div
                                            class="mt-2 text-sm text-gray-600"
                                        >
                                            {@html review.content}
                                        </div>
                                    </div>
                                {/each}
                            </div>
                        </section>
                    {/if}
                </div>
            </div>
        </div>
    </div>
{/if}