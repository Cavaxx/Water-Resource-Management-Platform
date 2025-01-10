// Initialize the map
var map = L.map('map').setView([46.1, 11.1], 10);

// Add a tile layer to the map
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; OpenStreetMap contributors'
}).addTo(map);

// Function to fetch and display data on the map
function displayOnMap(data) {
    // Add river markers
    data.river_data.forEach(river => {
        const marker = L.marker([river.latitude, river.longitude]).addTo(map);
        marker.bindPopup(`<b>${river.Name_River}</b><br>Water Level: ${river.Water_Level}`);
    });

    // Add facility markers
    data.facility_data.forEach(facility => {
        const marker = L.marker([facility.latitude, facility.longitude]).addTo(map);
        marker.bindPopup(`<b>${facility.Facility_Name}</b><br>ID Site: ${facility.ID_Site}<br>Communities Served: ${facility.Description}`);
    });
}

// Fetch data from the Flask endpoint and display it on the map
fetch('/search?name=Zento Novo')  // Replace 'Zento Novo' with a dynamic river name input if needed
    .then(response => response.json())
    .then(data => {
        displayOnMap(data);
    })
    .catch(error => console.error('Error fetching data:', error));

