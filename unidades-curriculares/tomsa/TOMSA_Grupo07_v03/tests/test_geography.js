/* Node's built-in test runner; no npm packages or real map/tile requests. */
const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');
const source = fs.readFileSync(path.join(__dirname, '../assets/geography.js'), 'utf8');
const geometrySource = fs.readFileSync(path.join(__dirname, '../assets/map_geometry.js'), 'utf8');

function setup() {
    const maps = [], status = [];
    const element = () => {
        const classes = new Set();
        return {style: {setProperty() {}}, classes,
            classList: {toggle(name, enabled) { if (enabled) classes.add(name); else classes.delete(name); }},
            appendChild() {}, setAttribute() {}};
    };
    class Map {
        constructor(options) {
            this.options = options; this.events = {}; this.fits = []; this.moves = [];
            this.layers = []; this.loaded = false; maps.push(this);
            this.sources = Object.fromEntries(Object.entries(options.style.sources).map(([key, value]) =>
                [key, {data: value.data, updates: 0, setData(data) { this.data = data; this.updates++; }}]));
        }
        addControl() {}
        resize() {}
        fitBounds(bounds, options) { this.fits.push({bounds, options}); }
        easeTo(options) { this.moves.push(options); }
        on(event, handler) { this.events[event] = handler; }
        isStyleLoaded() { return this.loaded; }
        setLayoutProperty(...args) { this.layers.push(args); }
        getSource(key) { return this.sources[key]; }
    }
    class Marker {
        constructor(options) { this.element = options.element; }
        setLngLat(position) { this.position = position; return this; }
        addTo(map) { (map.markers ||= []).push(this); return this; }
        getElement() { return this.element; }
        setRotation(heading) { this.heading = heading; return this; }
        setRotationAlignment(value) { this.rotationAlignment = value; return this; }
        setPitchAlignment(value) { this.pitchAlignment = value; return this; }
        remove() { this.removed = true; }
    }
    const context = {window: {dash_clientside: {set_props: (_, data) => status.push(data)}},
        document: {getElementById: element, createElement: element},
        maplibregl: {Map, Marker, NavigationControl: class {}, AttributionControl: class {}, ScaleControl: class {}},
        ResizeObserver: class {observe() {}}};
    context.window.maplibregl = context.maplibregl;
    vm.runInNewContext(geometrySource, context);
    vm.runInNewContext(source, context);
    const mission = {trajectories: {type: 'FeatureCollection', features: [
        {properties: {robot: 'r1', label: 'R1', color: '#db5661'},
            geometry: {type: 'LineString', coordinates: [[-8, 41], [-8.1, 41.1]]}}
    ]}, timeline_s: {r1: [0, 1]}, bounds: [[-8.1, 41], [-8, 41.1]], settings: {base_tiles_url: 'base', seamark_tiles_url: 'sea'}};
    const frame = longitude => ({selected: 'r1', radius_m: 450,
        robots: [{robot: 'r1', longitude, latitude: 41, sample_index: 1, heading_deg: null}]});
    return {context, maps, mission, frame, render: context.window.dash_clientside.tomsaMap.render, status};
}

test('replay reuses map, static trajectories and camera; reset/mode are explicit', () => {
    const {maps, mission, frame, render} = setup();
    render(mission, frame(-8), '2d', ['show'], 0);
    const map = maps[0], staticSource = map.options.style.sources.trajectories;
    for (let i = 1; i < 20; i++) render(mission, frame(-8 - i / 100), '2d', ['show'], 0);
    assert.equal(maps.length, 1);
    assert.equal(map.fits.length, 1);
    assert.equal(map.moves.length, 1);
    assert.equal(map.options.style.sources.trajectories, staticSource);
    assert.equal(map.markers.length, 1);
    assert.equal(map.markers[0].position[0], -8.19);
    render(mission, frame(-8), '3d', ['show'], 0);
    assert.equal(map.moves.length, 2);
    assert.equal(map.moves[1].pitch, 55);
    assert.equal(map.moves[1].center, undefined);
    render(mission, frame(-8), '3d', ['show'], 1);
    assert.equal(map.fits.length, 2);
});

test('missing samples remove markers; heading requires a finite confirmed angle', () => {
    const {maps, mission, frame, render} = setup();
    render(mission, frame(-8), '2d', [], 0);
    const marker = maps[0].markers[0];
    assert.equal(marker.heading, 0);
    assert.equal(marker.rotationAlignment, 'viewport');
    assert.match(marker.element.title, /não confirmado/);
    const confirmed = frame(-8); confirmed.robots[0].heading_deg = 90;
    render(mission, confirmed, '2d', [], 0);
    assert.equal(marker.heading, 90);
    assert.equal(marker.rotationAlignment, 'map');
    render(mission, {selected: 'r1', robots: []}, '2d', [], 0);
    assert.equal(marker.removed, true);
    render(mission, frame(-8.2), '2d', [], 0);
    assert.equal(maps[0].markers.length, 2);
});

test('delayed map load uses latest replay position and overlay choice', () => {
    const {maps, mission, frame, render} = setup();
    render(mission, null, '2d', ['show'], 0);
    render(mission, frame(-8.5), '2d', [], 0);
    const map = maps[0]; map.loaded = true; map.events.load();
    assert.equal(map.markers[0].position[0], -8.5);
    assert.equal(map.layers.filter(v => v[0] === 'seamarks').at(-1)[2], 'none');
    render(mission, frame(-8.6), '2d', ['show'], 0);
    assert.equal(map.layers.filter(v => v[0] === 'seamarks').at(-1)[2], 'visible');
});

test('CDN, WebGL and seamark failures are visible without throwing', () => {
    const {context, maps, mission, frame, render, status} = setup();
    context.window.maplibregl = undefined;
    assert.match(render(mission, frame(-8), '2d', [], 0), /MapLibre indisponível/);
    context.window.maplibregl = context.maplibregl;
    render(mission, frame(-8), '2d', [], 0);
    maps[0].events.error({sourceId: 'seamarks'});
    assert.match(status.at(-1).children, /OpenSeaMap indisponível/);
    const failure = setup();
    failure.context.maplibregl.Map = class {constructor() {throw Error('WebGL');}};
    assert.match(failure.render(failure.mission, failure.frame(-8), '2d', [], 0), /WebGL/);
});

test('ocean is installed lazily in 3D, survives replay, and hides in 2D while tiles load', () => {
    const {context, maps, mission, frame, render} = setup();
    const states = []; let installs = 0;
    context.window.tomsaOcean = {install: () => { installs++; return {setActive: value => states.push(value)}; }};
    render(mission, frame(-8), '2d', [], 0);
    const map = maps[0]; map.loaded = true; map.events.load();
    assert.equal(installs, 0);
    render(mission, frame(-8), '3d', [], 0);
    assert.equal(installs, 1);
    assert.equal(states.at(-1), true);
    const fits = map.fits.length, moves = map.moves.length;
    render(mission, frame(-8.1), '3d', [], 0);
    assert.equal(installs, 1);
    assert.equal(map.fits.length, fits);
    assert.equal(map.moves.length, moves);
    map.loaded = false;
    render(mission, frame(-8.2), '2d', [], 0);
    assert.equal(states.at(-1), false);
});

test('ocean failure falls back to base map and does not retry on every replay frame', () => {
    const {context, maps, mission, frame, render, status} = setup();
    const states = [];
    context.window.tomsaOcean = {install: () => ({setActive: value => states.push(value)})};
    render(mission, frame(-8), '3d', [], 0);
    const map = maps[0]; map.loaded = true; map.events.load();
    assert.equal(states.at(-1), true);
    map.events.error({sourceId: 'ocean-water'});
    assert.match(status.at(-1).children, /oceano indisponível/);
    assert.equal(states.at(-1), false);
    render(mission, frame(-8.1), '3d', [], 0);
    assert.equal(states.at(-1), false);
});

test('trails and visual toggles update locally without changing the static source or camera', () => {
    const {maps, mission, frame, render} = setup();
    render(mission, frame(-8), '2d', [], 0, '60', ['icons', 'ring']);
    const map = maps[0]; map.loaded = true; map.events.load();
    assert.equal(map.getSource('recent-trails').data.features.length, 1);
    assert.equal(map.getSource('proximity').data.features.length, 1);
    assert.ok(map.markers[0].element.classes.has('robot-icon'));
    assert.ok(map.markers[0].element.classes.has('pulse'));
    const fits = map.fits.length, moves = map.moves.length;
    render(mission, frame(-8), '2d', [], 0, 'full', []);
    assert.equal(map.layers.filter(v => v[0] === 'trajectories').at(-1)[2], 'visible');
    assert.equal(map.getSource('recent-trails').data.features.length, 0);
    assert.equal(map.getSource('proximity').data.features.length, 0);
    assert.ok(!map.markers[0].element.classes.has('robot-icon'));
    assert.ok(!map.markers[0].element.classes.has('pulse'));
    assert.equal(map.getSource('trajectories').updates, 0);
    assert.equal(map.fits.length, fits);
    assert.equal(map.moves.length, moves);
    render(mission, {selected: 'r1', robots: [], radius_m: 450}, '2d', [], 0, '30', ['ring']);
    assert.equal(map.getSource('recent-trails').data.features.length, 0);
    assert.equal(map.getSource('proximity').data.features.length, 0);
});

test('recent trails use only actual samples inside the chosen visible-sample window', () => {
    const {context, mission} = setup();
    const coordinates = [[0, 0], [1, 1], [2, 2], [3, 3], [4, 4]];
    mission.trajectories.features[0].geometry.coordinates = coordinates;
    mission.timeline_s.r1 = [-20, -10, 0, 10, 20];
    mission.settings.trail_max_gap_seconds = 15;
    const frame = {robots: [{robot: 'r1', sample_index: 3}]};
    const result = context.window.tomsaMapGeometry.recentTrails(mission, frame, 20);
    assert.equal(result.features.length, 2);
    assert.equal(result.features[0].geometry.coordinates[0], coordinates[1]);
    assert.equal(result.features[1].geometry.coordinates[1], coordinates[3]);
    assert.ok(result.features[0].properties.opacity < result.features[1].properties.opacity);
    assert.ok(result.features.every(f => f.properties.opacity >= .18 && f.properties.opacity <= 1));
    frame.robots[0].sample_index = 1; // Backwards seek: no future trail left over.
    const earlier = context.window.tomsaMapGeometry.recentTrails(mission, frame, 20);
    assert.equal(earlier.features.length, 1);
    assert.equal(earlier.features[0].geometry.coordinates[1], coordinates[1]);
});

test('recent trails do not interpolate, bridge large gaps or invent missing-robot paths', () => {
    const {context, mission} = setup();
    mission.timeline_s.r1 = [0, 1, 9, 10];
    mission.trajectories.features[0].geometry.coordinates = [[0, 0], [1, 1], [2, 2], [3, 3]];
    const fn = context.window.tomsaMapGeometry.recentTrails;
    const result = fn(mission, {robots: [{robot: 'r1', sample_index: 3}]}, 30);
    assert.equal(result.features.length, 2);
    assert.equal(result.features[0].geometry.coordinates[1][0], 1);
    assert.equal(result.features[1].geometry.coordinates[0][0], 2);
    assert.equal(fn(mission, {robots: []}, 30).features.length, 0);
    assert.equal(fn(mission, {robots: [{robot: 'r1', sample_index: 0}]}, 30).features.length, 0);
});

test('proximity polygon has the requested spherical radius and is removed without its center', () => {
    const {context, mission, frame} = setup();
    const fn = context.window.tomsaMapGeometry.proximityCircle;
    const data = frame(-8);
    const result = fn(data, mission);
    const ring = result.features[0].geometry.coordinates[0];
    assert.equal(ring.length, 65);
    assert.equal(JSON.stringify(ring[0]), JSON.stringify(ring.at(-1)));
    const rad = Math.PI/180, lat = data.robots[0].latitude*rad, lon = data.robots[0].longitude*rad;
    for (const point of ring) {
        const a = Math.sin((point[1]*rad-lat)/2)**2 + Math.cos(lat)*Math.cos(point[1]*rad)*Math.sin((point[0]*rad-lon)/2)**2;
        const distance = 2*6371008.8*Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
        assert.ok(Math.abs(distance-data.radius_m) < 1e-6);
    }
    assert.equal(fn({selected: 'absent', robots: data.robots, radius_m: 450}, mission).features.length, 0);
    assert.equal(fn({...data, radius_m: 0}, mission).features.length, 0);
});
