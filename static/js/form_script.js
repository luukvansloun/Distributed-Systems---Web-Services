let line_div = document.getElementById('linediv');
let dir_div = document.getElementById('dirdiv');

let province_select = document.getElementById('province')
let line_select = document.getElementById('line')
let direction_select = document.getElementById('direction')
let loading = document.getElementById('loading');
let current_markers = []

window.onload = function() {
  province_select.innerHTML = '<option disabled selected>Select Province</option>' + province_select.innerHTML;
  line_div.style.display = "none";
  dir_div.style.display = "none";
  loading.style.display = "none";
}

province_select.onchange = function () {
  province = province_select.value;
  fetch("/getLinesForProvince/" + province).then(function(response) {
	  response.json().then(function(data) {
		  let options = '<option disabled selected>Select Line</option>';
		  for(let line of data.lines) {
			  options += '<option value="' + line.linenumber + '">' + line.linenumber + ": " + line.description + '</option>';
		  }

		  line_select.innerHTML = options;
	  });
  }); 
  line_div.style.display = "block";
  dir_div.style.display = "none";
}

line_select.onchange = function () {
  province = province_select.value;
  line = line_select.value;

  fetch("/getLineDirections/" + province + "/" + line).then(function(response) {
	  response.json().then(function(data) {
		  let options = '<option disabled selected>Select Direction</option>';
		  for(let dir of data.directions) {
			  options += '<option value="' + dir.direction + '">' + dir.direction + ": " + dir.destination + 
							'</option>';
		  }
		  direction_select.innerHTML = options;
	  });
  }); 
  dir_div.style.display = "block";
}

direction_select.onchange = function () {
	loading.style.display = "block";
	province = province_select.value;
	line = line_select.value;
	direction = direction_select.value;

	fetch("/getLineRoute/" + province + "/" + line + "/" + direction).then(function(response) {
	  response.json().then(function(data) {
	  	let wps = []
	  	if(current_markers !== null) {
				for(let m = 0; m < current_markers.length; m++) {
					current_markers[m].remove();
				}
			}
		  for(let i = 0; i < data.stops.length; i++) {
		  	var stopMarker = document.createElement('div');
		  	stopMarker.className = "marker";

		  	let new_marker = new mapboxgl.Marker(stopMarker)
		  		.setLngLat([data.stops[i].longitude, data.stops[i].latitude])
		  		.setPopup(new mapboxgl.Popup({offset:25})
		  			.setHTML('<h3 style="text-align: center;">' + data.stops[i].description + "</h3>" +
		  								'<img style="display: block; margin-left: auto; margin-right: auto;" src=' + data.stops[i].weather_icon + '>' +
		  								'<p style="text-align: center;">' + data.stops[i].weather_description + '</p>' + 
		  								'<p style="text-align: center;">' + data.stops[i].weather_temp + ' degrees</p>'))
		  		.addTo(map);

		  	current_markers.push(new_marker);

		  	if(i < data.stops.length - 1) {
		  		for(let wp of data.stops[i].waypoints) {
		  			let coords = []
		  			coords.push(wp.lng)
		  			coords.push(wp.lat)
		  			wps.push(coords)
		  		}
		  	}
		  }
		  for(let bus of data.busses) {
		  	var busMarker = document.createElement('div');
		  	busMarker.className = "bus";

		  	let newmarker = new mapboxgl.Marker(busMarker)
		  		.setLngLat([bus.longitude, bus.latitude])
		  		.addTo(map);

		  	current_markers.push(newmarker)
		  }
		  if(map.getLayer('route')) {
		  		map.removeLayer('route');
		  		map.removeSource('route');
	  	}

	  	map.addLayer({
	  		"id": "route",
	  		"type": "line",
	  		"source": {
	  			"type": "geojson",
	  			"data": {
	  				"type": "Feature",
	  				"properties": {},
	  				"geometry": {
	  					"type": "LineString",
	  					"coordinates": wps
	  				}
	  			}
	  		},
  			"paint": {
  				"line-color": "#1D8ECE",
  				"line-width": 5
  			}
	  	});

	  	let bounds = wps.reduce(function(bounds, coord) {
	  		return bounds.extend(coord);
	  	}, new mapboxgl.LngLatBounds(wps[0], wps[0]));

	  	map.fitBounds(bounds, {
				padding: 50
			});
	  });
	  loading.style.display = "none";
  });
}