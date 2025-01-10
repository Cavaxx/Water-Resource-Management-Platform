// Inizializzazione della mappa
var map = L.map('map').setView([46.1, 11.1], 10);

// Aggiungere un layer di tile
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; OpenStreetMap contributors'
}).addTo(map);

L.marker([46.147744, 11.197343]).addTo(map).bindPopup('Test Marker');
// Aggiungere un marker a titolo di esempio
Papa.parse('../data/water_facilities_trentino.csv', {
    download: true,
    header: true,
    complete: function(results) {
        results.data.forEach(function(facility) {
            // Crea un marker per ogni sito
            var marker = L.marker([facility.latitude, facility.longitude]).addTo(map);
            
            // Crea il contenuto del popup con le informazioni desiderate
            var popupContent = `
                <b>Type:</b> ${facility.descrizione}
                <b>ID Sito:</b> ${facility.id_sito}<br>
                <b>Recettore:</b> ${facility.recettore}<br>
                <b>Comuni Serviti:</b> ${facility.comuni_serviti}
            `;

            // Aggiungi il popup al marker, senza aprirlo automaticamente
            marker.bindPopup(popupContent);
        });
    }
});

