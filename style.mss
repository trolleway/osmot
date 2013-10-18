Map {

}

#routeswithrefs {
  line-width:2;
  line-color:#f00;
  line-join:round;
  line-cap:round;
  line-smooth:0;
  text-name:[routes_ref];
  text-face-name: "DejaVu Sans Bold";
  text-dy: -8;
  text-allow-overlap:true;
  text-fill: red;

  text-placement: line;
  text-placement-type: simple; 
  text-ratio: 100;
  text-label-position-tolerance: 5;
  text-halo-radius: 1;
}

#terminalsexport {
  
    marker-placement: point;
    marker-fill: white;
    marker-line-width:2;
    text-name:[long_text];
    text-face-name: "DejaVu Sans Bold";
  
    text-fill: darkred;
    text-allow-overlap:false;
    text-placement-type: simple; 

    text-ratio: 100;
    text-placements: "E,W,NE,SE,NW,SW,16,14,12";
    text-dy: 3;
    text-dx: 6;
  
    text-halo-radius: 1;
  }



#planetosmpointwherer {
  marker-width:6;
  marker-fill:#f45;
  marker-line-color:#813;
  
  marker-allow-overlap:true;
  text-name:[name];
  text-face-name: "DejaVu Sans Oblique";
  text-placement-type: simple; 
  text-allow-overlap:false;
  text-dy: -3;
  text-dx: 3;
  text-halo-radius: 1;
  text-ratio:7;
  text-wrap-width:15;
  
  text-placements: "E,W,NE,SE,NW,SW,16,14,12";
}
