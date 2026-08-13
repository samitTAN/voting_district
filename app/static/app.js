/* Drawing page: county picker -> click-to-assign villages on a Leaflet map,
 * with every stats/warnings/completeness computation delegated to the
 * server-side evaluateAssignment seam (POST /api/counties/{county}/evaluate)
 * rather than re-implemented here — see docs/adr/0001-web-app-stack.md. */

let counties = [];
let currentCounty = null;
let seatCount = 0;
let villagesGeoJson = null;
let assignment = {};
let activeDistrict = 1;

let map = null;
let villageLayer = null;
let officialLayer = null;

function districtColor(n) {
  const hue = ((n - 1) * 137.508) % 360;
  return `hsl(${hue.toFixed(0)}, 55%, 45%)`;
}

function formatPercent(x) {
  const pct = x * 100;
  const sign = pct >= 0 ? "+" : "";
  return `${sign}${pct.toFixed(1)}%`;
}

async function init() {
  map = L.map("map").setView([23.7, 121], 8);
  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    attribution: "&copy; OpenStreetMap contributors",
  }).addTo(map);

  const response = await fetch("/api/counties");
  counties = await response.json();

  const select = document.getElementById("county-select");
  for (const county of counties) {
    const option = document.createElement("option");
    option.value = county.name;
    option.textContent = `${county.name}（${county.seat_count} 席）`;
    select.appendChild(option);
  }
  select.addEventListener("change", () => {
    if (select.value) loadCounty(select.value);
  });

  document.getElementById("official-toggle").addEventListener("change", (e) => {
    if (!officialLayer) return;
    if (e.target.checked) officialLayer.addTo(map);
    else map.removeLayer(officialLayer);
  });
}

async function loadCounty(name) {
  currentCounty = name;
  seatCount = counties.find((c) => c.name === name).seat_count;
  assignment = {};
  activeDistrict = 1;

  const response = await fetch(`/api/counties/${encodeURIComponent(name)}/villages`);
  villagesGeoJson = await response.json();

  renderDistrictToolbar();
  renderVillageLayer();
  renderOfficialLayer();
  await refreshEvaluation();
}

function renderDistrictToolbar() {
  const toolbar = document.getElementById("district-toolbar");
  toolbar.innerHTML = "";
  for (let n = 1; n <= seatCount; n++) {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "district-btn";
    button.textContent = `第 ${n} 選區`;
    button.style.setProperty("--district-color", districtColor(n));
    button.setAttribute("aria-pressed", String(n === activeDistrict));
    button.addEventListener("click", () => {
      activeDistrict = n;
      for (const child of toolbar.children) {
        child.setAttribute("aria-pressed", String(child === button));
      }
    });
    toolbar.appendChild(button);
  }
}

function villageStyle(feature) {
  const district = assignment[feature.properties.id];
  if (district) {
    return { color: districtColor(district), weight: 1, fillColor: districtColor(district), fillOpacity: 0.55 };
  }
  return { color: "#8a8072", weight: 1, fillColor: "#8a8072", fillOpacity: 0.12 };
}

function renderVillageLayer() {
  if (villageLayer) map.removeLayer(villageLayer);
  villageLayer = L.geoJSON(villagesGeoJson, {
    style: villageStyle,
    onEachFeature: (feature, layer) => {
      layer.bindTooltip(feature.properties.name);
      layer.on("click", () => toggleAssignment(feature.properties.id));
    },
  }).addTo(map);
  try {
    map.fitBounds(villageLayer.getBounds(), { padding: [16, 16] });
  } catch {
    // no valid bounds (empty county) — leave the default view
  }
}

function renderOfficialLayer() {
  if (officialLayer) map.removeLayer(officialLayer);
  officialLayer = L.geoJSON(villagesGeoJson, {
    style: (feature) => ({
      color: districtColor(feature.properties.official_district),
      weight: 2,
      fillOpacity: 0,
      dashArray: "4 3",
    }),
    interactive: false,
  });
  if (document.getElementById("official-toggle").checked) officialLayer.addTo(map);
}

function toggleAssignment(villageId) {
  if (assignment[villageId] === activeDistrict) {
    delete assignment[villageId];
  } else {
    assignment[villageId] = activeDistrict;
  }
  villageLayer.setStyle(villageStyle);
  refreshEvaluation();
}

async function refreshEvaluation() {
  const response = await fetch(`/api/counties/${encodeURIComponent(currentCounty)}/evaluate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ assignment }),
  });
  const result = await response.json();

  renderProgress();
  renderDistrictCards(result.district_stats);
  renderWarnings(result.warnings);
}

function renderProgress() {
  const total = villagesGeoJson.features.length;
  const assigned = Object.keys(assignment).length;
  document.getElementById("progress").innerHTML =
    `<span class="nums">${assigned} / ${total}</span> 村里已指派`;
}

function renderDistrictCards(districtStats) {
  const container = document.getElementById("district-cards");
  container.innerHTML = "";
  for (const stats of districtStats) {
    const memberCount = Object.values(assignment).filter((d) => d === stats.district).length;
    const card = document.createElement("div");
    card.className = "district-card";

    const chips =
      memberCount === 0
        ? '<span class="chip">尚無村里</span>'
        : `<span class="chip ${stats.within_threshold ? "ok" : "caution"}">人口 ${formatPercent(stats.deviation)}</span>` +
          `<span class="chip ${stats.contiguous ? "ok" : "violation"}">${stats.contiguous ? "地理連續" : "不連續"}</span>`;

    card.innerHTML = `
      <div class="head"><span class="swatch" style="background:${districtColor(stats.district)}"></span>第 ${stats.district} 選區</div>
      <div class="pop">人口 ${stats.population.toLocaleString("zh-Hant")} 人 · ${memberCount} 個村里</div>
      <div class="chips">${chips}</div>
    `;
    container.appendChild(card);
  }
}

function renderWarnings(warnings) {
  const list = document.getElementById("warn-list");
  list.innerHTML = "";
  if (warnings.length === 0) {
    list.innerHTML = '<li class="none">✅ 目前沒有偵測到違反原則的地方。</li>';
    return;
  }
  for (const warning of warnings) {
    const li = document.createElement("li");
    li.className = warning.severity;
    li.textContent = warning.message;
    list.appendChild(li);
  }
}

init();
