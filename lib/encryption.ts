import { createCipheriv, createDecipheriv, createHmac, randomBytes } from "node:crypto";

function keyFromEnv(name: "ENCRYPTION_KEY" | "HASH_KEY"): Buffer {
  const value = process.env[name]?.trim() ?? "";
  if (!/^[0-9a-fA-F]{64}$/.test(value)) {
    throw new Error(`${name} must be a 32-byte key encoded as 64 hex characters.`);
  }
  return Buffer.from(value, "hex");
}

export function encrypt(value: string | null | undefined): string | null {
  if (value == null) return null;
  const iv = randomBytes(16);
  const cipher = createCipheriv("aes-256-gcm", keyFromEnv("ENCRYPTION_KEY"), iv);
  const encrypted = Buffer.concat([cipher.update(value, "utf8"), cipher.final()]);
  const authTag = cipher.getAuthTag();
  return `${iv.toString("hex")}:${authTag.toString("hex")}:${encrypted.toString("hex")}`;
}

export function decrypt(value: string | null | undefined): string | null {
  if (value == null) return null;
  const [ivHex, authTagHex, encryptedHex] = value.split(":");
  if (!ivHex || !authTagHex || !encryptedHex) {
    throw new Error("Encrypted values must use iv:authTag:encryptedData hex format.");
  }
  const decipher = createDecipheriv("aes-256-gcm", keyFromEnv("ENCRYPTION_KEY"), Buffer.from(ivHex, "hex"));
  decipher.setAuthTag(Buffer.from(authTagHex, "hex"));
  return Buffer.concat([
    decipher.update(Buffer.from(encryptedHex, "hex")),
    decipher.final(),
  ]).toString("utf8");
}

export function hashForLookup(value: string | null | undefined): string | null {
  if (value == null) return null;
  return createHmac("sha256", keyFromEnv("HASH_KEY"))
    .update(value.trim().toLocaleLowerCase())
    .digest("hex");
}
