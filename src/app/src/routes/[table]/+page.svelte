<script>
    import { onMount } from 'svelte';
    import { page } from '$app/stores';
    import ProductCard from '../../components/ProductCard.svelte';
    import Pagination from '../../components/Pagination.svelte';
    
    let products = [];
    let searchQuery = '';
    let searchResults = [];
    let loading = true;
    let searching = false;
    let expandedProductId = null;
    let currentPage = 1;
    let totalPages = 1;
    let totalProducts = 0;
    let perPage = 100;
    let pageSizeOptions = [100, 200, 300, 400];
    let totalSearchResults = 0;
    
    $: tableName = $page.params.table;

    // Rest of your App.svelte code...
</script>

<!-- Rest of your App.svelte template... --> 