const fetchFilteredProducts = async (filter, page = 1) => {
    try {
        const response = await fetch(
            `${apiBase}/api/${tableName}/filter?` + 
            new URLSearchParams({
                filter_string: filter,
                page: page.toString(),
                per_page: itemsPerPage.toString()
            })
        );
        const data = await response.json();
        // ... rest of the function
    } catch (error) {
        console.error('Error fetching filtered products:', error);
    }
}; 