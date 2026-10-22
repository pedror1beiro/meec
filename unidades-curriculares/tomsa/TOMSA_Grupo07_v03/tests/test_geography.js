/* Node's built-in test runner; no npm packages or real map/tile requests. */
const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');
const source = fs.readFileSync(path.join(__dirname, '../assets/geography.js'), 'utf8');

function setup() {
    const maps = [], status = [];
    const element = () => ({style: {setProperty() {}}, classList: {toggle() {}},
        appendChild() {}, setAttribute() {}});
    class Map {
        constructor(options) {
            this.options = options; this.events = {}; this.fits = []; this.moves = [];
            this.layers = []; this.loaded = false; maps.push(this);
        }
        addControl() {}
        resize() {}
        fitBounds(bounds, options) { this.fits.push({bounds, options}); }
        easeTo(options) { this.moves.push(options); }
        on(event, handler) { this.events[event] = handler; }
        isStyleLoaded() { return this.loaded; }
        setLayoutProperty(...args) { this.layers.push(args); }
    }
    class Marker {
        constructor(options) { this.element = options.element; }
        setLngLat(position) { this.position = position; return this; }
        addTo(map) { (map.markers ||= []).push(this); return this; }
        getElement() { return this.element; }
        setRotation(heading) { this.heading = heading; return this; }
        remove() { this.removed = true; }
    }
    const context = {window: {dash_clientside: {set_props: (_, data) => status.push(data)}},
        document: {getElementById: element, createElement: element},
        maplibregl: {Map, Marker, NavigationControl: class {}, AttributionControl: class {}, ScaleControl: class {}},
        ResizeObserver: class {observe() {}}};
    context.window.maplibregl = context.maplibregl;
    vm.runInNewContext(source, context);
    const mission = {trajectories: {type: 'FeatureCollection', features: [
        {properties: {robot: 'r1', label: 'R1', color: '#db5661'},
            geometry: {type: 'LineString', coordinates: [[-8, 41], [-8.1, 41.1]]}}
    ]}, bounds: [[-8.1, 41], [-8, 41.1]], settings: {base_tiles_url: 'base', seamark_tiles_url: 'sea'}};
    const frame = longitude => ({selected: 'r1', robots: [{robot: 'r1', longitude, latitude: 41, heading_deg: null}]});
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
    assert.match(marker.element.title, /não confirmado/);
    const confirmed = frame(-8); confirmed.robots[0].heading_deg = 90;
    render(mission, confirmed, '2d', [], 0);
    assert.equal(marker.heading, 90);
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
    assert.equal(map.layers.at(-1)[2], 'none');
    render(mission, frame(-8.6), '2d', ['show'], 0);
    assert.equal(map.layers.at(-1)[2], 'visible');
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
