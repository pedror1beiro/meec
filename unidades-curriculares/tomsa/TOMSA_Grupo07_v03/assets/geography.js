/* One MapLibre instance per page. Replay changes markers, never the camera/style. */
(function () {
    "use strict";
    let map, mission, latestFrame, markers = {}, lastMode, lastReset = 0;
    let tileWarning = "";
    let mapReady = false, ocean, oceanFailed = false;
    let trailMode = "60", effects = ["icons", "ring"];
    const status = text => window.dash_clientside.set_props("map-status", {children: text});

    function updateMarkers() {
        if (!map || !mission || !latestFrame) return;
        const present = new Set(latestFrame.robots.map(robot => robot.robot));
        Object.keys(markers).forEach(key => {
            if (!present.has(key)) { markers[key].remove(); delete markers[key]; }
        });
        latestFrame.robots.forEach(robot => {
            const info = mission.trajectories.features.find(f => f.properties.robot === robot.robot).properties;
            if (!markers[robot.robot]) {
                const element = document.createElement("div");
                element.className = "robot-map-marker";
                element.style.setProperty("--robot-color", info.color);
                const arrow = document.createElement("span");
                arrow.className = "robot-map-heading";
                element.appendChild(arrow);
                const icon = document.createElement("span");
                icon.className = "robot-glyph";
                // Front-view pictogram: no unconfirmed body axis is implied by its shape.
                icon.innerHTML = '<svg viewBox="0 0 40 40" aria-hidden="true"><path d="M20 5v5M15 5h10" stroke="#17263c" stroke-width="2"/><rect x="7" y="11" width="26" height="23" rx="9" fill="var(--robot-color)" stroke="white" stroke-width="2"/><path d="M7 22H3m30 0h4" stroke="#17263c" stroke-width="4"/><rect x="12" y="16" width="16" height="8" rx="4" fill="#17263c"/><circle cx="16" cy="20" r="2" fill="#d5f4ff"/><circle cx="24" cy="20" r="2" fill="#d5f4ff"/></svg>';
                element.appendChild(icon);
                const number = document.createElement("span");
                number.className = "robot-number";
                number.textContent = robot.robot.replace(/^robot/, "");
                element.appendChild(number);
                markers[robot.robot] = new maplibregl.Marker({element,
                    rotationAlignment: "viewport", pitchAlignment: "viewport"})
                    .setLngLat([robot.longitude, robot.latitude]).addTo(map);
            }
            const marker = markers[robot.robot], element = marker.getElement();
            const headingKnown = Number.isFinite(robot.heading_deg);
            element.classList.toggle("selected", robot.robot === latestFrame.selected);
            element.classList.toggle("has-heading", headingKnown);
            element.classList.toggle("robot-icon", effects.includes("icons"));
            element.classList.toggle("pulse", effects.includes("ring") && robot.robot === latestFrame.selected);
            element.title = info.label + (headingKnown ? " · rumo " + robot.heading_deg.toFixed(1) + "°" : " · rumo não confirmado");
            element.setAttribute("aria-label", element.title);
            marker.setRotationAlignment(headingKnown ? "map" : "viewport");
            marker.setPitchAlignment(headingKnown ? "map" : "viewport");
            marker.setLngLat([robot.longitude, robot.latitude]).setRotation(headingKnown ? robot.heading_deg : 0);
        });
    }

    function fitMission() {
        map.fitBounds(mission.bounds, {padding: 55, maxZoom: 16, duration: 0});
    }

    function updateOcean() {
        if (!mapReady || oceanFailed || mission.settings.ocean_surface === false) return;
        try {
            if (!ocean && lastMode === "3d" && window.tomsaOcean) ocean = window.tomsaOcean.install(map, mission.settings);
            if (ocean) ocean.setActive(lastMode === "3d");
        } catch (error) {
            oceanFailed = true;
            tileWarning = "Superfície do oceano indisponível; a usar a cartografia base.";
        }
    }

    function updateGeometry() {
        if (!mapReady || !window.tomsaMapGeometry) return;
        const geometry = window.tomsaMapGeometry;
        const recent = trailMode === "30" || trailMode === "60";
        map.setLayoutProperty("trajectories", "visibility", trailMode === "full" ? "visible" : "none");
        map.setLayoutProperty("recent-trails", "visibility", recent ? "visible" : "none");
        map.setLayoutProperty("trail-glow", "visibility", recent ? "visible" : "none");
        map.getSource("recent-trails").setData(geometry.recentTrails(mission, latestFrame, recent ? Number(trailMode) : 0));
        map.getSource("proximity").setData(effects.includes("ring")
            ? geometry.proximityCircle(latestFrame, mission) : {type: "FeatureCollection", features: []});
    }

    function render(data, frame, mode, seamarks, reset, trails = "60", visualEffects = ["icons", "ring"]) {
        mission = data;
        latestFrame = frame;
        trailMode = trails;
        effects = visualEffects;
        if (!data || !document.getElementById("geographical-map")) return "A preparar mapa…";
        if (!window.maplibregl) return "MapLibre indisponível. Verificar a ligação ao CDN; as vistas NED continuam disponíveis.";
        if (!map) {
            const settings = data.settings;
            const sources = {
                osm: {type: "raster", tiles: [settings.base_tiles_url], tileSize: 256,
                    maxzoom: 19, attribution: settings.base_attribution},
                seamarks: {type: "raster", tiles: [settings.seamark_tiles_url], tileSize: 256,
                    maxzoom: 18, attribution: settings.seamark_attribution},
                trajectories: {type: "geojson", data: data.trajectories},
                "recent-trails": {type: "geojson", data: {type: "FeatureCollection", features: []}},
                proximity: {type: "geojson", data: {type: "FeatureCollection", features: []}}
            };
            try {
                map = new maplibregl.Map({container: "geographical-map",
                    style: {version: 8, sources, layers: [
                        {id: "osm", type: "raster", source: "osm"},
                        {id: "seamarks", type: "raster", source: "seamarks",
                            layout: {visibility: seamarks.includes("show") ? "visible" : "none"}},
                        {id: "proximity-fill", type: "fill", source: "proximity",
                            paint: {"fill-color": ["get", "color"], "fill-opacity": .045}},
                        {id: "proximity-ring", type: "line", source: "proximity",
                            paint: {"line-color": ["get", "color"], "line-width": 1.5, "line-opacity": .5,
                                "line-dasharray": [3, 3]}},
                        {id: "trajectories", type: "line", source: "trajectories",
                            paint: {"line-color": ["get", "color"], "line-width": 3, "line-opacity": 0.8}},
                        {id: "trail-glow", type: "line", source: "recent-trails", layout: {"line-cap": "round"},
                            paint: {"line-color": ["get", "color"], "line-width": 10,
                                "line-opacity": ["*", .16, ["get", "opacity"]], "line-blur": 3}},
                        {id: "recent-trails", type: "line", source: "recent-trails", layout: {"line-cap": "round"},
                            paint: {"line-color": ["get", "color"], "line-width": 3,
                                "line-opacity": ["get", "opacity"]}}
                    ]},
                    center: data.bounds[0], zoom: 12, maxPitch: 70,
                    attributionControl: false, renderWorldCopies: false});
                map.addControl(new maplibregl.AttributionControl({compact: false}));
                map.addControl(new maplibregl.NavigationControl({visualizePitch: true}), "top-right");
                map.addControl(new maplibregl.ScaleControl({unit: "metric"}));
                new ResizeObserver(() => map.resize()).observe(document.getElementById("geographical-map"));
                fitMission();
                map.on("load", () => {
                    mapReady = true;
                    // Use the latest callback state even when replay started before map load.
                    map.setLayoutProperty("seamarks", "visibility", showSeamarks ? "visible" : "none");
                    updateMarkers();
                    updateOcean();
                    updateGeometry();
                    status(tileWarning || "Mapa pronto · posições sincronizadas; percurso conforme a opção selecionada");
                });
                map.on("error", event => {
                    if (event.sourceId === "ocean-water") {
                        oceanFailed = true;
                        if (ocean) ocean.setActive(false);
                        tileWarning = "Superfície do oceano indisponível; a usar a cartografia base. Verificar ligação ao OpenFreeMap.";
                    } else tileWarning = event.sourceId === "seamarks"
                        ? "OpenSeaMap indisponível nesta vista; a cartografia base e as trajetórias continuam disponíveis."
                        : "Falha ao carregar cartografia. Verificar rede/provedor; as trajetórias e vistas NED mantêm-se disponíveis.";
                    status(tileWarning);
                });
            } catch (error) {
                map = undefined;
                return "Não foi possível iniciar o mapa (WebGL/rede): " + error.message;
            }
        }
        showSeamarks = seamarks.includes("show");
        if (mode !== lastMode) {
            map.easeTo({pitch: mode === "3d" ? 55 : 0, duration: 350});
            lastMode = mode;
        }
        if ((reset || 0) !== lastReset) { fitMission(); lastReset = reset || 0; }
        if (mapReady) map.setLayoutProperty("seamarks", "visibility", showSeamarks ? "visible" : "none");
        updateOcean();
        updateGeometry();
        updateMarkers();
        return tileWarning || (mode === "3d"
            ? "3D · ondas e iluminação ilustrativas; sem medições do mar/batimetria · botão direito para rodar/inclinar"
            : "Posições sincronizadas · arrastar para mover; botão direito para rodar/inclinar");
    }
    let showSeamarks = true;
    window.dash_clientside = Object.assign({}, window.dash_clientside, {tomsaMap: {render}});
}());
