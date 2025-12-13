/**
 * Umoja Farmer Connect - Map JavaScript
 * Handles map functionality using Leaflet.js
 */

let map;
let markers = [];
let userMarker;

/**
 * Initialize map
 */
function initMap(elementId = 'map', center = [-1.286389, 36.817223], zoom = 12) {
    // Create map instance
    map = L.map(elementId).setView(center, zoom);
    
    // Add OpenStreetMap tiles
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors',
        maxZoom: 19
    }).addTo(map);
    
    // Add user location if available
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(
            position => {
                const userLat = position.coords.latitude;
                const userLng = position.coords.longitude;
                
                // Add user marker
                userMarker = L.marker([userLat, userLng], {
                    icon: createCustomIcon('user')
                }).addTo(map);
                
                userMarker.bindPopup('<b>Your Location</b>').openPopup();
                
                // Center map on user location
                map.setView([userLat, userLng], 13);
            },
            error => {
                console.warn('Geolocation error:', error);
            }
        );
    }
    
    return map;
}

/**
 * Create custom icon
 */
function createCustomIcon(type = 'default') {
    const iconColors = {
        user: '#007bff',
        farmer: '#1B5E20',  // Dark green for nature theme
        broker: '#ffc107',
        stop: '#dc3545'
    };
    
    const color = iconColors[type] || iconColors.default;
    
    return L.divIcon({
        className: 'custom-marker',
        html: `
            <div style="
                background-color: ${color};
                width: 30px;
                height: 30px;
                border-radius: 50%;
                border: 3px solid white;
                box-shadow: 0 2px 5px rgba(0,0,0,0.3);
            "></div>
        `,
        iconSize: [30, 30],
        iconAnchor: [15, 15]
    });
}

/**
 * Add marker to map
 */
function addMarker(lat, lng, popupContent, type = 'default') {
    const marker = L.marker([lat, lng], {
        icon: createCustomIcon(type)
    }).addTo(map);
    
    if (popupContent) {
        marker.bindPopup(popupContent);
    }
    
    markers.push(marker);
    return marker;
}

/**
 * Add multiple markers
 */
function addMarkers(locations) {
    locations.forEach(location => {
        addMarker(
            location.lat,
            location.lng,
            location.popup,
            location.type
        );
    });
    
    // Fit bounds to show all markers
    if (markers.length > 0) {
        const group = L.featureGroup(markers);
        map.fitBounds(group.getBounds().pad(0.1));
    }
}

/**
 * Clear all markers
 */
function clearMarkers() {
    markers.forEach(marker => {
        map.removeLayer(marker);
    });
    markers = [];
}

/**
 * Draw route between points
 */
function drawRoute(points, color = '#1B5E20') {
    const polyline = L.polyline(points, {
        color: color,
        weight: 4,
        opacity: 0.7
    }).addTo(map);
    
    // Fit map to route
    map.fitBounds(polyline.getBounds());
    
    return polyline;
}

/**
 * Add circle radius
 */
function addCircle(lat, lng, radius, color = '#1B5E20') {
    const circle = L.circle([lat, lng], {
        color: color,
        fillColor: color,
        fillOpacity: 0.2,
        radius: radius * 1000 // Convert km to meters
    }).addTo(map);
    
    return circle;
}

/**
 * Calculate and display route
 */
async function calculateRoute(startLat, startLng, endLat, endLng) {
    // Using OSRM for routing (free alternative to Google Directions)
    const url = `https://router.project-osrm.org/route/v1/driving/${startLng},${startLat};${endLng},${endLat}?overview=full&geometries=geojson`;
    
    try {
        const response = await fetch(url);
        const data = await response.json();
        
        if (data.code === 'Ok') {
            const route = data.routes[0];
            const coordinates = route.geometry.coordinates.map(coord => [coord[1], coord[0]]);
            
            // Draw route
            const polyline = drawRoute(coordinates);
            
            // Add start and end markers
            addMarker(startLat, startLng, '<b>Start</b>', 'stop');
            addMarker(endLat, endLng, '<b>End</b>', 'stop');
            
            return {
                distance: (route.distance / 1000).toFixed(2), // km
                duration: Math.round(route.duration / 60), // minutes
                polyline: polyline
            };
        }
    } catch (error) {
        console.error('Route calculation error:', error);
        return null;
    }
}

/**
 * Search location by address
 */
async function searchLocation(address) {
    const url = `https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(address)}`;
    
    try {
        const response = await fetch(url);
        const data = await response.json();
        
        if (data.length > 0) {
            const result = data[0];
            return {
                lat: parseFloat(result.lat),
                lng: parseFloat(result.lon),
                displayName: result.display_name
            };
        }
        return null;
    } catch (error) {
        console.error('Location search error:', error);
        return null;
    }
}

/**
 * Get nearby locations
 */
function getNearbyLocations(centerLat, centerLng, locations, radiusKm) {
    return locations.filter(location => {
        const distance = window.UmojaFC.calculateDistance(
            centerLat,
            centerLng,
            location.lat,
            location.lng
        );
        return distance <= radiusKm;
    });
}

// Export functions
window.UmojaMap = {
    initMap,
    addMarker,
    addMarkers,
    clearMarkers,
    drawRoute,
    addCircle,
    calculateRoute,
    searchLocation,
    getNearbyLocations,
    getMap: () => map
};