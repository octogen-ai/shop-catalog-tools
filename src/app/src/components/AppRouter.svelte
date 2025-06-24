<script>
    import { Router, Link, Route } from "svelte-routing";
    import { navigate } from "svelte-routing";
    import CatalogSelector from "./CatalogSelector.svelte";
    import ProductList from "../routes/ProductList.svelte";
    import ProductView from "../routes/[table]/product/[id]/+page.svelte";
    import CrawlsView from "../routes/[table]/product/[id]/crawls/+page.svelte";

    export let url = "";
    export let currentCatalog;
    export let currentPath;

    function handleNavigate(path, e) {
        e.preventDefault();
        navigate(path);
        currentPath = path;
    }

    function handleCatalogChange(event) {
        const catalog = event.detail;
        window.location.href = `/${catalog}`;
    }
</script>

<Router {url}>
    <nav class="bg-gray-800">
        <div class="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
            <div class="flex h-16 items-center justify-between">
                <div class="flex flex-1 items-center justify-start">
                    <div class="flex space-x-4">
                        <Link 
                            to="/{currentCatalog}" 
                            class="rounded-md px-3 py-2 text-sm font-medium bg-gray-900 text-white"
                            on:click={(e) => handleNavigate(`/${currentCatalog}`, e)}
                        >
                            Products
                        </Link>
                    </div>
                    <div class="ml-6">
                        <CatalogSelector on:change={handleCatalogChange} />
                    </div>
                </div>
            </div>
        </div>
    </nav>

    <main class="container mx-auto px-4 py-8">
        <Route path="/:table/product/:id/crawls" component={CrawlsView} />
        <Route path="/:table/product/:id" component={ProductView} />
        <Route path="/:table" component={ProductList} />
    </main>
</Router> 