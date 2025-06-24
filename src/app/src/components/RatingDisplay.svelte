<script>
  import { Star } from 'lucide-svelte';

  export let rating = null;
  export let size = "md"; // sm, md, lg
  export let showValue = true;
  export let showCount = true;

  // Map size to icon dimensions
  const sizeMap = {
    sm: 14,
    md: 16,
    lg: 20
  };

  // Extract rating value and count
  $: ratingValue = 0;
  $: ratingCount = 0;
  $: {
    if (typeof rating === 'object' && rating !== null) {
      ratingValue = rating.average_rating || 0;
      ratingCount = rating.rating_count || 0;
    } else if (typeof rating === 'number' && !isNaN(rating)) {
      ratingValue = rating;
    }
  }

  // Generate array of 5 stars for rating
  $: stars = Array(5).fill(null).map((_, index) => ({
    filled: index < Math.floor(ratingValue),
    half: index === Math.floor(ratingValue) && ratingValue % 1 >= 0.5
  }));
</script>

{#if ratingValue > 0}
  <div class="flex items-center">
    <div class="flex items-center">
      {#each stars as star, i}
        <div class="relative">
          <!-- Full or empty star -->
          <Star
            size={sizeMap[size]}
            class={star.filled || star.half ? "text-yellow-400" : "text-gray-300"}
            fill={star.filled ? "currentColor" : "none"}
          />

          <!-- Half star overlay -->
          {#if star.half}
            <div class="absolute inset-0 overflow-hidden w-1/2">
              <Star
                size={sizeMap[size]}
                class="text-yellow-400"
                fill="currentColor"
              />
            </div>
          {/if}
        </div>
      {/each}
    </div>

    {#if showValue}
      <span class="text-gray-500 text-xs ml-2">
        {ratingValue.toFixed(1)}
        {#if showCount && ratingCount > 0}
          ({ratingCount})
        {/if}
      </span>
    {/if}
  </div>
{/if} 