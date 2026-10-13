# WorldForge: SmartCiti.X Master Cards for every world

WorldForge takes the 41 coming-soon worlds in `my-fabric/worlds/index.json` through the gates from the
"Create SmartCiti.X Roadmap" ChatGPT thread:

generated core → card-tagged GLB → Sneeze Scene Object Model mount plan → native load → rendered frame

```bash
node worldforge/build.mjs           # writes worldforge/out/, runs every world's evals, exit 1 on any failure
node worldforge/build.mjs --check   # exit 1 if worldforge/out/ is behind its sources
# viewer (with ./deploy/preview-local.sh running): http://localhost:8080/worldforge/viewer.html?world=locator-x
```

## What each world gets (`worldforge/out/<slug>/`)

| File | What it is |
|---|---|
| `cards.json` | SmartCiti.X Master Cards: world → plaza, Alignment Evaluation Gate, Steward Council (3 human seats, all empty), and zones → agent avatars. Each card has an owner (AGI Future Foundation PBC), a **Volum** (the bounded 3-D region it covers) and a permission matrix (`view, enter, build, operate, delegate, transfer, govern`). |
| `blockout.generated.json` | The generated core: zones, primitives and roads in metres. It is deterministic and synthetic, with no imported coordinates or geometry. |
| `<slug>.glb` | glTF 2.0. Every node carries its `cardId`/`parentCardId` in its extras, so a native loader can index cards without relying on display names. The Khronos validator reports 0 errors and 0 warnings on all 42 GLBs. |
| `sneeze-mount-plan.json` | Ordered SOM node specs, parents first, for `CONTAINER::Node_Open`. They share one `unit-cube.glb` resource whose URL fits the 128-byte `Resource.sReference` limit. |
| `manifest.json` | File hashes, counts, eval results and gate status. |

**Agents operate; people govern.** Agents can view, enter and operate their own zone, and nothing else. `delegate`
belongs to stewards. `transfer` and `govern`, plus the PBC's six reserved actions (taken verbatim from
`worlds/PBC.json`), are held for a 2-of-3 steward quorum. The Steward Council zone that every spec lists is
merged into the council card. It is never a zone, because agents operate zones. Each world's Omega Steward from
`agents/advisory/omega_agents.json` is linked on its world card as *defined, not seated*.

**Nothing invented.** Every zone and agent card keeps its spec's citation, and an eval checks this. Each world's
`gaps` list what is still missing: an RP1 anchor (37 of 41 worlds) or an agent whose zone the spec does not name.

## Evals (17 per world, 697 in all)

These check: unique IDs, parents before children, a single root, the umbrella in every node name, the 48-character
name limit, no agent holding a reserved right, reserved actions verbatim with a 2-of-3 quorum, three empty human
seats, no agent on the council, the council not being a zone, citations, nothing invented, every spec entry carded,
the resource URL limit, the GLB parsing, the GLB card tree matching the cards, and every primitive tagged.

Five deliberately broken worlds must each fail exactly their own check. If they don't, the suite isn't
discriminating.

## Gates

| Gate | Status |
|---|---|
| 1.1 Generated core per world | **done** (41 worlds) |
| 1.2 GLB written, parsed and card tree verified | **done** in JavaScript, and checked by the Khronos validator |
| 1.2n Native fastgltf load in the Sneeze host | **open**: Sneeze (MetaversalCorp/Sneeze) is not checked out in this project |
| 1.3 SOM mount plan | **prepared, not mounted**: the RMCOBJECT decoder must be written from the checked-out `Map_Object.h` / `RmcObject.cpp` |
| 1.4 Mounted scene rendered in the Sneeze viewport, frame captured | **open** |

Next step: clone Sneeze, build the native host from the thread's `glb_scene_loader.cpp`, and point it at
`worldforge/out/<slug>/<slug>.glb` using the hash in that world's `manifest.json`.
