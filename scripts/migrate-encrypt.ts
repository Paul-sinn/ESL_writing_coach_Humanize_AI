import { Client } from "pg";
import { encrypt, hashForLookup } from "../lib/encryption";

function isEncrypted(value: string | null): boolean {
  return value != null && /^[0-9a-f]+:[0-9a-f]+:[0-9a-f]+$/i.test(value);
}

async function main() {
  const databaseUrl = process.env.DATABASE_URL;
  if (!databaseUrl) {
    throw new Error("DATABASE_URL is required.");
  }

  const client = new Client({ connectionString: databaseUrl });
  await client.connect();

  try {
    await client.query("BEGIN");

    const profiles = await client.query<{
      id: string;
      email: string | null;
      full_name: string | null;
    }>("SELECT id, email, full_name FROM profiles");

    for (const row of profiles.rows) {
      const emailPlain = isEncrypted(row.email) ? null : row.email;
      const fullNamePlain = isEncrypted(row.full_name) ? null : row.full_name;
      await client.query(
        `
          UPDATE profiles
          SET
            email = COALESCE($2, email),
            email_hash = COALESCE($3, email_hash),
            full_name = COALESCE($4, full_name),
            full_name_hash = COALESCE($5, full_name_hash)
          WHERE id = $1
        `,
        [
          row.id,
          emailPlain == null ? null : encrypt(emailPlain),
          emailPlain == null ? null : hashForLookup(emailPlain),
          fullNamePlain == null ? null : encrypt(fullNamePlain),
          fullNamePlain == null ? null : hashForLookup(fullNamePlain),
        ],
      );
    }

    const logs = await client.query<{ id: number; ip_address: string | null }>(
      "SELECT id, ip_address FROM user_activity_logs WHERE ip_address IS NOT NULL",
    );
    for (const row of logs.rows) {
      if (isEncrypted(row.ip_address)) continue;
      await client.query(
        "UPDATE user_activity_logs SET ip_address = $2 WHERE id = $1",
        [row.id, encrypt(row.ip_address)],
      );
    }

    await client.query("COMMIT");
    console.log(`Encrypted ${profiles.rowCount} profiles and scanned ${logs.rowCount} activity logs.`);
  } catch (error) {
    await client.query("ROLLBACK");
    throw error;
  } finally {
    await client.end();
  }
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
