<script>
  export let rating = null;
  export let size = "sm"; // sm, md, lg

  // Size classes mapping
  const sizeClasses = {
    sm: "w-4 h-4",
    md: "w-5 h-5",
    lg: "w-6 h-6"
  };

  // Generate array of 5 stars for rating
  function getRatingStars(rating) {
    return Array(5).fill(null).map((_, index) => ({
      filled: index < Math.floor(rating),
      half: index === Math.floor(rating) && rating % 1 >= 0.5
    }));
  }
</script>

{#if rating?.average_rating}
  <div class="flex items-center gap-1">
    <div class="flex">
      {#each getRatingStars(rating.average_rating) as star}
        <svg 
          class="{sizeClasses[size]} {star.filled ? 'text-yellow-400' : 'text-gray-300'}"
          fill="currentColor"
          viewBox="0 0 20 20"
          xmlns="http://www.w3.org/2000/svg"
        >
          {#if star.half}
            <defs>
              <linearGradient id="half-star">
                <stop offset="50%" stop-color="currentColor"/>
                <stop offset="50%" stop-color="#D1D5DB"/>
              </linearGradient>
            </defs>
            <path 
              fill="url(#half-star)"
              d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z"
            />
          {:else}
            <path 
              d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z"
            />
          {/if}
        </svg>
      {/each}
    </div>
    <span class="text-sm text-gray-600">
      {rating.average_rating.toFixed(1)}{#if rating.rating_count} ({rating.rating_count}){/if}
    </span>
  </div>
{/if} 