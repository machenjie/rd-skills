"use strict";

function resolvePreference(record, key, fallback) {
  const value =
    record && Object.prototype.hasOwnProperty.call(record, key)
      ? record[key]
      : undefined;
  return value || fallback;
}

module.exports = { resolvePreference };
