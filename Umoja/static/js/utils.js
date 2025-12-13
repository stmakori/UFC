
/**
 * Umoja Farmer Connect - Utility Functions
 * Additional helper functions
 */

/**
 * Generate mock data for brokers
 */
function generateMockBrokers(count = 10) {
    const brokers = [];
    const produces = ['Maize', 'Beans', 'Tomatoes', 'Potatoes', 'Cabbage', 'Onions'];
    const locations = [
        { name: 'Nairobi', lat: -1.286389, lng: 36.817223 },
        { name: 'Kiambu', lat: -1.171500, lng: 36.835700 },
        { name: 'Machakos', lat: -1.517101, lng: 37.263428 },
        { name: 'Nakuru', lat: -0.303099, lng: 36.080025 },
        { name: 'Eldoret', lat: 0.514277, lng: 35.269779 }
    ];
    
    for (let i = 0; i < count; i++) {
        const location = locations[Math.floor(Math.random() * locations.length)];
        const produce = produces[Math.floor(Math.random() * produces.length)];
        
        brokers.push({
            id: i + 1,
            name: `${location.name} Broker ${i + 1}`,
            produce: produce,
            price: Math.floor(Math.random() * 50) + 20,
            location: location.name,
            lat: location.lat + (Math.random() - 0.5) * 0.1,
            lng: location.lng + (Math.random() - 0.5) * 0.1,
            distance: (Math.random() * 50).toFixed(1),
            collectionDate: generateFutureDate(),
            collectionTime: generateRandomTime(),
            verified: Math.random() > 0.3,
            rating: (Math.random() * 2 + 3).toFixed(1)
        });
    }
    
    return brokers;
}

/**
 * Generate future date
 */
function generateFutureDate() {
    const date = new Date();
    date.setDate(date.getDate() + Math.floor(Math.random() * 7));
    return date.toISOString().split('T')[0];
}

/**
 * Generate random time
 */
function generateRandomTime() {
    const hours = Math.floor(Math.random() * 12) + 6; // 6 AM to 6 PM
    const minutes = Math.floor(Math.random() * 4) * 15; // 0, 15, 30, 45
    return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}`;
}

/**
 * Generate mock routes
 */
function generateMockRoutes(count = 5) {
    const routes = [];
    const produces = ['Maize', 'Beans', 'Tomatoes', 'Potatoes', 'Cabbage'];
    
    for (let i = 0; i < count; i++) {
        routes.push({
            id: i + 1,
            name: `Route ${i + 1}`,
            produce: produces[Math.floor(Math.random() * produces.length)],
            stops: Math.floor(Math.random() * 5) + 3,
            date: generateFutureDate(),
            status: ['Active', 'Scheduled', 'Completed'][Math.floor(Math.random() * 3)],
            farmers: Math.floor(Math.random() * 20) + 5,
            totalQuantity: Math.floor(Math.random() * 500) + 100
        });
    }
    
    return routes;
}

/**
 * Generate mock transactions
 */
function generateMockTransactions(count = 10) {
    const transactions = [];
    const produces = ['Maize', 'Beans', 'Tomatoes', 'Potatoes', 'Cabbage'];
    const types = ['Sale', 'Purchase'];
    
    for (let i = 0; i < count; i++) {
        const quantity = Math.floor(Math.random() * 200) + 50;
        const price = Math.floor(Math.random() * 50) + 20;
        
        transactions.push({
            id: `TXN${1000 + i}`,
            type: types[Math.floor(Math.random() * types.length)],
            produce: produces[Math.floor(Math.random() * produces.length)],
            quantity: quantity,
            price: price,
            total: quantity * price,
            date: generatePastDate(),
            status: ['Completed', 'Pending', 'Processing'][Math.floor(Math.random() * 3)]
        });
    }
    
    return transactions;
}

/**
 * Generate past date
 */
function generatePastDate() {
    const date = new Date();
    date.setDate(date.getDate() - Math.floor(Math.random() * 30));
    return date.toISOString().split('T')[0];
}

/**
 * Filter items by search term
 */
function filterItems(items, searchTerm, keys) {
    if (!searchTerm) return items;
    
    const term = searchTerm.toLowerCase();
    return items.filter(item => {
        return keys.some(key => {
            const value = item[key];
            return value && value.toString().toLowerCase().includes(term);
        });
    });
}

/**
 * Sort items
 */
function sortItems(items, key, order = 'asc') {
    return [...items].sort((a, b) => {
        let aVal = a[key];
        let bVal = b[key];
        
        // Handle numbers
        if (typeof aVal === 'number' && typeof bVal === 'number') {
            return order === 'asc' ? aVal - bVal : bVal - aVal;
        }
        
        // Handle strings
        aVal = aVal.toString().toLowerCase();
        bVal = bVal.toString().toLowerCase();
        
        if (order === 'asc') {
            return aVal < bVal ? -1 : aVal > bVal ? 1 : 0;
        } else {
            return aVal > bVal ? -1 : aVal < bVal ? 1 : 0;
        }
    });
}

/**
 * Paginate items
 */
function paginateItems(items, page, perPage) {
    const start = (page - 1) * perPage;
    const end = start + perPage;
    
    return {
        items: items.slice(start, end),
        totalPages: Math.ceil(items.length / perPage),
        currentPage: page,
        totalItems: items.length
    };
}

/**
 * Export to CSV
 */
function exportToCSV(data, filename) {
    if (data.length === 0) return;
    
    const headers = Object.keys(data[0]);
    const csv = [
        headers.join(','),
        ...data.map(row => 
            headers.map(header => {
                const value = row[header];
                return typeof value === 'string' && value.includes(',') 
                    ? `"${value}"` 
                    : value;
            }).join(',')
        )
    ].join('\n');
    
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${filename}.csv`;
    a.click();
    window.URL.revokeObjectURL(url);
}

/**
 * Format file size
 */
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
}

/**
 * Get query parameter
 */
function getQueryParam(param) {
    const urlParams = new URLSearchParams(window.location.search);
    return urlParams.get(param);
}

/**
 * Set query parameter
 */
function setQueryParam(param, value) {
    const url = new URL(window.location);
    url.searchParams.set(param, value);
    window.history.pushState({}, '', url);
}

// Export functions
window.UmojaUtils = {
    generateMockBrokers,
    generateMockRoutes,
    generateMockTransactions,
    filterItems,
    sortItems,
    paginateItems,
    exportToCSV,
    formatFileSize,
    getQueryParam,
    setQueryParam
};