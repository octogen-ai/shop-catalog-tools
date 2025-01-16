/** @type {import('./$types').PageLoad} */
export function load({ params }) {
    console.log('Load function called with params:', params);
    
    // Ensure we have the required parameters
    if (!params.table || !params.id) {
        throw new Error('Missing required route parameters');
    }

    return {
        table: params.table,
        id: params.id
    };
} 