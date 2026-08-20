// Karte initialisieren, Startposition Mitte Deutschlands
var deutschlandBounds = L.latLngBounds(
    L.latLng(47.0, 5.5),   // Südwesten
    L.latLng(56.2, 15.5)   // Nordosten
);

var map = L.map('map', {
    minZoom: 5,
    maxZoom: 10,
    maxBounds: deutschlandBounds,
    maxBoundsViscosity: 1.0  // verhindert komplett das Rausziehen über die Grenze
}).setView([51.1657, 10.4515], 6);

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
                <b>Kreis:</b> ${standort["Kreis"]}, ${standort["bundesland"]}<br>
                <b>Landesärztekammer:</b> ${standort["Landesärztekammer"] || "-"}<br>
                <b>Art:</b> ${standort["ambulant/stationär/niedergelassen"] || "-"}<br>
                <b>Weiterbildungsermächtigung:</b> ${standort["Weiterbildungsermächtigung für Nephrologie"] || "-"}<br>
                <b>Befugnis:</b> ${standort["Befugnis"] || "-"}<br>
                <b>Angaben zur Person:</b> ${standort["Angaben zur Person"] || "-"}
            `;

            marker.bindPopup(popupContent);
        });
    })
    .catch(error => {
        console.error('Fehler beim Laden der Standorte:', error);
    });