// Karte initialisieren, Startposition Mitte Deutschlands
var map = L.map('map').setView([51.1657, 10.4515], 6);

// Tile-Layer (OpenStreetMap)
L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19,
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
}).addTo(map);

// Standorte per fetch von /api/standorte laden
fetch('/api/standorte')
    .then(response => response.json())
    .then(standorte => {
        standorte.forEach(standort => {
            if (standort.lat === null || standort.lng === null) {
                return; // Zeilen ohne Koordinaten überspringen
            }

            var marker = L.marker([standort.lat, standort.lng]).addTo(map);

            var popupContent = `
                <b>${standort["Einrichtung"] || "Unbekannte Einrichtung"}</b><br>
                ${standort["Kreis"]}, ${standort["bundesland"]}<br>
                ${standort["Angaben zur Person"] || ""}
            `;

            marker.bindPopup(popupContent);
        });
    })
    .catch(error => {
        console.error('Fehler beim Laden der Standorte:', error);
    });