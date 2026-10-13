#!/usr/bin/env python3
"""Voice the WorldForge avatar intro lines with Kokoro, a free open-source neural voice (Apache-2.0) that runs locally.

    .cache/voice/venv/bin/python worldforge/voice/voice_intros.py            # render, resumable, time-boxed
    .cache/voice/venv/bin/python worldforge/voice/voice_intros.py --plan     # show what would be rendered, render nothing
    python3 worldforge/voice/voice_intros.py --check                         # verify the manifest (no Kokoro needed)

Options: --budget-min N (wall-clock time box, default 35, sleeps included), --limit N (render at most N lines),
--batch N (lines per batch between registry re-reads, default 10).

Input: worldforge/out/avatars/index.json rows (avatarId, world, role, intro.text, voice.id), written by
worldforge/avatars.mjs. The registry is re-read before every batch, because another builder may be adding rows.
Output: worldforge/out/voices/<world>/<last path segment of avatarId>.mp4 (mono AAC in an .mp4 container at 48 kbps,
24 kHz, the hive's format: artifacts serve .mp4, not .m4a), loudness normalised with ffmpeg loudnorm in two passes
(-16 LUFS integrated, -1.5 dBTP), and worldforge/out/voices/manifest.json, which lists only lines actually rendered.

Each line is spoken with the row's voice.id at speed 1.0, with nothing prepended. A row whose intro text does not
itself say the voice is synthetic is skipped and reported. Omega rows are not voiced here: their greet line is the
hive's, voiced by agents/hive_voice.py to the path in the row's voice.audio.greet.

Priority: the coordinators, then the first specialist of each world, then advisors (host, liaison, alignment and any
other role that is not specialist, coordinator or omega), then the remaining specialists. Resumable: a line is
skipped when its .mp4 exists and its manifest entry has the same text hash, voice and path. Stale entries (text or
voice changed, row gone) are dropped from the manifest and their .mp4 removed before rendering, so a viewer that
HEAD-checks the contract path never plays an outdated line.

CPU etiquette: at most 2 threads (one Kokoro session with intra_op_num_threads=2, ffmpeg -threads 1); before each
line the local time (as date +%H:%M) is checked and the run sleeps through the other team's film render windows
07:25-07:35, 08:10-08:20 and 09:50-10:05.

Nothing is sent anywhere; no account, key or credits are involved. Not done here: lip sync, any live or AI speech
(the intro lines are scripted text), and voicing omega lines.
"""
import hashlib, json, os, re, shutil, struct, subprocess, sys, tempfile, time

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
REGISTRY = os.path.join(ROOT, "worldforge", "out", "avatars", "index.json")
OUT_REL = "worldforge/out/voices"
OUT = os.path.join(ROOT, *OUT_REL.split("/"))
MANIFEST = os.path.join(OUT, "manifest.json")
CACHE = os.path.join(ROOT, ".cache", "voice")
LOCAL_BIN = os.path.join(ROOT, ".cache", "bin")

ENGINE = "Kokoro v1.0 (kokoro-onnx), local"
SPEED = 1.0
THREADS = 2
LOUDNORM = {"I": -16.0, "TP": -1.5, "LRA": 11.0}
CODEC = {"container": "mp4", "codec": "aac", "channels": 1, "bitrate": "48k", "sample_rate": 24000}
QUIET_WINDOWS = [("07:25", "07:35"), ("08:10", "08:20"), ("09:50", "10:05")]
DURATION_TOLERANCE = 0.05
SYNTHETIC = re.compile(r"\bsynthetic\b", re.I)
SLUG = re.compile(r"^[a-z0-9][a-z0-9-]{0,47}$")
ADVISOR_ROLES = ("host", "liaison", "alignment")
TIER_NAMES = ["coordinator", "first specialist", "advisor", "specialist"]


# ---------------------------------------------------------------- registry and plan

def load_registry():
    """The registry may be mid-write by another builder: retry a few times on a partial file."""
    last = None
    for _ in range(6):
        try:
            with open(REGISTRY) as f:
                return json.load(f)["rows"]
        except (OSError, ValueError, KeyError) as e:
            last = e
            time.sleep(2)
    raise SystemExit(f"FAIL voices: cannot read worldforge/out/avatars/index.json ({last})")


def text_sha(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def audio_rel(row):
    """The avatar audio path contract: worldforge/out/voices/<world>/<last path segment of avatarId>.mp4, or None."""
    world, aid = row.get("world") or "", row.get("avatarId") or ""
    if not SLUG.match(world) or not aid.startswith(f"avatar:{world}/"):
        return None
    seg = aid.rsplit("/", 1)[-1]
    if not SLUG.match(seg):
        return None
    return f"{OUT_REL}/{world}/{seg}.mp4"


def lang_of(voice):
    return "en-gb" if voice.startswith(("bf_", "bm_")) else "en-us"


def plan(rows):
    """Every in-scope intro line in priority order, plus the rows skipped and why."""
    lines, skipped, seen_first = [], [], set()
    for idx, r in enumerate(rows):
        role = r.get("role")
        aid = r.get("avatarId", "?")
        if role == "omega":
            continue  # the hive voices the omega greet line (voice.audio.greet); out of scope here
        text = ((r.get("intro") or {}).get("text") or "").strip()
        if not text:
            continue  # intro not written yet (another builder may be adding it)
        if role == "coordinator":
            tier = 0
        elif role == "specialist":
            tier = 1 if r.get("world") not in seen_first else 3
            seen_first.add(r.get("world"))
        else:
            tier = 2  # advisors: host, liaison, alignment (and any newer non-agent role)
        voice = ((r.get("voice") or {}).get("id") or "").strip()
        path = audio_rel(r)
        if not path:
            skipped.append({"avatarId": aid, "why": "avatarId/world do not give a safe contract path"})
            continue
        if not re.match(r"^[ab][fm]_[a-z]+$", voice):
            skipped.append({"avatarId": aid, "why": f"no Kokoro voice id ({voice or 'none'})"})
            continue
        if not SYNTHETIC.search(text):
            skipped.append({"avatarId": aid, "why": "intro text does not say the voice is synthetic"})
            continue
        lines.append({"avatarId": aid, "role": role, "world": r["world"], "tier": tier, "order": idx, "text": text,
                      "voice": voice, "lang": lang_of(voice), "path": path, "text_sha256": text_sha(text)})
    by_path = {}
    for ln in lines:
        by_path.setdefault(ln["path"], []).append(ln)
    clash = {p for p, v in by_path.items() if len(v) > 1}
    for p in sorted(clash):
        for ln in by_path[p]:
            skipped.append({"avatarId": ln["avatarId"], "why": f"contract path {p} is shared with another avatar"})
    lines = [ln for ln in lines if ln["path"] not in clash]
    lines.sort(key=lambda ln: (ln["tier"], ln["order"]))
    return lines, skipped


# ---------------------------------------------------------------- manifest

def read_manifest():
    try:
        with open(MANIFEST) as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


def build_manifest(entries):
    lines = sorted(entries, key=lambda e: e["path"])
    by_role = {}
    for e in lines:
        by_role[e.get("role", "?")] = by_role.get(e.get("role", "?"), 0) + 1
    return {
        "schemaVersion": "worldforge-voices/0.1",
        "generator": "worldforge/voice/voice_intros.py",
        "engine": ENGINE,
        "settings": {"speed": SPEED, "prepend": None, "threads": THREADS,
                     "loudnorm": {"integrated_lufs": LOUDNORM["I"], "true_peak_dbtp": LOUDNORM["TP"], "lra": LOUDNORM["LRA"], "passes": 2},
                     "output": CODEC},
        "path_contract": "worldforge/out/voices/<world>/<last path segment of avatarId>.mp4",
        "scope": "intro lines of coordinator, specialist and advisor rows; omega greet lines are the hive's (agents/hive_voice.py)",
        "honesty": ["Synthetic voice: every line is Kokoro text-to-speech of a scripted intro that itself says the voice is synthetic.",
                    "This manifest lists only lines actually rendered; a missing entry means not voiced.",
                    "No model speaks live here; the intro lines are scripted text from worldforge/out/avatars/index.json."],
        "lines": [{"avatarId": e["avatarId"], "role": e.get("role"), "path": e["path"], "voice": e["voice"],
                   "seconds": e["seconds"], "text_sha256": e["text_sha256"]} for e in lines],
        "totals": {"lines": len(lines), "seconds": round(sum(e["seconds"] for e in lines), 2), "by_role": dict(sorted(by_role.items()))},
    }


def dump(obj):
    return json.dumps(obj, indent=1, ensure_ascii=False) + "\n"


def write_manifest(entries):
    os.makedirs(OUT, exist_ok=True)
    tmp = MANIFEST + f".{os.getpid()}.tmp"
    with open(tmp, "w") as f:
        f.write(dump(build_manifest(entries)))
    os.replace(tmp, MANIFEST)


# ---------------------------------------------------------------- audio

def mp4_seconds(path):
    """Duration from the mp4 movie header (mvhd), which carries the edit list length ffmpeg writes. Pure Python."""
    with open(path, "rb") as f:
        data = f.read()

    def boxes(buf, start, end):
        i = start
        while i + 8 <= end:
            size, kind = struct.unpack(">I4s", buf[i:i + 8])
            hdr = 8
            if size == 1:
                size = struct.unpack(">Q", buf[i + 8:i + 16])[0]
                hdr = 16
            elif size == 0:
                size = end - i
            if size < hdr:
                return
            yield kind, i + hdr, i + size
            i += size

    for kind, s, e in boxes(data, 0, len(data)):
        if kind == b"moov":
            for k2, s2, e2 in boxes(data, s, e):
                if k2 == b"mvhd":
                    ver = data[s2]
                    if ver == 1:
                        scale, dur = struct.unpack(">IQ", data[s2 + 20:s2 + 32])
                    else:
                        scale, dur = struct.unpack(">II", data[s2 + 12:s2 + 20])
                    return dur / scale if scale else None
    return None


def ffmpeg():
    local = os.path.join(LOCAL_BIN, "ffmpeg")
    return local if os.path.exists(local) else shutil.which("ffmpeg")


def loudnorm_filter(measured=None):
    f = f"loudnorm=I={LOUDNORM['I']}:TP={LOUDNORM['TP']}:LRA={LOUDNORM['LRA']}"
    if measured is None:
        return f + ":print_format=json"
    return (f + f":measured_I={measured['input_i']}:measured_TP={measured['input_tp']}:measured_LRA={measured['input_lra']}"
            f":measured_thresh={measured['input_thresh']}:offset={measured['target_offset']}:linear=true:print_format=summary")


def encode(wav, out):
    """Two-pass loudnorm, then mono AAC 48 kbps in .mp4. Returns an error string or None."""
    ff = ffmpeg()
    r = subprocess.run([ff, "-hide_banner", "-nostats", "-threads", "1", "-i", wav, "-af", loudnorm_filter(), "-f", "null", "-"],
                       capture_output=True, text=True)
    m = re.findall(r"\{[^{}]*\}", r.stderr)
    if r.returncode != 0 or not m:
        return "loudnorm measure failed: " + r.stderr.strip()[-200:]
    measured = json.loads(m[-1])
    if not all(re.match(r"^-?\d+(\.\d+)?$", str(measured.get(k, ""))) for k in ("input_i", "input_tp", "input_lra", "input_thresh", "target_offset")):
        return f"loudnorm measure not numeric: {measured}"
    part = out + ".part.mp4"
    r = subprocess.run([ff, "-v", "error", "-y", "-threads", "1", "-i", wav, "-af", loudnorm_filter(measured),
                        "-ar", str(CODEC["sample_rate"]), "-ac", "1", "-c:a", "aac", "-b:a", CODEC["bitrate"],
                        "-map_metadata", "-1", "-fflags", "+bitexact", "-flags:a", "+bitexact", "-movflags", "+faststart", part],
                       capture_output=True, text=True)
    if r.returncode != 0:
        try:
            os.remove(part)
        except OSError:
            pass
        return "encode failed: " + r.stderr.strip()[-200:]
    os.replace(part, out)
    return None


def make_kokoro():
    import onnxruntime as rt
    from kokoro_onnx import Kokoro
    opts = rt.SessionOptions()
    opts.intra_op_num_threads = THREADS
    opts.inter_op_num_threads = 1
    sess = rt.InferenceSession(os.path.join(CACHE, "kokoro-v1.0.onnx"), sess_options=opts, providers=["CPUExecutionProvider"])
    return Kokoro.from_session(sess, os.path.join(CACHE, "voices-v1.0.bin"))


# ---------------------------------------------------------------- etiquette

def quiet_wait_seconds():
    """Seconds until the current film render window ends, or 0 when outside every window (local time, date +%H:%M)."""
    now = time.localtime()
    hm = f"{now.tm_hour:02d}:{now.tm_min:02d}"
    for a, b in QUIET_WINDOWS:
        if a <= hm < b:
            bh, bm = map(int, b.split(":"))
            return max(1, (bh * 60 + bm) * 60 - (now.tm_hour * 3600 + now.tm_min * 60 + now.tm_sec)), a, b
    return 0, None, None


# ---------------------------------------------------------------- run

def arg(name, default):
    if name in sys.argv:
        i = sys.argv.index(name)
        if i + 1 < len(sys.argv):
            return float(sys.argv[i + 1])
    return default


def current_entries(lines_by_id):
    """Manifest entries still true of disk and registry; stale ones are returned separately."""
    disk = read_manifest() or {}
    keep, stale = [], []
    for e in disk.get("lines", []):
        ln = lines_by_id.get(e.get("avatarId"))
        p = os.path.join(ROOT, e.get("path", ""))
        ok = (ln is not None and ln["path"] == e.get("path") and ln["text_sha256"] == e.get("text_sha256")
              and ln["voice"] == e.get("voice") and os.path.exists(p))
        (keep if ok else stale).append(e)
    return keep, stale


def run():
    budget = arg("--budget-min", 35.0) * 60
    limit = int(arg("--limit", 10 ** 9))
    batch = max(1, int(arg("--batch", 10)))
    plan_only = "--plan" in sys.argv
    t_start = time.time()
    deadline = t_start + budget
    rows = load_registry()
    lines, skipped = plan(rows)
    by_id = {ln["avatarId"]: ln for ln in lines}
    keep, stale = current_entries(by_id)
    done = {e["avatarId"] for e in keep}
    todo = [ln for ln in lines if ln["avatarId"] not in done]
    counts = [sum(1 for ln in lines if ln["tier"] == t) for t in range(4)]
    print(f"voices: {len(rows)} registry rows, {len(lines)} intro lines in scope ({', '.join(f'{c} {n}' for c, n in zip(counts, TIER_NAMES))}), "
          f"{len(done)} already voiced, {len(todo)} to render, {len(skipped)} skipped, {len(stale)} stale", flush=True)
    for s in skipped:
        print(f"  skipped {s['avatarId']}: {s['why']}", flush=True)
    if plan_only:
        for ln in todo[:20]:
            print(f"  next [{TIER_NAMES[ln['tier']]}] {ln['avatarId']} -> {ln['path']} ({ln['voice']})")
        print(f"---- voices plan: {len(todo)} lines to render, {len(done)} current, {len(skipped)} skipped")
        return 0
    if not ffmpeg():
        print("FAIL voices: no ffmpeg (expected .cache/bin/ffmpeg)")
        return 1
    if stale:  # never leave an outdated line at a contract path
        for e in stale:
            p = os.path.join(ROOT, e.get("path", ""))
            if e.get("path", "").startswith(OUT_REL + "/") and e["path"].endswith(".mp4") and os.path.exists(p):
                os.remove(p)
            print(f"  dropped stale {e.get('avatarId')} ({e.get('path')})", flush=True)
        write_manifest(keep)
    entries = {e["avatarId"]: e for e in keep}
    kokoro = None
    made, failed, times, stop = 0, {}, [], None
    while made < limit:
        # re-read the registry before every batch: another builder may add rows (advisors) or change intro text
        rows = load_registry()
        lines, _ = plan(rows)
        by_id = {ln["avatarId"]: ln for ln in lines}
        for aid in [a for a, e in entries.items() if a not in by_id or by_id[a]["text_sha256"] != e["text_sha256"] or by_id[a]["voice"] != e["voice"]]:
            e = entries.pop(aid)
            p = os.path.join(ROOT, e["path"])
            if os.path.exists(p):
                os.remove(p)
            print(f"  dropped stale {aid} (registry changed mid-run)", flush=True)
            write_manifest(entries.values())
        todo = [ln for ln in lines if ln["avatarId"] not in entries and ln["avatarId"] not in failed]
        if not todo:
            stop = "all in-scope lines voiced" if not failed else "only failed lines left"
            break
        for ln in todo[:batch]:
            if made >= limit:
                stop = f"--limit {limit} reached"
                break
            wait, a, b = quiet_wait_seconds()
            if wait:
                if time.time() + wait >= deadline:
                    stop = f"time box would end inside the {a}-{b} render window"
                    break
                print(f"  render window {a}-{b}: sleeping {wait} s", flush=True)
                time.sleep(wait)
            avg = (sum(times) / len(times)) if times else 10.0
            if time.time() + avg * 1.5 > deadline:
                stop = f"time box of {budget / 60:.0f} min reached"
                break
            if kokoro is None:
                kokoro = make_kokoro()
            t0 = time.time()
            import soundfile as sf
            audio, sr = kokoro.create(ln["text"], voice=ln["voice"], speed=SPEED, lang=ln["lang"])
            t_tts = time.time() - t0
            out = os.path.join(ROOT, ln["path"])
            os.makedirs(os.path.dirname(out), exist_ok=True)
            with tempfile.TemporaryDirectory() as tmp:
                wav = os.path.join(tmp, "line.wav")
                sf.write(wav, audio, sr)
                err = encode(wav, out)
            if err:
                failed[ln["avatarId"]] = err
                print(f"FAIL {ln['avatarId']}: {err}", flush=True)
                continue
            secs = mp4_seconds(out)
            if secs is None:
                failed[ln["avatarId"]] = "no mvhd duration"
                print(f"FAIL {ln['avatarId']}: no mvhd duration", flush=True)
                continue
            dt = round(time.time() - t0, 2)
            times.append(dt)
            entries[ln["avatarId"]] = {"avatarId": ln["avatarId"], "role": ln["role"], "path": ln["path"], "voice": ln["voice"],
                                       "seconds": round(secs, 2), "text_sha256": ln["text_sha256"]}
            write_manifest(entries.values())  # saved after every line, so a stopped run resumes
            made += 1
            print(f"{ln['avatarId']}: {secs:.2f} s audio ({ln['voice']}, raw {len(audio) / sr:.2f} s), {dt:.2f} s to render ({t_tts:.2f} s TTS) "
                  f"[{TIER_NAMES[ln['tier']]}] [{made}]", flush=True)
        if stop:
            break
    if stop is None:
        stop = f"--limit {limit} reached" if made >= limit else "done"
    left = len([ln for ln in plan(load_registry())[0] if ln["avatarId"] not in entries])
    tt = f", render {min(times):.2f}-{max(times):.2f} s per line (mean {sum(times) / len(times):.2f} s)" if times else ""
    print(f"---- voices: {made} lines rendered with Kokoro in {time.time() - t_start:.0f} s{tt}; {len(entries)} voiced, "
          f"{left} left, {len(failed)} failed; stopped: {stop}", flush=True)
    return 1 if failed else 0


# ---------------------------------------------------------------- check

def check():
    rows = load_registry()
    lines, skipped = plan(rows)
    by_id = {ln["avatarId"]: ln for ln in lines}
    raw = None
    try:
        with open(MANIFEST) as f:
            raw = f.read()
    except OSError:
        pass
    fails = []
    disk = None
    if raw is None:
        entries = []
    else:
        try:
            disk = json.loads(raw)
            entries = disk.get("lines", [])
        except ValueError:
            fails.append("manifest.json is not JSON")
            entries = []
    if disk is not None:
        if disk.get("engine") != ENGINE:
            fails.append(f"engine is {disk.get('engine')!r}, want {ENGINE!r}")
        try:
            rebuilt = dump(build_manifest(entries))
            if rebuilt != raw:
                fails.append("manifest.json differs from its in-memory rebuild (order, totals or format)")
        except (KeyError, TypeError) as e:
            fails.append(f"manifest lines malformed ({e})")
    seen = set()
    for e in entries:
        aid = e.get("avatarId")
        if aid in seen:
            fails.append(f"{aid}: listed twice")
        seen.add(aid)
        ln = by_id.get(aid)
        if ln is None:
            fails.append(f"{aid}: not an in-scope intro row in the registry")
            continue
        if e.get("path") != ln["path"]:
            fails.append(f"{aid}: path {e.get('path')} breaks the contract ({ln['path']})")
        if e.get("text_sha256") != ln["text_sha256"]:
            fails.append(f"{aid}: intro text changed since it was voiced")
        if e.get("voice") != ln["voice"]:
            fails.append(f"{aid}: voice {e.get('voice')} is not the registry's {ln['voice']}")
        p = os.path.join(ROOT, e.get("path") or "")
        if not os.path.isfile(p):
            fails.append(f"{aid}: {e.get('path')} missing")
            continue
        secs = mp4_seconds(p)
        if secs is None or abs(secs - float(e.get("seconds", -1))) > DURATION_TOLERANCE:
            fails.append(f"{aid}: duration {secs} vs manifest {e.get('seconds')}")
        if not SYNTHETIC.search(ln["text"]):
            fails.append(f"{aid}: intro does not say the voice is synthetic")
    listed = {e.get("path") for e in entries}
    if os.path.isdir(OUT):
        for dp, _, fs in os.walk(OUT):
            for fn in fs:
                rel = os.path.relpath(os.path.join(dp, fn), ROOT).replace(os.sep, "/")
                if fn.endswith(".mp4") and not fn.endswith(".part.mp4") and rel not in listed:  # .part.mp4: encode in progress
                    fails.append(f"{rel}: audio on disk but not in the manifest")
    for f in fails[:25]:
        print(f"  FAIL {f}")
    n_ok = len([e for e in entries if e.get("avatarId") in by_id])
    print(f"voices current: {n_ok} of {len(lines)} intro lines voiced, {len(fails)} failing")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(check() if "--check" in sys.argv else run())
