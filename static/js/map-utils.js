// Shared Leaflet utilities used by the dashboard and activity detail pages.

function decodePolyline(str) {
    let i = 0, lat = 0, lng = 0, coords = [];
    while (i < str.length) {
        let b, shift = 0, result = 0;
        do { b = str.charCodeAt(i++) - 63; result |= (b & 0x1f) << shift; shift += 5; }
        while (b >= 0x20);
        lat += (result & 1) ? ~(result >> 1) : (result >> 1);
        shift = result = 0;
        do { b = str.charCodeAt(i++) - 63; result |= (b & 0x1f) << shift; shift += 5; }
        while (b >= 0x20);
        lng += (result & 1) ? ~(result >> 1) : (result >> 1);
        coords.push([lat / 1e5, lng / 1e5]);
    }
    return coords;
}

function createTileLayer() {
    return L.tileLayer('https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png', {
        maxZoom: 19,
        subdomains: 'abcd',
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
    });
}
