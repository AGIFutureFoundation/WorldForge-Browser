# RMCOBJECT mapping: WorldForge mount plan to Sneeze native node (Gate 1.3)

**Status:** The field mapping below was checked against the real headers. The decoder compiles with `clang++ -std=c++17 -fsyntax-only` against them, and it has been run over all 41 plans (2,042 nodes) without linking the engine. **Nothing has been mounted or rendered.** Sneeze has not been built, the decoder has not been linked against Map, RMAP or Sneeze, and the mount sequence (`MountPlanApply`) has never run. Gates 1.2n (native load) and 1.4 (rendered frame) are still open.

Every citation is `repo/path:line` at the commits in section 0. `Sneeze/` paths are in MetaversalCorp/Sneeze, `Map/` paths in MetaversalCorp/Map, and `RMAP/` paths in MetaversalCorp/RMAP. `build.mjs` is `worldforge/build.mjs` in this tree.

## 0. What was read, at which commit

| Repository | Commit (HEAD of `--depth 1` clone, 2026-10-12) | Date / subject |
|---|---|---|
| https://github.com/MetaversalCorp/Sneeze | `0008d08bc46546a29a93b447f3b173202358b69a` | 2026-10-06 "Fix Panel initialization" |
| https://github.com/MetaversalCorp/Map | `0e6d26ac34f4627baf86c333062a3981a6c40742` | 2026-09-01 "Clearing Factory Lists" |
| https://github.com/MetaversalCorp/RMAP | `0fd7efba6febda9dc97a9f629732a380ef7f2dc7` | 2026-09-15 "3 sec fix" |
| nlohmann/json single header, release v3.11.3 | sha256 `9bea4c8066ef4a1c206b2be5a36302f8926f7fdc6087af5d20b417d0cf103ea6` | Sneeze pins v3.11.3 (`Sneeze/deps/dependencies.json:11`) |

**Why three repositories.** Sneeze's own tree does not contain `Map_Object.h`. `Sneeze/src/context/scene/Scene.md:614` lists it, but the header lives in MetaversalCorp/Map. Sneeze includes it as `<Map/Map_Object.h>` (`Sneeze/include/Sneeze.h:39`) and fetches Map and RMAP as dependencies. Both track `main` with no pin (`Sneeze/deps/dependencies.json:20-21`), so the Map and RMAP commits above are simply the tips on the day this was read. All three clones went into `$TMPDIR` and none went into this repository.

**Files read:** `Sneeze/src/context/scene/{Scene.md, RmcObject.h, RmcObject.cpp, Node.cpp, Fabric.cpp, Scene.cpp, MapSvc.h}`, `Sneeze/src/context/Container.cpp`, `Sneeze/include/{Sneeze.h, Scene.h, Container.h}`, `Sneeze/src/sneeze/{Pch.h, Types.h, control/Compositor.cpp}`, `Sneeze/src/context/viewport/GltfMesh.cpp`, `Sneeze/src/deps/wasm/HostFunctions.cpp`, `Sneeze/deps/{dependencies.json, map.cmake, rmap.cmake}`, `Map/include/Map/{Map_Object.h, Map.h}`, `Map/src/{Map_Object.cpp, pch.h, Source_SB_Object.h}`, `RMAP/RMAP/include/RMAP/Mem.h`, `RMAP/RMAP/src/Utils.cpp`.

## 1. What "RMCOBJECT" is at this commit

The name refers to three different things. The decoder targets the first.

1. **The flat wire form of a SOM node.** Sneeze's comments call it an "RMCOBJECT" (`Sneeze/src/context/scene/RmcObject.h:18-21`). In code it is not a struct. It is the triple `(uint16_t wClass, uint64_t twObjectIx, RMAP::MAP::MAP_OBJECT_POD)`:
   * `SNEEZE::MOCelestial_FromJson` produces it (`Sneeze/src/context/scene/RmcObject.h:44`).
   * `RMAP::MAP::MAP_OBJECT::Create(wClass, twObjectIx, Pod)` consumes it (`Map/include/Map/Map_Object.h:171`).
   * `CONTAINER::Node_Root` and `CONTAINER::Node_Open` take the resulting `RMAP::MAP::MAP_OBJECT*` (`Sneeze/include/Container.h:77-78`).
   * Branch injection runs exactly this sequence (`Sneeze/src/context/Container.cpp:417-426`).
2. **The WASM ABI payload** `MAP_OBJECT_PODX { OBJECT_HEADX Object_Head; MAP_OBJECT_POD Map_Object_Pod; }` (`Sneeze/src/deps/wasm/HostFunctions.cpp:30-43`). It is a file-local typedef inside a `.cpp`, so it cannot be included. The NODE_ROOT and NODE_OPEN host calls unpack it into the same triple (`HostFunctions.cpp:839-888`).
3. **`RMAP::MAP::RMCOBJECT`** (`Map/include/Map/Map.h:95-128`) is the map-service model class for celestial objects: `MODEL_OBJECT` plus `MAP_OBJECT_CELESTIAL`. Its constructor takes an RMAP `IREFERENCE*` and a `MEM::SOURCE*` (`Map.h:122`). A JSON spec cannot construct it, and no node operation takes it. **The decoder does not return this type.** Returning it would mean building a map-service model, not a scene node.

So `RmcObjectDecoder(const nlohmann::json& spec)` returns `WORLDFORGE::NATIVE::RMCOBJECT_DECODED`, which holds the real `wClass`, `twObjectIx` and `RMAP::MAP::MAP_OBJECT_POD`, plus the provenance that has no native slot (`worldforge/native/rmcobject_decoder.hpp`).

## 2. Native layout (verified)

`RMAP::MAP::MAP_OBJECT_POD` (`Map/include/Map/Map_Object.h:124-134`) is 504 bytes with no padding. The offsets were measured by compiling against the header, and they are pinned by `static_assert`s in `rmcobject_decoder.cpp`, so a layout change upstream breaks `check_decoder.sh`.

| Sub-struct | Offset | Size | Fields | Header line |
|---|---:|---:|---|---|
| `Name` (`MAP_OBJECT_NAME`) | 0 | 96 | `uint16_t wsName[48]` (UTF-16 units) | `Map_Object.h:26-29` (field `:28`) |
| `Type` (`MAP_OBJECT_TYPE`) | 96 | 8 | `uint8_t bType, bSubtype, bFiction, abReserved[5]` | `Map_Object.h:31-37` |
| `Owner` (`MAP_OBJECT_OWNER`) | 104 | 8 | `uint64_t twOwner` | `Map_Object.h:39-42` |
| `Resource` (`MAP_OBJECT_RESOURCE`) | 112 | 200 | `uint64_t qwResource` (+0), `char sName[64]` (+8), `char sReference[128]` (+72) | `Map_Object.h:44-49` |
| `Transform` (`MAP_OBJECT_TRANSFORM`) | 312 | 80 | `double d3Position[3]`, `double d4Rotation[4]`, `double d3Scale[3]` | `Map_Object.h:51-56` |
| `Orbit` (union) | 392 | 32 | `.Celestial {tmPeriod, tmOrigin, dA, dB}`, used only by celestial nodes | `Map_Object.h:58-73` |
| `Bound` (`MAP_OBJECT_BOUND`) | 424 | 48 | `uint8_t abReserved[24]`, `double d3Max[3]` (at 448) | `Map_Object.h:75-79` |
| `Properties` (union) | 472 | 32 | `.Celestial` / `.Light` / `.Terrestial` (spelled that way upstream) | `Map_Object.h:81-122` |

Class discriminator: `enum MAP_OBJECT_CLASS : uint16_t` with ROOT 70, CELESTIAL 71, TERRESTRIAL 72, PHYSICAL 73, PANEL 74, LIGHT 75 (`Map_Object.h:16-24`). The object stores it as `m_wClass` and the index as `m_twObjectIx`, next to `m_POD` (`Map_Object.h:204-207`).

Index constants: `SNEEZE::OBJECTIX_IDENTITY = 0x0000FFFFFFFFFFFF` means "assign me the next free index", and `OBJECTIX_ERROR = 0x0000FFFFFFFFFFFE` (`Sneeze/include/Scene.h:40-46`). A composed handle is `(wClass << 48) | index` (`RMAP/RMAP/include/RMAP/Mem.h:12, 23-29`).

## 3. Field-by-field mapping

Plan schema `worldforge-sneeze-mount-plan/0.1`. The "Decoder" column says what `rmcobject_decoder.cpp` does.

| Plan field | Native target | Decoder | Citation |
|---|---|---|---|
| `nativeClass` | `wClass` (out-param, then `MAP_OBJECT::m_wClass`) | Looks the string up in a table that accepts both the derived-type spelling (`MAP_OBJECT_TERRESTRIAL`) and the enum spelling (`MAP_OBJECT_CLASS_TERRESTRIAL`). An unknown string is an error, because `Create` returns `nullptr` for unknown classes. | `Map_Object.h:16-24`; `Map/src/Map_Object.cpp:98-113`; `Sneeze/src/context/scene/Scene.md:364-371` |
| *(none)* | `twObjectIx` | Always `SNEEZE::OBJECTIX_IDENTITY`. The container allocates the next index. Explicit indices are de-duplicated per container: a repeat gets `OBJECTIX_ERROR`. | `Sneeze/src/context/Container.cpp:316-349`; `Scene.h:45` |
| `cardId` | **no slot** | Kept in `RMCOBJECT_DECODED::sCardId`. The mounting code has to keep the map from cardId to handle. | `Map_Object.h:124-134` has no id field |
| `parentCardId` | **no slot in the POD**; it becomes the `qwComposed_Parent` argument of `Node_Open`, or nesting in `aChildren` on the JSON route | `null` marks the root, which must be the first node. Otherwise the parent must appear earlier. | `Container.h:78`; `Container.cpp:297-312` (parent resolved with `Node_Find`); `Container.cpp:54, 455-489` (`aChildren`) |
| `displayName` | `Pod.Name.wsName[48]`, UTF-16 | Decodes UTF-8 to UTF-16. Non-BMP code points and invalid bytes become U+FFFD. Clamps to **47 units** and always leaves a NUL. Warns when it clamps. | `Map_Object.h:28`; `Sneeze/src/context/scene/Node.cpp:703-735` (reads BMP UTF-16 back, stops at NUL or 48); the 47+NUL convention kept by every clamping writer (see M1): `Map/src/Map_Object.cpp:142` via `RMAP/RMAP/src/Utils.cpp:192-202`, `Sneeze/src/deps/wasm/HostFunctions.cpp:1009-1013`, `Scene.md:299-304` |
| `transform.translation [x,y,z]` | `Pod.Transform.d3Position[3]` (metres) | Y-up to Z-up: `(x, -z, y)` | `Map_Object.h:53`; `Map/src/Map_Object.cpp:177-183`; frame: `Sneeze/src/context/viewport/GltfMesh.cpp:1827-1830` |
| `transform.rotation [x,y,z,w]` | `Pod.Transform.d4Rotation[4]`, order x,y,z,w (identity has `[3] = 1`) | Conjugates by Rx(+90°), which gives `(qx, -qz, qy, qw)`. The quaternion must be finite and non-zero. A non-unit quaternion is renormalised and warned about, because the engine does not normalise. | `Map_Object.h:54, 159-165`; `Map/src/Map_Object.cpp:185-192`; `Sneeze/src/context/scene/RmcObject.cpp:112`; `Sneeze/src/sneeze/control/Compositor.cpp:231-249` |
| `transform.scale [x,y,z]` | `Pod.Transform.d3Scale[3]` | `(sx, sz, sy)`. A zero axis is an error. | `Map_Object.h:55`; `Map/src/Map_Object.cpp:194-199`; `RmcObject.h:25-28` |
| `resource.sReference` | `Pod.Resource.sReference[128]` | At most **127 bytes** plus a NUL. A longer value is an error, not a silent truncation, because a cut URL would not resolve. Empty is an error. A value starting with `action:` is an error, because it is never fetched. | `Map_Object.h:48`; `RmcObject.cpp:126-134, 190`; `Sneeze/src/context/scene/Node.cpp:155-167, 201-209`; absolute URLs pass `FABRIC::Resolve` unchanged (`Sneeze/src/context/scene/Fabric.cpp:73-103`) |
| `resource: null` | `sReference[0] == 0` | No fetch | `Node.cpp:155` |
| *(none)* `resource.sName` | `Pod.Resource.sName[64]` | Accepted if present (at most 63 bytes). The plan never sets it. | `Map_Object.h:47`; `RmcObject.cpp:189` |
| *(none)* | `Pod.Resource.qwResource` | 0 | `Map_Object.h:46` |
| `extras {kind, source, zoneCardId, shape, ...}` | **no slot** | Kept in `RMCOBJECT_DECODED::jExtras` | `Map_Object.h:124-134` |
| *(none)* | `Pod.Type {bType, bSubtype, bFiction}` | All 0. **`bSubtype` must never be 255**: that marks an MSF attachment point, and the node's `sReference` is then spawned as a child fabric instead of being fetched as a model. | `Map_Object.h:31-37`; `Node.cpp:155-167`; `Scene.md:211-221, 322-326` |
| *(none)* | `Pod.Owner.twOwner` | 0 | `Map_Object.h:41`; `RmcObject.cpp:183` |
| *(none; `volum` is in cards.json)* | `Pod.Bound.d3Max[3]`: full extent in metres | Zero, because the plan carries no volume. If a spec adds `volum.halfExtents`, the decoder writes `2 × halfExtents`, permuted to Z-up. | `Map_Object.h:75-79`; `Compositor.cpp:647-653, 734-742` (extent = ½·‖d3Max‖; box half-size = ½·d3Max) |
| *(none)* | `Pod.Orbit`, `Pod.Properties` | 0. Orbit is celestial-only. TERRESTRIAL and PHYSICAL nodes read no Properties member in Sneeze (no `bLockToGround`/`bAvatar` reads under `Sneeze/src`). | `Map_Object.h:66-73, 114-122` |

**Plan-level fields**

| Plan field | Native meaning | Notes |
|---|---|---|
| `rootCardId` | The first node, created with `Node_Root` (or `Node_Open` under an existing node; see §5) | `Container.cpp:280-295` (one root per fabric, `:290`) |
| `mountParent` = `"SCENE::Fabric_Root()->Node_Root()"` | The structural root fabric's ROOT node in the synthetic root container | See mismatch M7 |
| `coordinateFrame.up = "Y"` | Sneeze's world is right-handed **Z-up** | The decoder converts (M4) |
| `resourceCachePolicy = shared-by-exact-sReference-URL` | Matches the engine: models with the same resolved URL share one refcounted `GLTF_RENDER_MODEL` | `Scene.md:232-235` |
| `assets[]`, `previewGlb` | No native field | Used only for hashing and preview |
| `acceptanceRequirements` | See M12 | |

## 4. Class discriminators

| Plan `nativeClass` | Enum constant (`Map_Object.h`) | Value | Object built by `MAP_OBJECT::Create` (`Map/src/Map_Object.cpp:98-113`) | JSON-route `Head.Self` (`RmcObject.cpp:67-90`) | Plan nodes |
|---|---|---:|---|---|---:|
| `MAP_OBJECT_TERRESTRIAL` | `MAP_OBJECT_CLASS_TERRESTRIAL` (`:20`) | 72 | `MAP_OBJECT_TERRESTRIAL` (`Map_Object.h:275`) | `"T-?"` | 939 |
| `MAP_OBJECT_PHYSICAL` | `MAP_OBJECT_CLASS_PHYSICAL` (`:21`) | 73 | base `MAP_OBJECT` (there is no `MAP_OBJECT_PHYSICAL` class) | `"P-?"` | 1,103 |
| (unused) ROOT / CELESTIAL / PANEL / LIGHT | `:18`, `:19`, `:22`, `:23` | 70 / 71 / 74 / 75 | base / `MAP_OBJECT_CELESTIAL` / base / `MAP_OBJECT_LIGHT` | `R` / `C` / no letter (composed integer, as `Sneeze/src/context/scene/Scene.cpp:478` does) / `L` | 0 |

Any value outside 70-75 makes `Create` return `nullptr` (`Map/src/Map_Object.cpp:98-113`). What happens next depends on the node:

* **The root** (route A, or the first node of a route-B branch): `Node_Root` and `Node_Open` check `if (pMap_Object)` (`Container.cpp:286, 303`), so the node is simply not created (`Container.cpp:424-449`).
* **A child on the MSF "Data" route** (route B): `Branch_Add_Aux` passes the `nullptr` straight to `Node_Create` (`Container.cpp:470-472`), which dereferences it at `Container.cpp:316`. A bad class on a child node therefore crashes Sneeze rather than being skipped (U9). On that route a class outside 70-75 comes from a `Head.Self` that is missing, has no `-`, or is a raw composed integer with a bad class (`RmcObject.cpp:79-86, 107, 154-166`); an unknown letter falls back to PHYSICAL (`RmcObject.cpp:86`).

This does not affect our 41 plans: every node is class 72 or 73, the decoder rejects any other class, and `RmcObjectNodeJson` always writes a `"T-?"`/`"P-?"` `Head.Self`.

## 5. Mount routes

**A. Native: `CONTAINER::Node_Root` / `Node_Open`.** This is the route the plan names (`build.mjs:14`), and the decoder's default target.

* For each node in plan order: `RmcObjectDecoder(spec)`, then `MAP_OBJECT::Create(wClass, twObjectIx, Pod)`.
* The root goes to `Node_Root(twFabricIx, obj)`, or to `Node_Open(qwParent, obj)` under an existing node.
* Every other node goes to `Node_Open(handle[parentCardId], obj)`.
* Both calls return the **composed** handle (`Container.cpp:342`). That handle feeds the children's `Node_Open` and resolves with `Node_Find` (`Container.cpp:387-396`).
* On `OBJECTIX_ERROR`, the caller deletes the object, as `Branch_Add` does (`Container.cpp:449, 484`).

This sequence is written as `MountPlanApply` (compiled only with `-DWORLDFORGE_LINK_SNEEZE`, syntax-checked, **never executed**).

**B. MSF "Data": NODE_MAP_DATA, then `CONTAINER::Branch_Add`, then `MOCelestial_FromJson`.**

* A fabric's WASM module asks the host to build its branch from the MSF payload's `"Data"` tree (`HostFunctions.cpp:726-742, 809-834`).
* `Branch_Add` runs each JSON node through `MOCelestial_FromJson`, recurses through `"aChildren"`, and calls `Scene_Invalidate` at the end (`Container.cpp:409-489`).
* `MountPlanToBranch` / `RmcObjectNodeJson` emit that JSON using the keys in `RmcObject.cpp:23-58`, with transforms already in Z-up.
* This route has stricter name limits at this commit (see U1/U2), so `RmcObjectNodeJson` writes each non-ASCII code point as `?` and warns.
* `Head.Self` uses the `"T-?"` letter form, because every composed integer for these classes exceeds 2^53 and JavaScript-generated JSON would round it.

**C. Map service (MAPSVC, "Mode B").** This route does not apply: it needs a running map server, and Sneeze then streams nodes on proximity (`Scene.md:453-497`). Its wire schema has its own limits: an object id of `STRING_W(48)`, a resource `sName` of `STRING(32)` and a `sReference` of `STRING(64)` (`Map/src/pch.h:42-48`, `Map/src/Source_SB_Object.h:86-91, 109-141`). The 35-byte plan URL fits.

## 6. Mismatches between our plan and Sneeze

| # | Mismatch | Evidence | Effect on our 41 plans | What was done |
|---|---|---|---|---|
| M1 | **Name length limit is 47 UTF-16 units, not 48.** `build.mjs:37` sets `NAME_LIMIT = 48` with the comment "Artemis 0.4.0 aborts on longer node names", which is a different engine. The field is `wsName[48]`. Sneeze's only name reader, `NODE::Name`, is bounded at 48 and would read a 48-unit name with no NUL correctly, so 47 is not a crash or garbling limit. It is the limit every engine writer that clamps keeps: `MAP_OBJECT::Name` (through RMAP `WString_to_Uint16`) and the ABI `NODE.Name` mutator both write at most 47 units plus a NUL, and `Scene.md` documents the same contract. A 48-unit name therefore cannot round-trip through the engine. (The route-B JSON copy does not clamp at 48 at all; see M2 and U1.) | `Map_Object.h:28`; reader: `Node.cpp:715-717`; writers: `Map/src/Map_Object.cpp:142` via `RMAP/RMAP/src/Utils.cpp:194, 201`, and `HostFunctions.cpp:1009-1013`; contract: `Scene.md:299-304`. A grep finds no other `wsName` reader in `Sneeze/src`, `Sneeze/include`, `Map/src` or `Map/include`. | **267 of 2,042 nodes** have 48-unit names. They come from two places in `build.mjs` (split derived from the plans in `conformance-report.json` `totals.native.nameUnitsByOrigin`): <ul><li>**67 umbrella-suffix names**, all TERRESTRIAL cards (30 coordinator, 26 plaza, 7 world, 2 zone, 2 agent). `nodeName()` budgets `"<label> · Powered by AGI Corp"` to exactly 48 units (`build.mjs:94`). Clamping drops the last letter of the suffix, which becomes `· Powered by AGI Cor`.</li><li>**200 PHYSICAL primitive names**, from `displayName: primitiveId.slice(-48)` (`build.mjs:388`). Clamping drops the last character of the path, so `gentic-payments/service-provisioning-counter/pad` ends in `/pa` and `agent:s35-parkinsons-dao/progress-tracker/avatar` ends in `/avata`.</li></ul> | The decoder clamps to 47 and warns. The conformance script counts these as the only native-route violations and reports the split by origin. **Fix belongs in `build.mjs` (not this builder's file):** a separate 47-unit limit for plan `displayName`s (`build.mjs:37`), used by `nodeName()` (`:94`) and by the PHYSICAL names at `build.mjs:388`, which should use `slice(-47)` so the end of the path survives. |
| M2 | **Name encoding.** The POD is UTF-16 (BMP). The plan is UTF-8 with `·` (U+00B7) and `…` (U+2026). That is fine on route A. On route B, Sneeze's JSON decoder copies UTF-8 *bytes* one per unit, so non-ASCII names come out garbled. It writes up to 95 units, so a name of exactly 48 bytes fills `wsName[48]` with no NUL, and a longer one overruns into `Type` (U1). | `Node.cpp:713-735`; `RmcObject.cpp:136-145, 172` | Route A: 0 problems beyond M1. Route B: 939 non-ASCII names and 323 names over 47 bytes (248 are exactly 48 bytes and fill the field with no NUL; 75 are longer and overrun into `Type`, U1), **1,529 violations on 1,139 nodes**. Split in `conformance-report.json` `totals.json.nameBytesSplit`. | Route A encodes UTF-16 correctly. Route B folds to ASCII with `?` and clamps to 47 bytes. |
| M3 | **Class names.** The plan uses derived-type spellings. The discriminators are spelled `MAP_OBJECT_CLASS_*`. `MAP_OBJECT_PHYSICAL` is not a C++ class in Map: class 73 builds a base `MAP_OBJECT`. | `Map_Object.h:16-24, 144, 221, 275, 308`; `Map_Object.cpp:107` | No functional problem: both values (72, 73) are valid. | The decoder accepts both spellings. |
| M4 | **Coordinate frame and transform representation.** The plan is Y-up. Sneeze is right-handed **Z-up**: glTF models are converted with Rx(+90) on import, and the orbit camera's "up" is +Z. The engine composes T·R·S from doubles with an x,y,z,w quaternion and **does not normalise it**. | `GltfMesh.cpp:1827-1830`; `Compositor.cpp:231-249, 606-627, 1125-1126` | Sent unconverted, every world would be mounted lying on its side. All 2,042 rotations are identity and unit length. | The decoder conjugates each node by Rx(+90): position `(x,-z,y)`, rotation `(qx,-qz,qy,qw)`, scale `(sx,sz,sy)`. That keeps a Y-up glTF resource and its node aligned after Sneeze's own import conversion. |
| M5 | **Resource field size.** `sReference[128]` holds 127 bytes plus a NUL. The map-service route caps it at 64. | `Map_Object.h:48`; `RmcObject.cpp:131`; `Map/src/pch.h:48` | `build.mjs:436` already checks `< 128` bytes, which is consistent. Every plan URL is 35 bytes. | The conformance script enforces at most 127 bytes and reports the 64-byte map-service cap as an advisory (0 nodes affected). |
| M6 | **No identity or provenance slot.** cardId, parentCardId and extras cannot travel in the POD. Native identity is a per-container OBJECTIX allocated at mount time. | `Map_Object.h:124-134`; `Container.cpp:316-349`; `Scene.md:29-33, 144-152` | All 2,042 nodes | Kept beside the POD in `RMCOBJECT_DECODED`. `MountPlanApply` keeps the map from cardId to handle. |
| M7 | **`mountParent` names the scene's structural root fabric.** `Node_Root` refuses a fabric that already has a root, so the plan root would have to be `Node_Open`-ed under the root container's ROOT node, the way `Scene.cpp:205-221` adds the primary attach node. That puts the world outside any MSF/WASM container: access checks are bypassed, and the world belongs to the structural root fabric, which has no MSF/WASM owner (`Node_Open` hands the new node `pNode_Parent->Fabric()`). The parent handle must also be composed explicitly, because `NODE::ObjectIx()` returns the *raw* index. | `Container.cpp:290, 305-308`; `Scene.md:12-21, 440-451, 593-603`; `Node.cpp:701`; `Compositor.cpp:706-708` | All 41 plans | `MOUNT_TARGET` supports both: `bFabricRoot` (a fabric the caller owns, which is what a world should be) and `qwComposed_Parent`. Which one to use is a design decision, not a decoder question. |
| M8 | **No bound.** Sneeze reads `Bound.d3Max` for each node's size, which feeds scene framing and the LOD ratio. Nodes injected by WASM or a static MSF are never proximity-unloaded, so a zero bound does not hide them. It only stops them from contributing their own size to framing. | `Compositor.cpp:647-653, 671-692, 713-718` | All 2,042 nodes | `Bound` stays zero, and the decoder warns. The decoder will take `volum` from cards.json if the plan ever carries it. |
| M9 | **Card kinds have no native type.** world, plaza, zone and the other kinds are not Sneeze types. `MAP_OBJECT_TERRESTRIAL::eTYPE` (ROOT, WATER, …, CITY, COMMUNITY, SECTOR, PARCEL) exists, but choosing one per kind would be invented. | `Map_Object.h:278-292` | All nodes | `Type` is left 0. Kind stays in `extras`. |
| M10 | **Large integer ids in JSON.** `OBJECTIX_COMPOSE(72, IDENTITY)` is about 2.05×10^16, above 2^53. | `RMAP/RMAP/include/RMAP/Mem.h:12` | Route B only | The JSON route uses the `"<letter>-?"` string form (`RmcObject.cpp:67-90`). |
| M11 | **`bindingStatus` is stale.** The plans say `plan-only-native-RMCOBJECT-encoding-not-generated`. A decoder now exists, but nothing is mounted. | `worldforge/out/*/sneeze-mount-plan.json` | All 41 | Not changed: those files are `build.mjs` output, which this builder does not own. |
| M12 | **Acceptance requirements against the API.** <ul><li>"Parents first": satisfied, 0 violations.</li><li>"Handle resolves via `Node_Find`": consistent, because `Node_Root`/`Node_Open` return composed handles and `Node_Find` takes composed handles.</li><li>"`Gltf_Render_Model()` != nullptr": the accessor exists (`Sneeze/include/Scene.h:88`), but it can only be observed in a running engine.</li><li>"Safe lifecycle/thread boundary": Sneeze itself documents that **there is no read guard yet**. Mutating while the compositor traverses is unsafe, and a mounter outside the engine cannot satisfy this today. The in-engine `Branch_Add` path is the closest thing.</li></ul> | `Container.cpp:342, 387-396`; `Scene.md:563-591` | — | Recorded here. Not testable without a built engine. |

## 7. Upstream defects and doc drift seen while reading

The clones are read-only, so none of these was patched.

* **U1. Name overflow in the JSON decoder.** `RmcObject.cpp:172` passes `sizeof(wsName)`, which is 96 bytes, as the *unit* limit. The helper then writes up to 95 `uint16_t` into a 48-unit array (`RmcObject.cpp:136-145`). Name bytes from the 49th on land in `Type` (offset 96), then `Owner`, and so on.
  * Where `char` is signed (x86-64, Apple arm64; this is a compiler ABI fact, not from these repositories), a non-ASCII byte in position 49 becomes `0xFFxx`. That writes `Type.bSubtype = 255`, which turns the node into an attachment point that spawns its `sReference` as a fabric (`Node.cpp:157-164`).
  * `Type` is re-read only when the JSON has a `"Type"` key (`RmcObject.cpp:175-181`). That is why `RmcObjectNodeJson` always writes `"Type"`, and why it clamps names to 47 ASCII bytes.
* **U2. Byte-per-unit name copies.** Both `RmcObject.cpp:141-143` and the `NODE.Name` ABI mutator (`HostFunctions.cpp:1012`) treat each UTF-8 byte as one UTF-16 unit.
* **U3. `SNEEZE::Name_Set` is documented but missing.** `Scene.md:299-304` and `Sneeze/.cursor/rules/project.mdc:660` describe a shared UTF-8 decoder with this name. No definition exists anywhere in the Sneeze source tree at `0008d08`.
* **U4. `NODE::ObjectIx()` is not composed.** `Scene.md:262` says it returns a composed handle. `Node.cpp:701` returns the raw `m_twObjectIx`, and `Compositor.cpp:706-708` composes it explicitly.
* **U5. Scene.md describes the old `MAP_OBJECT` API.** `Scene.md:293-297, 307, 373` describe an `OBJECT_HEAD` constructor, `m_Head` and `Class()`. Map at `0e6d26a` has `MAP_OBJECT(uint16_t wClass, uint64_t twObjectIx, const MAP_OBJECT_POD&)` with `m_POD`/`m_wClass`/`m_twObjectIx` (`Map_Object.h:168, 204-207`). `Sneeze/deps/dependencies.json:21` records that migration.
* **U6. Types missing from Map.** `Scene.md:366-371` lists `MAP_OBJECT_ROOT`, `MAP_OBJECT_PHYSICAL` and `MAP_OBJECT_PANEL` as types. They do not exist in Map, and `Create` builds a base `MAP_OBJECT` for those classes.
* **U7. Spelling.** `MAP_OBJECT_PROPERTIES_TERRESTIAL` and its union member `Terrestial` (`Map_Object.h:91, 120`) are spelled that way and must be used verbatim.
* **U8. Unpinned dependencies.** Map and RMAP track `main` (`dependencies.json:20-21`). Re-run `check_decoder.sh` on every bump. It fails on commit drift on purpose.
* **U9. Null dereference for a bad class on a JSON-route child.** `Branch_Add_Aux` calls `MAP_OBJECT::Create` and passes the result straight to `Node_Create` with no null check (`Container.cpp:470-472`). `Node_Create` begins `uint64_t twObjectIx = pMap_Object->m_twObjectIx;` (`Container.cpp:316`). So a child node whose class is outside 70-75 (`Create` returns `nullptr`, `Map/src/Map_Object.cpp:98-113`) crashes Sneeze. `Node_Root` and `Node_Open` both check `if (pMap_Object)` first (`Container.cpp:286, 303`), so the root and route A are safe. Our 41 plans do not hit this (every class is 72 or 73, see section 4).

## 8. Files, commands and results (2026-10-12)

| File | Role |
|---|---|
| `worldforge/native/rmcobject_decoder.hpp/.cpp` | `RmcObjectDecoder(spec)` returns the real `wClass` / `twObjectIx` / `RMAP::MAP::MAP_OBJECT_POD`. Also `MountPlanDecode`, `RmcObjectNodeJson`, `MountPlanToBranch`, and, under `WORLDFORGE_LINK_SNEEZE`, `RmcObjectCreate` / `MountPlanApply` / `RmcObjectCrossCheck`. |
| `worldforge/native/decoder_smoke.cpp` | Runs the decoder over all plans and checks invariants. `--dump-branch <slug>` prints the route-B branch. |
| `worldforge/native/check_decoder.sh` | Two syntax-only configurations plus a smoke build and run in `$TMPDIR`. Fails on a missing dependency or commit drift. |
| `worldforge/native/mount_plan_conformance.mjs` | Static check with the constants above baked in (no clone needed). Writes `conformance-report.json`. Has `--check` and `--route=json`, and a self-test of 13 broken variants. |
| `worldforge/native/conformance-report.json` | Deterministic report written by the script above. `totals.native.nameUnitsByOrigin` splits the M1 names by where `build.mjs` made them; `totals.json.nameBytesSplit` splits the M2 over-47-byte names into exactly-48 and longer. |

```
$ bash worldforge/native/check_decoder.sh
syntax-only (default): ok
syntax-only (WORLDFORGE_LINK_SNEEZE): ok
check_decoder: OK - clang++ -std=c++17 -fsyntax-only compiled rmcobject_decoder.cpp in 2/2 configs (default, WORLDFORGE_LINK_SNEEZE) against Sneeze 0008d08 / Map 0e6d26a / RMAP 0fd7efb / nlohmann-json 3.11.3; PASS 41 plans, 2042 nodes, 0 decode errors, 0 plan errors, 0 invariant failures, 1103 resource nodes, 267 names clamped to 47 UTF-16 units, 939 json-route names ASCII-folded, pod fnv1a64 f690b629ca9b1b4a, branch fnv1a64 f3730da9ad120678

$ node worldforge/native/mount_plan_conformance.mjs
  native name-utf16-units: 267
    name-utf16-units from umbrellaSuffix: 67
    name-utf16-units from primitiveIdTail: 200
  ...
  selftest: 13/13 broken variants caught by exactly their own rule
sneeze conformance: 41 plans, 2042 nodes, 267 violations          (native route; all 267 are name-utf16-units, see M1)
$ node worldforge/native/mount_plan_conformance.mjs --route=json
  ...
    json-name-bytes exactly48NoNul: 248
    json-name-bytes over48IntoType: 75
  ...
sneeze conformance: 41 plans, 2042 nodes, 1529 violations
$ node worldforge/native/mount_plan_conformance.mjs --check        (exit 1 until M1 is fixed in build.mjs)
```

Both programs pass with `-Wall -Wextra -Wpedantic -Werror`. The Sneeze, Map, RMAP and JSON headers are included with `-isystem`, so their own warnings are not counted.

## 9. Not done

* **No mount and no render.** No Sneeze host was built. Per `Sneeze/README.md:9, 148`, the dependency phase alone takes 1-2 hours and needs Rust, Go, CMake, Python and a C++17 toolchain. That was not attempted in this sprint.
* **Nothing linked against the engine.** The decoder has not been linked against Map, RMAP or Sneeze. `RmcObjectCreate`, `MountPlanApply` and `RmcObjectCrossCheck` are syntax-checked only. The smoke run links just the decoder.
* **Plans unchanged.** The plans still have 267 names of 48 units (M1: 67 umbrella-suffix names, 200 PHYSICAL primitive names) and the stale `bindingStatus` (M11). The fixes belong in `build.mjs`.
* **Gate status.** 1.2n (native fastgltf load) is still open. 1.3 has a decoder written against the real headers but no mount attempted. 1.4 is still open.
