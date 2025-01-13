<script>
  import RatingDisplay from './RatingDisplay.svelte';
  export let reviews = [];

  // Format date to be more readable
  function formatDate(dateString) {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  }
</script>

<div class="space-y-8">
  {#each reviews as review}
    <div class="border-b border-gray-200 pb-8 last:border-b-0">
      <div class="flex items-start justify-between">
        <div class="flex-1">
          <div class="flex items-center gap-4">
            <RatingDisplay 
              rating={{ 
                average_rating: review.reviewRating.average_rating,
                rating_count: null 
              }} 
              size="sm" 
            />
            <p class="text-sm text-gray-600">
              {review.author.name} · {formatDate(review.datePublished)}
            </p>
          </div>
          <p class="mt-2 text-gray-700 whitespace-pre-line">
            {review.reviewBody}
          </p>
        </div>
      </div>
    </div>
  {/each}
</div> 