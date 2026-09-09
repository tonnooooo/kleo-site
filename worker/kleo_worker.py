#!/usr/bin/env python3
"""
Kleo GPU worker — runs INSIDE the ephemeral Vast.ai instance, one job per instance.

It talks only to the Kleo API (KLEO_API) with the per-job secret (KLEO_SECRET):
  1. fetch the job spec              GET  /internal/jobs/{id}
  2. report progress                 POST /internal/jobs/{id}/progress
  3. render (see render() below)     <-- plug your ComfyUI / Wan / LTX / ffmpeg pipeline here
  4. upload the outputs              PUT  /internal/jobs/{id}/files/{name}  (multipart for big files)
  5. mark done / failed              POST /internal/jobs/{id}/done | /failed
  6. destroy this very instance      DELETE https://console.vast.ai/api/v0/instances/$CONTAINER_ID/  (CONTAINER_API_KEY)
A watchdog timer (KLEO_SELF_DESTRUCT_MIN) destroys the instance even if the render hangs.
Standard library only, so it runs in any image with python3 and ffmpeg.
"""
import json, os, sys, time, threading, subprocess, tempfile, urllib.request, urllib.error, traceback

API = os.environ.get("KLEO_API", "").rstrip("/")
JOB = os.environ.get("KLEO_JOB_ID", "")
SECRET = os.environ.get("KLEO_SECRET", "")
SELF_DESTRUCT_MIN = int(os.environ.get("KLEO_SELF_DESTRUCT_MIN", "110"))
PART = 50 * 1024 * 1024


def log(*a):
    print(time.strftime("%H:%M:%S"), *a, flush=True)


def api(method, path, data=None, raw=None, ctype="application/json", retries=3):
    body = raw if raw is not None else (json.dumps(data).encode() if data is not None else None)
    req = urllib.request.Request(f"{API}{path}", data=body, method=method)
    req.add_header("Authorization", f"Bearer {SECRET}")
    if body is not None:
        req.add_header("Content-Type", ctype)
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                txt = r.read().decode() or "{}"
                return json.loads(txt) if txt.startswith("{") else txt
        except urllib.error.HTTPError as e:
            if 400 <= e.code < 500:
                raise
            log("api error", e.code, "retrying")
        except Exception as e:  # network hiccup
            log("api error", e, "retrying")
        time.sleep(2 * (attempt + 1))
    raise RuntimeError(f"api {method} {path} failed after {retries} tries")


def progress(track, percent, eta_min=None, message=None):
    try:
        api("POST", f"/internal/jobs/{JOB}/progress", {"track": track, "percent": percent, "eta_min": eta_min, "message": message})
    except Exception as e:
        log("progress report failed:", e)


def upload(path, name):
    size = os.path.getsize(path)
    if size <= 90 * 1024 * 1024:
        with open(path, "rb") as f:
            api("PUT", f"/internal/jobs/{JOB}/files/{name}", raw=f.read(), ctype="application/octet-stream")
        return
    up = api("POST", f"/internal/jobs/{JOB}/files/{name}/uploads")
    uid, parts, n = up["uploadId"], [], 1
    with open(path, "rb") as f:
        while True:
            chunk = f.read(PART)
            if not chunk:
                break
            r = api("PUT", f"/internal/jobs/{JOB}/files/{name}/uploads/{uid}/parts/{n}", raw=chunk, ctype="application/octet-stream")
            parts.append({"partNumber": r["partNumber"], "etag": r["etag"]})
            log(f"uploaded part {n} of {name}")
            n += 1
    api("POST", f"/internal/jobs/{JOB}/files/{name}/uploads/{uid}/complete", {"parts": parts})


def self_destruct(reason):
    """Destroy this instance with the restricted key Vast injects into every container."""
    log("self-destruct:", reason)
    cid, key = os.environ.get("CONTAINER_ID"), os.environ.get("CONTAINER_API_KEY")
    if cid and key:
        try:
            req = urllib.request.Request(f"https://console.vast.ai/api/v0/instances/{cid}/", method="DELETE")
            req.add_header("Authorization", f"Bearer {key}")
            urllib.request.urlopen(req, timeout=30).read()
            return
        except Exception as e:
            log("direct destroy failed:", e)
    try:
        api("POST", f"/internal/jobs/{JOB}/selfdestruct")
    except Exception as e:
        log("server-side destroy failed:", e)


def watchdog():
    t = threading.Timer(SELF_DESTRUCT_MIN * 60, lambda: (api_safe_fail("watchdog timeout"), self_destruct("watchdog")))
    t.daemon = True
    t.start()


def api_safe_fail(msg):
    try:
        api("POST", f"/internal/jobs/{JOB}/failed", {"error": msg, "retry": True})
    except Exception:
        pass


# ----------------------------------------------------------------------------------------------
# RENDER PIPELINE — replace the body of render() with the real thing.
# It must write video.mp4, subtitles.srt and thumbnail.jpg into out_dir and call progress().
# Tracks and percent ranges expected by the server: script 0-8, voice 8-16, clips 16-64, edit 64-78, finishing 78-99.
# ----------------------------------------------------------------------------------------------
def render(job, out_dir):
    p = job["params"]
    dur = int(p.get("duration_s", 45))
    w, h = (2160, 3840) if p.get("format") == "9:16" else (3840, 2160)
    prompt = job["prompt"]

    progress("script", 3, message="writing script")          # 1. LLM → script/scenes
    time.sleep(1)
    progress("voice", 10, message="synthesizing voice")        # 2. TTS
    time.sleep(1)
    progress("clips", 20, message="generating clips")          # 3. Wan / LTX per scene (parallel)
    # placeholder video: dark frame with the prompt as text, correct resolution, 60 fps, real length
    video = os.path.join(out_dir, "video.mp4")
    txt = prompt.replace("'", "").replace(":", " ")[:60]
    vf = f"drawtext=text='{txt}':fontcolor=white:fontsize={h//30}:x=(w-text_w)/2:y=(h-text_h)/2"
    base = ["ffmpeg", "-loglevel", "error", "-y", "-f", "lavfi", "-i", f"color=c=0x0F1216:s={w}x{h}:d={dur}:r=60",
            "-f", "lavfi", "-i", f"sine=f=220:d={dur}"]
    enc = ["-c:v", "libx264", "-preset", "veryfast", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "96k", "-movflags", "+faststart", "-shortest", video]
    if subprocess.run(base + ["-vf", vf] + enc).returncode != 0:
        subprocess.run(base + enc, check=True)               # no font available: skip the text
    progress("edit", 70, message="editing")                    # 4. ffmpeg: cuts, captions, music
    with open(os.path.join(out_dir, "subtitles.srt"), "w") as f:
        f.write(f"1\n00:00:00,000 --> 00:00:05,000\n{prompt[:90]}\n")
    progress("finishing", 85, message="upscale + 60 fps")      # 5. SeedVR2 → RIFE → H.265
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", video, "-frames:v", "1", "-q:v", "3", os.path.join(out_dir, "thumbnail.jpg")], check=True)
    progress("finishing", 95, message="encoded")
    return {"video.mp4": video, "subtitles.srt": os.path.join(out_dir, "subtitles.srt"), "thumbnail.jpg": os.path.join(out_dir, "thumbnail.jpg")}


def main():
    if not (API and JOB and SECRET):
        log("missing KLEO_API / KLEO_JOB_ID / KLEO_SECRET"); sys.exit(2)
    watchdog()
    started = time.time()
    try:
        job = api("GET", f"/internal/jobs/{JOB}")
        log("job", JOB, job["template"], job["params"])
        progress("script", 1, message="worker started")
        out_dir = tempfile.mkdtemp(prefix="kleo-")
        files = render(job, out_dir)
        for name, path in files.items():
            progress("finishing", 97, message=f"uploading {name}")
            upload(path, name)
        cost = None
        dph = os.environ.get("KLEO_DPH")                      # optional: orchestrator can pass the hourly price
        if dph:
            cost = round(float(dph) * (time.time() - started) / 3600, 4)
        api("POST", f"/internal/jobs/{JOB}/done", {"cost_usd": cost})
        log("done in %.0f s" % (time.time() - started))
        self_destruct("finished")
    except Exception as e:
        log("FAILED:", e); traceback.print_exc()
        api_safe_fail(str(e)[:500])
        self_destruct("failed")


if __name__ == "__main__":
    main()
