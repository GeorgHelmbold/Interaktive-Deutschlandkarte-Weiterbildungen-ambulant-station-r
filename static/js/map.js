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
        var marker = L.marker([erster.lat, erster.lng]).addTo(map);

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