// Posts one Kleo film to X (@kleooai) with text: chunked media upload (v2) + POST /2/tweets.
// OAuth 1.0a user context, signed with node:crypto only — no dependencies.
//
//   node scripts/publish-x.mjs --video https://kleooai.com/samples/realistic-tether.mp4 --text "..." [--dry-run]
//
// Secrets (env): X_API_KEY, X_API_SECRET, X_ACCESS_TOKEN, X_ACCESS_SECRET
// (Developer portal → your app → Keys and tokens; the access token must be generated
//  AFTER the app permissions are set to "Read and write".)
// Exit code is non-zero on any failure so the workflow goes red for real.

import { createHmac, randomBytes } from "node:crypto";

const args = Object.fromEntries(
  process.argv.slice(2).reduce((acc, a, i, all) => {
    if (a.startsWith("--")) acc.push([a.slice(2), all[i + 1]?.startsWith("--") || all[i + 1] === undefined ? "true" : all[i + 1]]);
    return acc;
  }, []),
);
const videoUrl = args.video;
const text = args.text ?? "";
const dry = args["dry-run"] === "true";
if (!text) fail("--text is required");
if (text.length > 280) fail(`text is ${text.length} chars, X allows 280`);

const env = process.env;
const missing = ["X_API_KEY", "X_API_SECRET", "X_ACCESS_TOKEN", "X_ACCESS_SECRET"].filter((k) => !env[k]);
if (dry) {
  console.log(`dry-run: text ok (${text.length} chars), video ${videoUrl ?? "none"}, missing secrets: ${missing.join(", ") || "none"}`);
  process.exit(0);
}
if (missing.length) fail(`missing secrets: ${missing.join(", ")}`);

const enc = (s) => encodeURIComponent(s).replace(/[!'()*]/g, (c) => "%" + c.charCodeAt(0).toString(16).toUpperCase());

function authHeader(method, url, query = {}) {
  const oauth = {
    oauth_consumer_key: env.X_API_KEY,
    oauth_nonce: randomBytes(16).toString("hex"),
    oauth_signature_method: "HMAC-SHA1",
    oauth_timestamp: Math.floor(Date.now() / 1000).toString(),
    oauth_token: env.X_ACCESS_TOKEN,
    oauth_version: "1.0",
  };
  const params = { ...query, ...oauth };
  const base = [method.toUpperCase(), enc(url), enc(Object.keys(params).sort().map((k) => `${enc(k)}=${enc(params[k])}`).join("&"))].join("&");
  const key = `${enc(env.X_API_SECRET)}&${enc(env.X_ACCESS_SECRET)}`;
  oauth.oauth_signature = createHmac("sha1", key).update(base).digest("base64");
  return "OAuth " + Object.keys(oauth).sort().map((k) => `${enc(k)}="${enc(oauth[k])}"`).join(", ");
}

async function call(method, url, { query = {}, json, form } = {}) {
  const qs = Object.keys(query).length ? "?" + new URLSearchParams(query) : "";
  const headers = { Authorization: authHeader(method, url, query) };
  let body;
  if (json) { headers["Content-Type"] = "application/json"; body = JSON.stringify(json); }
  if (form) body = form;
  const r = await fetch(url + qs, { method, headers, body });
  const txt = await r.text();
  let data; try { data = JSON.parse(txt); } catch { data = { raw: txt }; }
  if (!r.ok) fail(`${method} ${url} → ${r.status} ${txt.slice(0, 500)}`);
  return data;
}

let mediaId;
if (videoUrl) {
  const res = await fetch(videoUrl);
  if (!res.ok) fail(`video download ${res.status}`);
  const buf = Buffer.from(await res.arrayBuffer());
  const mediaType = res.headers.get("content-type") || "video/mp4";
  console.log(`video ${buf.length} bytes, ${mediaType}`);

  const init = await call("POST", "https://api.x.com/2/media/upload/initialize", {
    json: { media_type: mediaType, total_bytes: buf.length, media_category: "tweet_video" },
  });
  mediaId = init.data?.id ?? init.media_id_string ?? init.id;
  if (!mediaId) fail("no media id from initialize: " + JSON.stringify(init));

  const chunk = 4 * 1024 * 1024;
  for (let i = 0, seg = 0; i < buf.length; i += chunk, seg++) {
    const form = new FormData();
    form.append("segment_index", String(seg));
    form.append("media", new Blob([buf.subarray(i, i + chunk)], { type: mediaType }), "chunk.mp4");
    await call("POST", `https://api.x.com/2/media/upload/${mediaId}/append`, { form });
  }
  let fin = await call("POST", `https://api.x.com/2/media/upload/${mediaId}/finalize`);
  let info = fin.data?.processing_info ?? fin.processing_info;
  while (info && info.state !== "succeeded") {
    if (info.state === "failed") fail("media processing failed: " + JSON.stringify(info));
    await new Promise((r) => setTimeout(r, (info.check_after_secs ?? 2) * 1000));
    const st = await call("GET", "https://api.x.com/2/media/upload", { query: { command: "STATUS", media_id: mediaId } });
    info = st.data?.processing_info ?? st.processing_info;
  }
  console.log(`media ${mediaId} ready`);
}

const post = await call("POST", "https://api.x.com/2/tweets", {
  json: mediaId ? { text, media: { media_ids: [String(mediaId)] } } : { text },
});
const id = post.data?.id;
if (!id) fail("no post id: " + JSON.stringify(post));
console.log(`posted https://x.com/kleooai/status/${id}`);

function fail(msg) { console.error("publish-x: " + msg); process.exit(1); }
