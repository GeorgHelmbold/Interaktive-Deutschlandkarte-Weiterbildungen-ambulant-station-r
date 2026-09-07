var map = L.map('map', {
    minZoom: 6,
    maxZoom: 16,
    maxBounds: L.latLngBounds(L.latLng(46.0, 2.5), L.latLng(57.0, 18.5)),
    maxBoundsViscosity: 0.5
}).setView([51.1657, 10.4515], 6);

L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19,
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
}).addTo(map);

// Farbfunktion für Leaflet-Marker
function erstelleIcon(farbe) {
    return new L.Icon({
        iconUrl: `https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-${farbe}.png`,
        shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
        iconSize: [25, 41],
        iconAnchor: [12, 41],
        popupAnchor: [1, -34],
        shadowSize: [41, 41]
    });
}

var icons = {
    blau: erstelleIcon('blue'),
    rot: erstelleIcon('red'),
    lila: erstelleIcon('violet'),
    grau: erstelleIcon('grey')
};

// Ermittelt die passende Farbe für eine Gruppe von Standorten
function ermittleFarbe(gruppe) {
    var hatAmbulant = false;
    var hatStationaer = false;

    gruppe.forEach(standort => {
        var typ = (standort["ambulant/stationär/niedergelassen"] || "").toLowerCase();
        if (typ.includes('ambulant')) hatAmbulant = true;
        if (typ.includes('stationär') || typ.includes('stationaer')) hatStationaer = true;
    });

    if (hatAmbulant && hatStationaer) return icons.lila;
    if (hatStationaer) return icons.rot;
    if (hatAmbulant) return icons.blau;
    return icons.grau;
}

function formatiereEintrag(standort) {
    return `
        <b>${standort["Einrichtung"] || "Unbekannte Einrichtung"}</b><br>
        <b>Kreis:</b> ${standort["Kreis"]}, ${standort["bundesland"]}<br>
        <b>Landesärztekammer:</b> ${standort["Landesärztekammer"] || "-"}<br>
        <b>Art:</b> ${standort["ambulant/stationär/niedergelassen"] || "-"}<br>
        <b>Weiterbildungsermächtigung:</b> ${standort["Weiterbildungsermächtigung für Nephrologie"] || "-"}<br>
        <b>Befugnis:</b> ${standort["Befugnis"] || "-"}<br>
        <b>Angaben zur Person:</b> ${standort["Angaben zur Person"] || "-"}
    `;
}

function zeigeStandorte(standorte) {
    var gruppiert = {};

    standorte.forEach(standort => {
        if (standort.lat === null || standort.lng === null) return;
        var key = `${standort.lat},${standort.lng}`;
        if (!gruppiert[key]) gruppiert[key] = [];
        gruppiert[key].push(standort);
    });

    Object.values(gruppiert).forEach(gruppe => {
        var erster = gruppe[0];
        var icon = ermittleFarbe(gruppe);

        var marker = L.marker([erster.lat, erster.lng], { icon: icon }).addTo(map);

        var popupContent = gruppe.map(formatiereEintrag).join('<hr>');

        marker.bindPopup(popupContent, { maxWidth: 450, minWidth: 250, maxHeight: 400 });
    });
}

if (window.STANDORTE_DATA) {
    zeigeStandorte(window.STANDORTE_DATA);
} else {
    fetch('/api/standorte')
        .then(response => response.json())
        .then(zeigeStandorte)
        .catch(error => console.error('Fehler beim Laden der Standorte:', error));
}

var legende = L.control({ position: 'bottomright' });

legende.onAdd = function (map) {
    var div = L.DomUtil.create('div', 'info legend');
    div.innerHTML += '<h4>Einrichtungstyp</h4>';
    div.innerHTML += '<i style="background: #2A81CB"></i> Ambulant<br>';
    div.innerHTML += '<i style="background: #CB2B3E"></i> Stationär<br>';
    div.innerHTML += '<i style="background: #9C2BCB"></i> Beides<br>';
    div.innerHTML += '<i style="background: #7B7B7B"></i> Keine Angabe';
    return div;
};

legende.addTo(map);