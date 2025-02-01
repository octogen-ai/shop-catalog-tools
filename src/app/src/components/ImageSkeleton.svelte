<script>
  export let compact = false;
</script>

<div class="animate-pulse">
  {#if compact}
    <div class="h-64 bg-gray-200 rounded-lg" />
  {:else}
    <div class="grid grid-cols-1 lg:grid-cols-2 lg:grid-rows-3 gap-4">
      <!-- Main large skeleton -->
      <div class="rounded-lg lg:col-span-2 lg:row-span-2 w-full h-[32rem] bg-gray-200" />
      
      <!-- Thumbnail skeletons -->
      <div class="hidden lg:block rounded-lg w-full h-[16rem] bg-gray-200" />
      <div class="hidden lg:block rounded-lg w-full h-[16rem] bg-gray-200" />
    </div>
  {/if}
</div> 