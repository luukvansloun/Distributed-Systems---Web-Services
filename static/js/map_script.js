// MAP SETUP

mapboxgl.accessToken = 
  'pk.eyJ1IjoibHV1a3ZhbnNsb3VuIiwiYSI6ImNrMmQ3eWltcDA4b2gzYnMyaDV1Mjg1bHEifQ.lW_7UMom8nFmVmkEIVD32g';

var map = new mapboxgl.Map({
	container: 'map', // container id
	style: 'mapbox://styles/mapbox/streets-v11', // stylesheet location
	center: [4.4568032, 51.0210252], // starting position [lng, lat]
	zoom: 8.5 // starting zoom
});


