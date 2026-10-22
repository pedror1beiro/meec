const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');

function setup(reducedMotion = false) {
    let now = 0, nextTimer = 0;
    const timers = new Map(), events = {}, documentEvents = {};
    const reduced = {matches: reducedMotion, addEventListener() {}, removeEventListener() {}};
    const document = {hidden: false,
        addEventListener: (name, fn) => documentEvents[name] = fn,
        removeEventListener: name => delete documentEvents[name]};
    const context = {window: {matchMedia: () => reduced}, document,
        performance: {now: () => now},
        setTimeout: fn => { timers.set(++nextTimer, fn); return nextTimer; },
        clearTimeout: id => timers.delete(id)};
    vm.runInNewContext(fs.readFileSync(path.join(__dirname, '../assets/ocean.js'), 'utf8'), context);
    const map = {images: {}, sources: {}, layers: [], repaintCount: 0, pitch: 55,
        addImage(name, image) { this.images[name] = image; },
        addSource(name, source) { this.sources[name] = source; },
        addLayer(layer, before) { this.layers.push({layer, before}); },
        setLayoutProperty(name, key, value) { this.layers.find(v => v.layer.id === name).layer.layout[key] = value; },
        triggerRepaint() { this.repaintCount++; }, getPitch() {return this.pitch;}, getBearing() {return 0;},
        on: (name, fn) => events[name] = fn, off: name => delete events[name]};
    const ocean = context.window.tomsaOcean.install(map, {ocean_tiles_url: 'https://example.test/water.json'});
    return {map, ocean, image: map.images['ocean-waves'], timers, events, document, documentEvents,
        setTime: time => now = time};
}

test('water is masked to mapped ocean polygons, below seamarks; no camera methods needed', () => {
    const {map} = setup();
    assert.equal(map.sources['ocean-water'].url, 'https://example.test/water.json');
    const {layer, before} = map.layers[0];
    assert.equal(layer['source-layer'], 'water');
    assert.equal(JSON.stringify(layer.filter), JSON.stringify(['==', ['get', 'class'], 'ocean']));
    assert.equal(before, 'seamarks');
    assert.equal(layer.layout.visibility, 'none');
    assert.match(map.sources['ocean-water'].attribution, /OpenFreeMap/);
});

test('water has shaded detail and animates at a capped rate without reallocating image data', () => {
    const {ocean, image, setTime} = setup();
    ocean.setActive(true);
    const data = image.data;
    assert.equal(image.render(), true);
    const first = Array.from(data);
    assert.ok(new Set(first.filter((_, i) => i % 4 === 0)).size > 20);
    assert.ok(first.filter((_, i) => i % 4 === 3).every(alpha => alpha === 255));
    setTime(50);
    assert.equal(image.render(), false);
    setTime(1100);
    assert.equal(image.render(), true);
    assert.equal(data, image.data);
    assert.notDeepEqual(Array.from(data), first);
});

test('2D, hidden tab and map removal stop scheduled rendering', () => {
    const {ocean, image, timers, document, documentEvents, map, events} = setup();
    assert.equal(timers.size, 0);
    ocean.setActive(true); image.render();
    assert.equal(timers.size, 1);
    document.hidden = true; documentEvents.visibilitychange();
    assert.equal(timers.size, 0);
    assert.equal(image.render(), false);
    document.hidden = false; documentEvents.visibilitychange();
    assert.equal(timers.size, 1);
    ocean.setActive(false);
    assert.equal(map.layers[0].layer.layout.visibility, 'none');
    assert.equal(timers.size, 0);
    assert.equal(image.render(), false);
    ocean.setActive(true);
    events.remove();
    assert.equal(timers.size, 0);
    assert.equal(documentEvents.visibilitychange, undefined);
});

test('reduced motion retains static shading and responds to camera lighting changes', () => {
    const {ocean, image, timers, map, events, setTime} = setup(true);
    ocean.setActive(true);
    assert.equal(image.render(), true);
    const first = Array.from(image.data);
    setTime(1000);
    assert.equal(image.render(), false);
    assert.equal(timers.size, 0);
    map.pitch = 25; events.move();
    assert.equal(image.render(), true);
    assert.notDeepEqual(Array.from(image.data), first);
    assert.equal(timers.size, 0);
});
