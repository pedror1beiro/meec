/* Illustrative water material, not wave/bathymetry data. No extra renderer. */
(function () {
    "use strict";
    function install(map, settings) {
        const size = 128, interval = 100; // Small repeating texture, at most 10 updates/s.
        const reduced = window.matchMedia("(prefers-reduced-motion: reduce)");
        let active = false, disposed = false, timer, dirty = true, last = -Infinity;
        const image = {width: size, height: size, data: new Uint8Array(size * size * 4)};

        function cancel() { clearTimeout(timer); timer = undefined; }
        function schedule() {
            if (active && !disposed && !document.hidden && !reduced.matches && timer === undefined) {
                timer = setTimeout(() => { timer = undefined; map.triggerRepaint(); }, interval);
            }
        }
        function repaint() {
            cancel(); dirty = true;
            if (active && !document.hidden && !disposed) { map.triggerRepaint(); schedule(); }
        }
        function shade(time) {
            // Normal shading from three periodic waves. All lengths/speeds are
            // artistic texture parameters, with no physical units or log input.
            const pitch = map.getPitch() * Math.PI / 180;
            const bearing = map.getBearing() * Math.PI / 180;
            const view = [Math.sin(bearing) * Math.sin(pitch),
                -Math.cos(bearing) * Math.sin(pitch), Math.cos(pitch)];
            const half = [view[0] - .4, view[1] - .5, view[2] + .768];
            const halfNorm = Math.hypot(...half);
            for (let y = 0; y < size; y++) {
                for (let x = 0; x < size; x++) {
                    const u = x * 2 * Math.PI / size, v = y * 2 * Math.PI / size;
                    const a = 5*u + 2*v - .85*time;
                    const b = -3*u + 7*v - 1.2*time;
                    const c = 11*u - 4*v + .65*time;
                    const nx = -.38*Math.cos(a) + .15*Math.cos(b) - .12*Math.cos(c);
                    const ny = -.152*Math.cos(a) - .35*Math.cos(b) + .044*Math.cos(c);
                    const norm = Math.hypot(nx, ny, 1);
                    const diffuse = Math.max(0, (-.4*nx - .5*ny + .768) / norm);
                    const specular = Math.pow(Math.max(0, (nx*half[0] + ny*half[1] + half[2]) / (norm*halfNorm)), 32);
                    const fresnel = Math.pow(1 - Math.max(0, (nx*view[0] + ny*view[1] + view[2]) / norm), 4);
                    const foam = 9 * Math.pow(Math.max(0, (Math.sin(a) + .5*Math.sin(b) + .2*Math.sin(c)) / 1.7), 8);
                    const light = .55 + .65*diffuse;
                    const index = (y*size + x)*4;
                    image.data[index] = Math.min(255, 14*light + 125*specular + 70*fresnel + foam);
                    image.data[index+1] = Math.min(255, 83*light + 138*specular + 90*fresnel + foam);
                    image.data[index+2] = Math.min(255, 111*light + 140*specular + 100*fresnel + foam);
                    image.data[index+3] = 255;
                }
            }
        }
        image.render = function () {
            if (!active || disposed || document.hidden) return false;
            const now = performance.now();
            if (!dirty && (reduced.matches || now-last < interval)) { schedule(); return false; }
            shade(reduced.matches ? 0 : now / 1000);
            dirty = false; last = now; schedule();
            return true;
        };
        shade(0);
        map.addImage("ocean-waves", image, {pixelRatio: 1});
        map.addSource("ocean-water", {type: "vector", url: settings.ocean_tiles_url,
            attribution: '<a href="https://openfreemap.org">OpenFreeMap</a> © <a href="https://openmaptiles.org">OpenMapTiles</a> · © <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'});
        map.addLayer({id: "ocean-surface", type: "fill", source: "ocean-water",
            "source-layer": "water", filter: ["==", ["get", "class"], "ocean"],
            layout: {visibility: "none"},
            paint: {"fill-pattern": "ocean-waves", "fill-opacity": .88, "fill-antialias": false}}, "seamarks");
        document.addEventListener("visibilitychange", repaint);
        reduced.addEventListener("change", repaint);
        map.on("move", repaint); // Lighting follows the camera, without moving it.
        function destroy() {
            disposed = true; cancel();
            document.removeEventListener("visibilitychange", repaint);
            reduced.removeEventListener("change", repaint);
            map.off("move", repaint);
        }
        map.on("remove", destroy);
        return {setActive(value) {
            if (active === value || disposed) return;
            active = value;
            map.setLayoutProperty("ocean-surface", "visibility", active ? "visible" : "none");
            repaint();
        }, destroy};
    }
    window.tomsaOcean = {install};
}());
