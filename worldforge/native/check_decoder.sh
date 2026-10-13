#!/usr/bin/env bash
# worldforge/native/check_decoder.sh
#
# Compiles worldforge/native/rmcobject_decoder.cpp with `clang++ -std=c++17 -fsyntax-only` against the
# cloned Sneeze / Map / RMAP headers, in two configurations:
#   1. default                  (decoder + MSF "Data" route)
#   2. -DWORLDFORGE_LINK_SNEEZE (adds MAP_OBJECT::Create, CONTAINER::Node_Root/Node_Open/Node_Find and
#                                SNEEZE::MOCelestial_FromJson call sites; syntax only, never linked)
# Then, unless SKIP_SMOKE=1, it builds decoder_smoke.cpp into $TMPDIR (never into the repo) and runs it
# over all plans. The smoke binary links only the decoder, not Sneeze/Map/RMAP.
#
# Clones are expected in $TMPDIR (override with SNEEZE_DIR / MAP_DIR / RMAP_DIR / NLOHMANN_INC):
#   git clone --depth 1 https://github.com/MetaversalCorp/Sneeze "$TMPDIR/Sneeze"
#   git clone --depth 1 https://github.com/MetaversalCorp/Map    "$TMPDIR/Map"
#   git clone --depth 1 https://github.com/MetaversalCorp/RMAP   "$TMPDIR/RMAP"
#   curl -sSfL --create-dirs -o "$TMPDIR/nlohmann-json-3.11.3/include/nlohmann/json.hpp" \
#        https://github.com/nlohmann/json/releases/download/v3.11.3/json.hpp
#
# Prints one final line: "check_decoder: OK ..." (exit 0), or "check_decoder: FAIL <the exact missing
# dependency or first compiler error>" (exit 1). It also exits 1 if a clone is not at the commit that
# RMCOBJECT_MAPPING.md was verified against, because the line citations would then need re-checking.

set -u

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/../.." && pwd)"
T="${TMPDIR:-/tmp}"
T="${T%/}"

SNEEZE_DIR="${SNEEZE_DIR:-$T/Sneeze}"
MAP_DIR="${MAP_DIR:-$T/Map}"
RMAP_DIR="${RMAP_DIR:-$T/RMAP}"
CXX="${CXX:-clang++}"

VERIFIED_SNEEZE="0008d08bc46546a29a93b447f3b173202358b69a"
VERIFIED_MAP="0e6d26ac34f4627baf86c333062a3981a6c40742"
VERIFIED_RMAP="0fd7efba6febda9dc97a9f629732a380ef7f2dc7"
VERIFIED_JSON_SHA256="9bea4c8066ef4a1c206b2be5a36302f8926f7fdc6087af5d20b417d0cf103ea6"   # json.hpp v3.11.3

fail () { echo "check_decoder: FAIL - $*"; exit 1; }

command -v "$CXX" >/dev/null 2>&1 || fail "missing dependency: $CXX not on PATH"

need () { [ -f "$1" ] || fail "missing dependency: $1 (fix: $2)"; }
need "$SNEEZE_DIR/include/Sneeze.h"                 "git clone --depth 1 https://github.com/MetaversalCorp/Sneeze $SNEEZE_DIR"
need "$SNEEZE_DIR/include/Scene.h"                  "git clone --depth 1 https://github.com/MetaversalCorp/Sneeze $SNEEZE_DIR"
need "$SNEEZE_DIR/include/Container.h"              "git clone --depth 1 https://github.com/MetaversalCorp/Sneeze $SNEEZE_DIR"
need "$SNEEZE_DIR/src/sneeze/Types.h"               "git clone --depth 1 https://github.com/MetaversalCorp/Sneeze $SNEEZE_DIR"
need "$SNEEZE_DIR/src/context/scene/RmcObject.h"    "git clone --depth 1 https://github.com/MetaversalCorp/Sneeze $SNEEZE_DIR"
need "$MAP_DIR/include/Map/Map_Object.h"            "git clone --depth 1 https://github.com/MetaversalCorp/Map $MAP_DIR"
need "$RMAP_DIR/RMAP/include/RMAP/RMAP.h"           "git clone --depth 1 https://github.com/MetaversalCorp/RMAP $RMAP_DIR"
need "$RMAP_DIR/RMAP/include/RMAP/Mem.h"            "git clone --depth 1 https://github.com/MetaversalCorp/RMAP $RMAP_DIR"

JSON_INC=""
for d in "${NLOHMANN_INC:-}" /opt/homebrew/include /usr/local/include /usr/include "$T/nlohmann-json-3.11.3/include"; do
   if [ -n "$d" ] && [ -f "$d/nlohmann/json.hpp" ]; then JSON_INC="$d"; break; fi
done
[ -n "$JSON_INC" ] || fail "missing dependency: nlohmann/json.hpp 3.11.3 (fix: curl -sSfL --create-dirs -o $T/nlohmann-json-3.11.3/include/nlohmann/json.hpp https://github.com/nlohmann/json/releases/download/v3.11.3/json.hpp)"
grep -q "define NLOHMANN_JSON_VERSION_MINOR 11" "$JSON_INC/nlohmann/json.hpp" && grep -q "define NLOHMANN_JSON_VERSION_PATCH 3" "$JSON_INC/nlohmann/json.hpp" \
   || fail "nlohmann/json at $JSON_INC is not 3.11.3, the version Sneeze pins (deps/dependencies.json)"
JSON_SHA="$(shasum -a 256 "$JSON_INC/nlohmann/json.hpp" 2>/dev/null | cut -d' ' -f1)"

rev () { git -C "$1" rev-parse HEAD 2>/dev/null || echo "unknown"; }
REV_SNEEZE="$(rev "$SNEEZE_DIR")"; REV_MAP="$(rev "$MAP_DIR")"; REV_RMAP="$(rev "$RMAP_DIR")"
DRIFT=""
[ "$REV_SNEEZE" = "$VERIFIED_SNEEZE" ] || DRIFT="$DRIFT Sneeze@${REV_SNEEZE:0:7}"
[ "$REV_MAP"    = "$VERIFIED_MAP"    ] || DRIFT="$DRIFT Map@${REV_MAP:0:7}"
[ "$REV_RMAP"   = "$VERIFIED_RMAP"   ] || DRIFT="$DRIFT RMAP@${REV_RMAP:0:7}"
echo "headers: Sneeze ${REV_SNEEZE:0:12}  Map ${REV_MAP:0:12}  RMAP ${REV_RMAP:0:12}  nlohmann/json $JSON_INC (sha256 ${JSON_SHA:0:12}$( [ "$JSON_SHA" = "$VERIFIED_JSON_SHA256" ] && echo ', = v3.11.3 release asset' ))"

INC=(-isystem "$JSON_INC" -isystem "$SNEEZE_DIR/include" -isystem "$SNEEZE_DIR/src" -isystem "$MAP_DIR/include" -isystem "$RMAP_DIR/RMAP/include")
WARN=(-Wall -Wextra -Wpedantic -Werror)
LOG="$(mktemp "$T/check_decoder.XXXXXX")"
trap 'rm -f "$LOG"' EXIT

# Apple's /usr/bin/clang++ shim may print a harmless "couldn't create cache file ... xcrun_db" line when
# the sandbox blocks its cache directory. That line is filtered; everything else counts.
compile () {
   local label="$1"; shift
   "$CXX" -std=c++17 -fsyntax-only "${WARN[@]}" "$@" "${INC[@]}" "$HERE/rmcobject_decoder.cpp" >"$LOG" 2>&1
   local rc=$?
   local first; first="$(grep -v 'xcrun_db' "$LOG" | grep -m1 -E 'error|fatal' || true)"
   if [ $rc -ne 0 ]; then
      grep -v 'xcrun_db' "$LOG" | head -20
      fail "clang++ -std=c++17 -fsyntax-only ($label): ${first:-exit $rc}"
   fi
   echo "syntax-only ($label): ok"
}

compile "default"
compile "WORLDFORGE_LINK_SNEEZE" -DWORLDFORGE_LINK_SNEEZE

SMOKE="smoke skipped (SKIP_SMOKE=1)"
if [ "${SKIP_SMOKE:-0}" != "1" ]; then
   OUT="$T/worldforge-native-smoke"
   mkdir -p "$OUT"
   "$CXX" -std=c++17 -O1 "${WARN[@]}" "${INC[@]}" "$HERE/decoder_smoke.cpp" "$HERE/rmcobject_decoder.cpp" -o "$OUT/decoder_smoke" >"$LOG" 2>&1 \
      || { grep -v 'xcrun_db' "$LOG" | head -20; fail "smoke build: $(grep -v 'xcrun_db' "$LOG" | grep -m1 -E 'error|fatal')"; }
   SMOKE="$("$OUT/decoder_smoke" "$ROOT" 2>"$LOG" | tail -1)"
   grep -v 'xcrun_db' "$LOG" | head -10
   case "$SMOKE" in "decoder smoke: PASS"*) ;; *) fail "${SMOKE:-decoder smoke produced no output}";; esac
fi

if [ -n "$DRIFT" ]; then
   fail "compiled, but the clones are not at the verified commits ($DRIFT ); re-verify RMCOBJECT_MAPPING.md citations"
fi

echo "check_decoder: OK - clang++ -std=c++17 -fsyntax-only compiled rmcobject_decoder.cpp in 2/2 configs (default, WORLDFORGE_LINK_SNEEZE) against Sneeze ${VERIFIED_SNEEZE:0:7} / Map ${VERIFIED_MAP:0:7} / RMAP ${VERIFIED_RMAP:0:7} / nlohmann-json 3.11.3; ${SMOKE#decoder smoke: }"
