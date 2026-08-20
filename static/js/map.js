// Karte initialisieren, Startposition z.B. Mitte Deutschlands
var map = L.map('map').setView([51.1657, 10.4515], 6);

// Tile-Layer (OpenStreetMap)
L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19,
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
}).addTo(map);

// Beispiel-Marker
var marker = L.marker([52.52, 13.405]).addTo(map);
marker.bindPopup("<b>Berlin</b><br>Beispieltext");