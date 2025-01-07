<script>
    import { onMount } from 'svelte';
    import { goto } from '$app/navigation';

    onMount(() => {
        // Redirect to the anntaylor catalog by default
        goto('/anntaylor');
    });
</script>

<div class="flex items-center justify-center h-screen">
    <p class="text-gray-600">Redirecting to catalog...</p>
</div> 