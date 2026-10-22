/* One MapLibre instance per page. Replay changes markers, never the camera/style. */
(function () {
    "use strict";
    let map, mission, latestFrame, markers = {}, lastMode, lastReset = 0;
    let tileWarning = "";
    let mapReady = false, ocean, oceanFailed = false;
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
                markers[robot.robot] = new maplibregl.Marker({element,
                    rotationAlignment: "map", pitchAlignment: "map"})
                    .setLngLat([robot.longitude, robot.latitude]).addTo(map);
            }
            const marker = markers[robot.robot], element = marker.getElement();
            const headingKnown = Number.isFinite(robot.heading_deg);
            element.classList.toggle("selected", robot.robot === latestFrame.selected);
            element.classList.toggle("has-heading", headingKnown);
            element.title = info.label + (headingKnown ? " · rumo " + robot.heading_deg.toFixed(1) + "°" : " · rumo não confirmado");
            element.setAttribute("aria-label", element.title);
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

    function render(data, frame, mode, seamarks, reset) {
        mission = data;
        latestFrame = frame;
        if (!data || !document.getElementById("geographical-map")) return "A preparar mapa…";
        if (!window.maplibregl) return "MapLibre indisponível. Verificar a ligação ao CDN; as vistas NED continuam disponíveis.";
        if (!map) {
            const settings = data.settings;
            const sources = {
                osm: {type: "raster", tiles: [settings.base_tiles_url], tileSize: 256,
                    maxzoom: 19, attribution: settings.base_attribution},
                seamarks: {type: "raster", tiles: [settings.seamark_tiles_url], tileSize: 256,
                    maxzoom: 18, attribution: settings.seamark_attribution},
                trajectories: {type: "geojson", data: data.trajectories}
            };
            try {
                map = new maplibregl.Map({container: "geographical-map",
                    style: {version: 8, sources, layers: [
                        {id: "osm", type: "raster", source: "osm"},
                        {id: "seamarks", type: "raster", source: "seamarks",
                            layout: {visibility: seamarks.includes("show") ? "visible" : "none"}},
                        {id: "trajectories", type: "line", source: "trajectories",
                            paint: {"line-color": ["get", "color"], "line-width": 3, "line-opacity": 0.8}}
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
                    status(tileWarning || "Mapa pronto · trajetórias completas e posições sincronizadas");
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
        updateMarkers();
        return tileWarning || (mode === "3d"
            ? "3D · ondas e iluminação ilustrativas; sem medições do mar/batimetria · botão direito para rodar/inclinar"
            : "Trajetórias completas · arrastar para mover; botão direito para rodar/inclinar");
    }
    let showSeamarks = true;
    window.dash_clientside = Object.assign({}, window.dash_clientside, {tomsaMap: {render}});
}());
