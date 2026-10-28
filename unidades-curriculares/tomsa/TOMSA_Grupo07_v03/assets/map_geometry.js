/* Geometry for presentation only. Mission samples are never changed/interpolated. */
(function () {
    "use strict";
    const empty = () => ({type: "FeatureCollection", features: []});

    function recentTrails(data, frame, seconds) {
        const result = empty();
        if (!frame || !data.timeline_s || !(seconds > 0)) return result;
        for (const robot of frame.robots) {
            const trace = data.trajectories.features.find(f => f.properties.robot === robot.robot);
            const times = data.timeline_s[robot.robot];
            if (!trace || !times || !Number.isInteger(robot.sample_index)) continue;
            const end = Math.min(robot.sample_index, times.length-1);
            if (end < 1) continue;
            const cutoff = times[end]-seconds;
            let low = 0, high = end;
            while (low < high) {
                const mid = (low+high) >> 1;
                if (times[mid] < cutoff) low = mid+1; else high = mid;
            }
            const maxGap = data.settings.trail_max_gap_seconds || 2;
            for (let i = low+1; i <= end; i++) {
                if (!(times[i] > times[i-1]) || times[i]-times[i-1] > maxGap) continue;
                result.features.push({type: "Feature", properties: {
                    ...trace.properties, opacity: .18 + .82*(times[i]-cutoff)/seconds},
                    geometry: {type: "LineString", coordinates: [trace.geometry.coordinates[i-1], trace.geometry.coordinates[i]]}});
            }
        }
        return result;
    }

    function proximityCircle(frame, data) {
        const result = empty();
        if (!frame || !Number.isFinite(frame.radius_m) || frame.radius_m <= 0) return result;
        const center = frame.robots.find(r => r.robot === frame.selected);
        if (!center) return result;
        const info = data.trajectories.features.find(f => f.properties.robot === frame.selected);
        const rad = Math.PI/180, latitude = center.latitude*rad, longitude = center.longitude*rad;
        // Spherical direct geodesic, R=mean Earth radius. Explicitly approximate;
        // the actual local-view filter continues to use the full 3D NED norm.
        const angle = frame.radius_m/6371008.8, coordinates = [];
        for (let i = 0; i <= 64; i++) {
            const bearing = 2*Math.PI*i/64;
            const lat = Math.asin(Math.sin(latitude)*Math.cos(angle) + Math.cos(latitude)*Math.sin(angle)*Math.cos(bearing));
            const lon = longitude + Math.atan2(Math.sin(bearing)*Math.sin(angle)*Math.cos(latitude),
                Math.cos(angle)-Math.sin(latitude)*Math.sin(lat));
            coordinates.push([lon/rad, lat/rad]);
        }
        // An exactly closed GeoJSON linear ring, including after floating-point rounding.
        coordinates[64] = coordinates[0].slice();
        result.features.push({type: "Feature", properties: {color: info.properties.color},
            geometry: {type: "Polygon", coordinates: [coordinates]}});
        return result;
    }
    window.tomsaMapGeometry = {recentTrails, proximityCircle};
}());
