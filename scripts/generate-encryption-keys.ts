import { existsSync, readFileSync, writeFileSync } from "node:fs";
import { randomBytes } from "node:crypto";

const target = ".env.local";
const generated = {
  ENCRYPTION_KEY: randomBytes(32).toString("hex"),
  HASH_KEY: randomBytes(32).toString("hex"),
};

const existing = existsSync(target) ? readFileSync(target, "utf8") : "";
const lines = existing ? existing.trimEnd().split(/\r?\n/) : [];
const keys = new Set(lines.map((line) => line.split("=", 1)[0]));

for (const [name, value] of Object.entries(generated)) {
  if (!keys.has(name)) {
    lines.push(`${name}=${value}`);
  }
}

writeFileSync(target, `${lines.join("\n")}\n`, { mode: 0o600 });
console.log(`${target} now contains ENCRYPTION_KEY and HASH_KEY entries.`);
