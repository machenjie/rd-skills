"use strict";

const assert = require("assert");
const { resolvePreference } = require("../src/preferences");

assert.strictEqual(resolvePreference({ limit: 0 }, "limit", 10), 0);
assert.strictEqual(resolvePreference({ enabled: false }, "enabled", true), false);
assert.strictEqual(resolvePreference({ label: "" }, "label", "untitled"), "");
assert.strictEqual(resolvePreference({}, "limit", 10), 10);
assert.strictEqual(resolvePreference({ limit: undefined }, "limit", 10), 10);
assert.strictEqual(resolvePreference({ limit: null }, "limit", 10), 10);
assert.strictEqual(resolvePreference({ limit: 25 }, "limit", 10), 25);

console.log("preferences tests passed");
