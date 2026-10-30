// Task T-004 starter: an empty map at the Mayon summit.
// Later tasks replace these fixed values with data/sites.json (T-022, T-023).

const MAYON_SUMMIT = [13.2572, 123.6856];
const DANGER_ZONE_M = 6000;

const map = L.map("map").setView(MAYON_SUMMIT, 12);

// Background imagery (Esri). Check Esri's terms and attribution before release (04, ADR-010).
L.tileLayer(
  "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
  { maxZoom: 18, attribution: "Tiles &copy; Esri" }
).addTo(map);

// 6 km Permanent Danger Zone ring around the summit (FR-004)
L.circle(MAYON_SUMMIT, {
  radius: DANGER_ZONE_M,
  color: "#c2410c",
  weight: 2,
  fill: false,
  dashArray: "6 6",
})
  .addTo(map)
  .bindTooltip("Permanent Danger Zone (6 km)");
