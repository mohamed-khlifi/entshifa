#!/usr/bin/env node
/**
 * Fail on npm audit findings at or above the configured severity unless allowlisted.
 * Mirrors apps/api/scripts/pip_audit_check.py.
 */

import { execSync } from "node:child_process";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const MIN_SEVERITY = "critical";
const ORDER = ["low", "moderate", "high", "critical"];

const allowlistPath = join(
  dirname(fileURLToPath(import.meta.url)),
  "npm_audit_allowlist.txt",
);

function loadAllowlist() {
  const ids = new Set();
  for (const raw of readFileSync(allowlistPath, "utf8").split(/\r?\n/)) {
    const line = raw.trim();
    if (!line || line.startsWith("#")) {
      continue;
    }
    ids.add(line);
  }
  return ids;
}

function severityRank(value) {
  const index = ORDER.indexOf(String(value).toLowerCase());
  return index === -1 ? 0 : index;
}

function minRank() {
  return severityRank(MIN_SEVERITY);
}

function parseAudit(stdout) {
  const data = JSON.parse(stdout);
  const unexpected = [];
  for (const row of data.vulnerabilities ? Object.values(data.vulnerabilities) : []) {
    const severity = row.severity ?? "moderate";
    if (severityRank(severity) < minRank()) {
      continue;
    }
    const name = row.name ?? "?";
    const via = row.via ?? [];
    const findings = [];
    for (const item of via) {
      if (typeof item === "string") {
        findings.push(item);
        continue;
      }
      const id = String(item.source ?? item.name ?? item.title ?? "?");
      const url = item.url ?? "";
      const ghsa = url.includes("/GHSA-")
        ? url.split("/").pop()
        : id.startsWith("GHSA-")
          ? id
          : null;
      findings.push(ghsa ?? id);
    }
    const unlisted = findings.filter(
      (id) => id && !allow.has(id) && !allow.has(String(id).split("/").pop()),
    );
    if (unlisted.length === 0 && findings.length > 0) {
      continue;
    }
    if (findings.length === 0) {
      unexpected.push(`${name} (no advisory id, ${severity})`);
      continue;
    }
    for (const id of unlisted) {
      unexpected.push(`${name} ${id} (${severity})`);
    }
  }
  return unexpected;
}

const allow = loadAllowlist();
let stdout;
try {
  stdout = execSync("npm audit --json", {
    encoding: "utf8",
    stdio: ["ignore", "pipe", "pipe"],
  });
} catch (error) {
  stdout = error.stdout?.toString() ?? "";
  if (!stdout.trim()) {
    console.error(error.stderr?.toString() ?? error.message);
    process.exit(1);
  }
}

let unexpected;
try {
  unexpected = parseAudit(stdout);
} catch (error) {
  console.error(stdout);
  console.error(error);
  process.exit(1);
}

if (unexpected.length > 0) {
  console.error(`Unexpected ${MIN_SEVERITY}+ npm audit findings:`);
  for (const line of unexpected) {
    console.error(`  ${line}`);
  }
  console.error(
    "Add advisory ids to apps/web/scripts/npm_audit_allowlist.txt only with a tracked upgrade plan.",
  );
  process.exit(1);
}

console.log(
  `npm audit ok (min severity ${MIN_SEVERITY}, ${allow.size} allowlisted id(s))`,
);
