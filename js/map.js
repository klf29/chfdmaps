var directionsService = new google.maps.DirectionsService();

var CHFDMap = {
  bounds: null,
  map: null,
  map2: null,
  hydrants: null,
  knoxs: null,

  init: function(latLng, zoom) {
    var myOptions = {
      zoom: zoom,
      center: latLng,
      mapTypeId: google.maps.MapTypeId.ROADMAP
    }

    this.map = new google.maps.Map(document.getElementById('map_canvas'), myOptions);
    this.bounds = new google.maps.LatLngBounds();
  },
  
  placeMarkers: function(filename, target, icon, array) {
    $.get(filename, function(xml){
      $(xml).find(target).each(function(){
        var lat = $(this).find('lat').text();
        var lng = $(this).find('lng').text();
        var point = new google.maps.LatLng(parseFloat(lat),parseFloat(lng));
        CHFDMap.bounds.extend(point);
        var marker = new google.maps.Marker({position: point, map: CHFDMap.map, icon: icon});
        array.push(marker);
      });
      
      CHFDMap.map.fitBounds(CHFDMap.bounds);
      
    });
  },

  makeBorder: function(filename) {
    var corners = [];
    $.get(filename, function(xml){
      $(xml).find('corner').each(function(){
        var lat = $(this).find('lat').text();
        var lng = $(this).find('lng').text();
        var point = new google.maps.LatLng(parseFloat(lat),parseFloat(lng));
        corners.push(point);
      });
    
      var district = new google.maps.Polyline({
        path: corners,
        strokeColor: "#FF0000",
        strokeOpacity: 1.0,
        strokeWeight: 2.5
      });
      district.setMap(CHFDMap.map);
    });
  },

  clearMarkers: function(array) {
    // Hides markers in array in map
    for (var i = 0; i < array.length; i++) {
      array[i].setMap(null);
    }
  },

  restoreMarkers: function(array) {
    // Shows markers in array in map
    for (var i = 0; i < array.length; i++) {
      array[i].setMap(CHFDMap.map);
    }
  }
}

var calcRoute = function() {
  var start = '194 Pleasant Grove Rd, Ithaca NY';
  var end = getURLParameter('daddr');
  if (end == "null") var end = document.getElementById('custaddr').value;

  var json = $.getJSON('active', function(data) {
    end = data.destination;
    end = end.replace(/\//g,"&");
    
    var request = {
      origin: start,
      destination: end,
      travelMode: google.maps.DirectionsTravelMode.DRIVING
    };

    directionsService.route(request, function(response, status) {            
      if (status == google.maps.DirectionsStatus.OK) {
        // Once route is found, create second zoom map on destination
        var fire = 'img/fire_yellow_small.png';
        createZoom(response.routes[0].legs[0].end_location, fire)
        directionsDisplay.setDirections(response);
      }
    });
  });
}

var getURLParameter = function(name) {
  return decodeURI(
    (RegExp(name + '=' + '(.+?)(&|$)').exec(location.search)||[,null])[1]
  );
}

var downloadUrl = function(url, callback) {  
  var request;
  if(window.ActiveXObject) {
    request = new ActiveXObject('Microsoft.XMLHTTP');
  } else {
    request = new XMLHttpRequest;
  }

  request.onreadystatechange = function() {    
    if (request.readyState == 4) callback(request);
  };  

  request.open('GET', url, true);  
  request.send(null); 
}

var createZoom = function(destination, image) {
  // Creates a small map that zooms in on destination and shows hydrants
  var opts = {
    center: destination,
    zoom: 16,
    disableDefaultUI: true,
    mapTypeId: google.maps.MapTypeId.ROADMAP
  }

  CHFDMap.map2 = new google.maps.Map(document.getElementById("map_canvas2"), opts);
  var marker = new google.maps.Marker({position: destination, map: CHFDMap.map2, icon: image});

  // Place the stored hydrants
  var hydImage  = 'img/hydrant_red_small.png';
  for (var i = 0; i < CHFDMap.hydrants.length; i++) {
    var marker = new google.maps.Marker({position: CHFDMap.hydrants[i].getPosition(), map: CHFDMap.map2, icon: hydImage});
  }

  // Place the stored knoxes
  var knoxImage = 'img/knox_small.png';
  for (var i = 0; i < CHFDMap.knoxs.length; i++) {
    var marker = new google.maps.Marker({position: CHFDMap.knoxs[i].getPosition(), map: CHFDMap.map2, icon: knoxImage});
  }
}


var initialize = function() {
  // Set map
  directionsDisplay = new google.maps.DirectionsRenderer();
  var chfd = new google.maps.LatLng(42.467854,-76.478458);
  CHFDMap.init(chfd, 11);
  directionsDisplay.setMap(CHFDMap.map);
  directionsDisplay.setPanel(document.getElementById('directionsPanel'));
  
  // Set hydrants
  var hydImage  = 'img/hydrant_red_small.png';
  CHFDMap.hydrants = [];
  CHFDMap.placeMarkers('data/CHFDFireMarkers.xml', 'hydrant', hydImage, CHFDMap.hydrants);
  
  // Set knox boxes
  var knoxImage = 'img/knox_small.png';
  CHFDMap.knoxs = [];
  CHFDMap.placeMarkers('data/CHFDFireMarkers.xml', 'knox', knoxImage, CHFDMap.knoxs);
  
  // Make border
  CHFDMap.makeBorder('data/CHFDFireMarkers.xml');
  
  var firemen = 'img/firemen.png'
  createZoom(chfd, firemen)
  
  // Add zoom listener
  google.maps.event.addListener(CHFDMap.map, "zoom_changed", function() { 
    if (CHFDMap.map.getZoom() < 14) {
      CHFDMap.clearMarkers(CHFDMap.hydrants);
      CHFDMap.clearMarkers(CHFDMap.knoxs);
    }
    else {
      CHFDMap.restoreMarkers(CHFDMap.hydrants);
      CHFDMap.restoreMarkers(CHFDMap.knoxs);
    }
  });
  if (getURLParameter('daddr') !== "null") calcRoute();
}

$(function() {
  initialize();

  calcRoute();
  $('#home').on('click', function() { 
    console.log('test');
    window.location = window.location.pathname;
  });
});
