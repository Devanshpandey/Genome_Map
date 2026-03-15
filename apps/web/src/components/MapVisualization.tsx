import React from "react";
import { ComposableMap, Geographies, Geography, Marker } from "react-simple-maps";

const geoUrl = "https://unpkg.com/world-atlas@2.0.2/countries-110m.json";

const regionCoords: Record<string, [number, number]> = {
  "Northern Europe": [10, 60],
  "Southern Europe": [12, 43],
  "Northern/Western Europe": [5, 48],
  "East Asia": [115, 35],
  "Southeast Asia": [105, 15],
  "West Africa": [0, 10],
  "East Africa": [35, 0],
  "South Asia": [78, 20],
  "Central America": [-90, 15],
  "South America": [-70, -15],
  "Caribbean": [-70, 18],
  "African American": [-95, 38], // Default to Central US roughly
};

export default function MapVisualization({ topRegions }: { topRegions: Array<{name: string, score: number}> }) {
  
  // Create markers based on top regions matching our coords dictionary
  const markers = topRegions
    .slice(0, 3)
    .filter(r => regionCoords[r.name])
    .map((r, idx) => ({
      name: r.name,
      coords: regionCoords[r.name],
      radius: Math.max(8, r.score * 30), // Scale radius by probabilty score
      color: idx === 0 ? "#818cf8" : idx === 1 ? "#2dd4bf" : "#c084fc"
    }));

  return (
    <div className="w-full h-full bg-[#0a0c10]">
      <ComposableMap 
        projection="geoMercator"
        projectionConfig={{ scale: 120, center: [0, 40] }}
        width={800} height={500}
      >
        <Geographies geography={geoUrl}>
          {({ geographies }) =>
            geographies.map((geo) => (
              <Geography
                key={geo.rsmKey}
                geography={geo}
                fill="#1e293b"
                stroke="#0f172a"
                strokeWidth={0.5}
                style={{
                  default: { outline: "none" },
                  hover: { fill: "#334155", outline: "none", transition: "all 250ms" },
                  pressed: { outline: "none" },
                }}
              />
            ))
          }
        </Geographies>
        
        {markers.map((marker, idx) => (
          <Marker key={idx} coordinates={marker.coords}>
            <circle r={marker.radius} fill={marker.color} className="opacity-60 drop-shadow-xl" />
            <circle r={4} fill="#fff" />
            <text
              textAnchor="middle"
              y={-14}
              style={{ fontFamily: "inherit", fill: "#f1f5f9", fontSize: 10, fontWeight: 600, textShadow: "0 2px 4px rgba(0,0,0,0.8)" }}
            >
              {marker.name}
            </text>
          </Marker>
        ))}
      </ComposableMap>
    </div>
  );
}
