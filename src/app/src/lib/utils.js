/* comment  */
export function toTitleCase(str) {
    return str.split(/[-_]/).map(word => 
        word.charAt(0).toUpperCase() + word.slice(1)
    ).join(' ');
}

/**
 * Get the unique ID for a product.
 * @param {Object} product - The product object.
 * @returns {string} The unique ID for the product.
 */
export function getProductUniqueId(product) {
  return product.id ?? product.productGroupID;
} 

