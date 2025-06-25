/**
 * Extracts the final (sale) and original (regular) prices from a product object
 * @param {Object} product - The product object
 * @return {Object} An object containing final and original prices formatted as currency
 */
export function getFormattedPrice(product) {
    if (!product) return { final: null, original: null };
    
    // Try to use current_price/original_price fields first
    if (typeof product.current_price === 'number') {
        const price = {
            final: new Intl.NumberFormat("en-US", {
                style: "currency",
                currency: product.priceCurrency || 'USD',
            }).format(product.current_price),
            original: product.original_price && product.original_price > product.current_price 
                ? new Intl.NumberFormat("en-US", {
                    style: "currency",
                    currency: product.priceCurrency || 'USD',
                }).format(product.original_price)
                : null
        };
        return price;
    }

    // If current_price is not available, try to extract from offers
    if (product.offers) {
        const { finalPrice, originalPrice } = extractPricesFromOffers(product.offers);
        
        if (finalPrice > 0) {
            return {
                final: new Intl.NumberFormat("en-US", {
                    style: "currency",
                    currency: product.offers.priceCurrency || 'USD',
                }).format(finalPrice),
                original: originalPrice > 0 && originalPrice > finalPrice
                    ? new Intl.NumberFormat("en-US", {
                        style: "currency",
                        currency: product.offers.priceCurrency || 'USD',
                    }).format(originalPrice)
                    : null
            };
        }
    }

    // Fallback
    return { final: "Price unavailable", original: null };
}

/**
 * Extracts final and original prices as raw numbers from offers
 * @param {Object} offers - The offers object from a product
 * @return {Object} An object with finalPrice and originalPrice as numbers
 */
export function extractPricesFromOffers(offers) {
    if (!offers) {
        return { finalPrice: 0, originalPrice: 0 };
    }

    // Case 1: Handle AggregateOffer
    if ('lowPrice' in offers && typeof offers.lowPrice === 'number') {
        return {
            finalPrice: offers.lowPrice,
            originalPrice: offers.highPrice && offers.highPrice > offers.lowPrice ? offers.highPrice : 0
        };
    }
    
    // Case 2: Handle PriceSpecification directly in offers
    if ('priceSpecification' in offers && offers.priceSpecification) {
        const priceSpec = offers.priceSpecification;
        
        // Check for CompoundPriceSpecification with priceComponent
        if (priceSpec.priceComponent && Array.isArray(priceSpec.priceComponent)) {
            let finalPrice = 0;
            let originalPrice = 0;
            
            for (const comp of priceSpec.priceComponent) {
                if (!comp.priceType || comp.priceType.toLowerCase().includes('saleprice')) {
                    finalPrice = parseFloat(comp.price) || 0;
                } else if (comp.priceType.toLowerCase().includes('regularprice')) {
                    originalPrice = parseFloat(comp.price) || 0;
                }
            }
            
            // If there's only a regular price but no sale price, use it as the final price
            if (finalPrice === 0 && originalPrice > 0 && priceSpec.priceComponent.length === 1) {
                finalPrice = originalPrice;
            }
            
            return { finalPrice, originalPrice };
        }
        
        // Simple price specification
        if ('price' in priceSpec && typeof priceSpec.price === 'number') {
            return {
                finalPrice: priceSpec.price,
                originalPrice: priceSpec.originalPrice || 0
            };
        }
    }
    
    // Case 3: Handle Offers array
    if ('offers' in offers && Array.isArray(offers.offers) && offers.offers.length > 0) {
        const firstOffer = offers.offers[0];
        
        if (firstOffer && firstOffer.priceSpecification) {
            if ('price' in firstOffer.priceSpecification && typeof firstOffer.priceSpecification.price === 'number') {
                return {
                    finalPrice: firstOffer.priceSpecification.price,
                    originalPrice: firstOffer.priceSpecification.originalPrice || 0
                };
            }
            
            // Check for CompoundPriceSpecification in the first offer
            if (firstOffer.priceSpecification.priceComponent && 
                Array.isArray(firstOffer.priceSpecification.priceComponent)) {
                let finalPrice = 0;
                let originalPrice = 0;
                
                for (const comp of firstOffer.priceSpecification.priceComponent) {
                    if (!comp.priceType || comp.priceType.toLowerCase().includes('saleprice')) {
                        finalPrice = parseFloat(comp.price) || 0;
                    } else if (comp.priceType.toLowerCase().includes('regularprice')) {
                        originalPrice = parseFloat(comp.price) || 0;
                    }
                }
                
                // If there's only a regular price but no sale price, use it as the final price
                if (finalPrice === 0 && 
                    originalPrice > 0 && 
                    firstOffer.priceSpecification.priceComponent.length === 1) {
                    finalPrice = originalPrice;
                }
                
                return { finalPrice, originalPrice };
            }
        }
    }

    // No match, default
    return { finalPrice: 0, originalPrice: 0 };
} 