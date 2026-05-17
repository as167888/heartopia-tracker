const USER_AGENT =
  "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36";

function beijingTimestamp() {
  const utc = Date.now() + 8 * 60 * 60 * 1000; // UTC+8, no DST
  const d = new Date(utc);
  const p = (n) => String(n).padStart(2, "0");
  return `${d.getUTCFullYear()}-${p(d.getUTCMonth() + 1)}-${p(d.getUTCDate())} ${p(d.getUTCHours())}:${p(d.getUTCMinutes())}:${p(d.getUTCSeconds())}`;
}

async function fetchDiscord(env) {
  const resp = await fetch(env.DISCORD_API, { headers: { "User-Agent": USER_AGENT } });
  if (!resp.ok) throw new Error(`Discord HTTP ${resp.status}`);
  const json = await resp.json();
  return {
    member_count: json.approximate_member_count,
    presence_count: json.approximate_presence_count,
    guild_name: json.guild?.name ?? "",
  };
}

async function readData(env) {
  const url = `https://api.github.com/repos/${env.GITHUB_OWNER}/${env.GITHUB_REPO}/contents/${env.DATA_PATH}`;
  const resp = await fetch(url, {
    headers: {
      Authorization: `Bearer ${env.GITHUB_TOKEN}`,
      "User-Agent": "heartopia-worker",
      Accept: "application/vnd.github.v3+json",
    },
  });
  if (resp.status === 404) return { entries: [], sha: null };
  if (!resp.ok) throw new Error(`GitHub read HTTP ${resp.status}`);
  const raw = await resp.json();
  return {
    entries: JSON.parse(atob(raw.content)),
    sha: raw.sha,
  };
}

async function writeData(env, entries, sha) {
  const url = `https://api.github.com/repos/${env.GITHUB_OWNER}/${env.GITHUB_REPO}/contents/${env.DATA_PATH}`;
  const content = btoa(JSON.stringify(entries, null, 2));
  const body = { message: "Update data [skip ci]", content };
  if (sha) body.sha = sha;

  const resp = await fetch(url, {
    method: "PUT",
    headers: {
      Authorization: `Bearer ${env.GITHUB_TOKEN}`,
      "User-Agent": "heartopia-worker",
      Accept: "application/vnd.github.v3+json",
      "Content-Type": "application/json",
    },
    body: JSON.stringify(body),
  });
  if (!resp.ok) {
    const text = await resp.text();
    throw new Error(`GitHub write HTTP ${resp.status}: ${text}`);
  }
  return resp.json();
}

async function collect(env) {
  const info = await fetchDiscord(env);
  const { entries, sha } = await readData(env);

  entries.push({
    timestamp: beijingTimestamp(),
    member_count: info.member_count,
    presence_count: info.presence_count,
  });

  const result = await writeData(env, entries, sha);
  return { info, commit: result.commit?.sha?.slice(0, 7) };
}

export default {
  async scheduled(_event, env, ctx) {
    ctx.waitUntil(
      collect(env)
        .then((r) => console.log(`[${r.info.guild_name}] members=${r.info.member_count} online=${r.info.presence_count} commit=${r.commit}`))
        .catch((e) => console.error(`[ERROR] ${e.message}`))
    );
  },

  async fetch(_request, env) {
    try {
      const r = await collect(env);
      return new Response(
        JSON.stringify({ ok: true, guild: r.info.guild_name, members: r.info.member_count, online: r.info.presence_count, commit: r.commit }),
        { status: 200, headers: { "Content-Type": "application/json" } }
      );
    } catch (e) {
      return new Response(
        JSON.stringify({ ok: false, error: e.message }),
        { status: 500, headers: { "Content-Type": "application/json" } }
      );
    }
  },
};
