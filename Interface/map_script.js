// Inizializzazione della mappa
var map = L.map('map').setView([46.1, 11.1], 10);

// Aggiungere un layer di tile
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; OpenStreetMap contributors'
}).addTo(map);

// Aggiungere un marker a titolo di esempio
L.marker([46.1, 11.1]).addTo(map)
    .bindPopup('Trento')
    .openPopup();

