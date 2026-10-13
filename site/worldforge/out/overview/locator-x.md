# Locator.X

> Real-estate development and investment predictive tooling, plus the Academy that teaches it

| Field | Value |
|---|---|
| Status | coming soon |
| Umbrella | Powered by AGI Corp |
| Owner | AGI Future Foundation PBC |
| Management style | Agent-managed DAO |
| Principle | Agents operate; people govern. |
| RP1 anchor | lat 21.09705311564314, lon 142.69254864512746 (rad 6,371,000 m): https://enter.rp1.com?start_cid=553&lat=21.09705311564314&lon=142.69254864512746&rad=6371000 |
| Team brand mark | `LX`, hue 121, lockup "Locator.X · Powered by AGI Corp" |
| Root card | `world:locator-x` |
| Master Cards | 24 |

Open: [3-D viewer](../../viewer.html?world=locator-x) · [WorldForge console](../../../consoles/worldforge/index.html?world=locator-x) · [cards.json](../locator-x/cards.json) · [GLB](../locator-x/locator-x.glb) · [mount plan](../locator-x/sneeze-mount-plan.json) · [manifest](../locator-x/manifest.json) · [network overview](README.md)

_Source: `worldforge/out/locator-x/cards.json#world:locator-x`, `worlds/generated/teams/locator-x.json#brand`_

## Ownership and permissions

Every object in Locator.X is a SmartCiti.X Master Card owned by AGI Future Foundation PBC. The tree below follows `parentCardId`: world, plaza (coordinator and scripted advisors), gate, council (human seats), Omega Steward, then zones with their agent avatars.

- **Locator.X** (world) `world:locator-x`: coming soon; Agent-managed DAO
  - **Locator.X Plaza** (plaza) `plaza:locator-x`: the shared round plaza every world opens onto
    - **Locator.X Coordinator** (coordinator) `coordinator:locator-x`: swarm coordinator (hub-hybrid: coordinator supervises, specialists hand off swarm-style): routes turns, answers unroutable ones, hands off to specialists
    - **Host Advisor** (advisor) `advisor:locator-x/host`: scripted guide: welcoming visitors and pointing them to the right zone
    - **Steward Liaison** (advisor) `advisor:locator-x/steward`: scripted guide: connecting visitors and agents to the human stewards
    - **Alignment Advisor** (advisor) `advisor:locator-x/alignment`: scripted guide: the Alignment Evaluation Gate and the agents' limits
  - **Alignment Evaluation Gate** (gate) `gate:locator-x`: Pre-registered safety evaluation before deployment
  - **Steward Council** (council) `council:locator-x`: Human stewards: oversight, values alignment and final governance
    - **Steward Seat 1** (seat) `seat:locator-x/steward-1`: human seat, empty
    - **Steward Seat 2** (seat) `seat:locator-x/steward-2`: human seat, empty
    - **Steward Seat 3** (seat) `seat:locator-x/steward-3`: human seat, empty
  - **Omega Steward · Locator.X** (omega) `omega:locator-x`: defined, not seated; seated agent: none
  - **Master Dashboard** (zone) `zone:locator-x/master-dashboard`: Central hub: portfolio summary, cross-market comparison and navigation to market editions
    - **Guide** (agent) `agent:locator-x/guide`: Persistent floating assistant: guided tour of every section and live search over help text
  - **Underwriting Desk** (zone) `zone:locator-x/underwriting-desk`: Maps, scores and underwrites parcels; runs the seven-gate LOCATOR screen; break-even at DSCR 1.20
    - **Forecast Agent** (agent) `agent:locator-x/forecast-agent`: Predictive models over the ZIP value series with point forecast and ~80% band
  - **Evidence Layer** (zone) `zone:locator-x/evidence-layer`: Grades every number shown: coverage before any rate, sample floor of 5, explicit list of unknowns
    - **Review Agent** (agent) `agent:locator-x/review-agent`: Produces a review digest per scan pass, incl. 12-month re-underwrite flip scan
  - **The Academy** (zone) `zone:locator-x/the-academy`: 19 tracks, 92 lessons, 50 curriculum items teaching how to read what the platform produces
    - **Level Gates** (agent) `agent:locator-x/level-gates`: Grades curriculum levels as capabilities on a real parcel; counts certainty errors
  - **Market Editions** (zone) `zone:locator-x/market-editions`: National corridor baseline, Bay Area premium and New Orleans emerging-market maps
    - **Scout Agent** (agent) `agent:locator-x/scout-agent`: Scans feeds, diffs, scores and matches new listings and changes
  - **Louisiana Developer Desk** (zone) `zone:locator-x/louisiana-developer-desk`: Parish-by-parish record coverage, named data traps, cancelled capital weighted to zero
    - **Developer Brief Desk** (agent) `agent:locator-x/developer-brief-desk`: Role-only agent: tells a developer what the parish record supports and what it caps at

Card counts: world 1, plaza 1, coordinator 1, advisor 3, gate 1, council 1, seat 3, omega 1, zone 6, agent 6. The 3 council seats are human seats; 3 are empty.

### Who holds each right

Cards that share the same permission matrix are grouped into one column (3 distinct matrices across 24 cards).

| Right | world, advisor x3, gate, omega | plaza, coordinator, zone x6, agent x6 | council, seat x3 |
|---|---|---|---|
| view | public | public | public |
| enter | public | public | stewards |
| build | stewards | stewards | stewards |
| operate | stewards | stewards, agents:zone | stewards |
| delegate | stewards | stewards | stewards |
| transfer | steward-quorum | steward-quorum | steward-quorum |
| govern | steward-quorum | steward-quorum | steward-quorum |

Holders are written as the cards store them. In the words of `worldforge/README.md`: agents can view, enter and operate their own zone (`agents:zone`), and nothing else; `delegate` belongs to stewards; `transfer` and `govern` are held for a 2-of-3 steward quorum.

### Actions reserved for people

| Action | Held for | Quorum | Seats |
|---|---|---|---|
| `governance.final_vote` | Steward Council | 2-of-3 | 3 |
| `charter.amend` | Steward Council | 2-of-3 | 3 |
| `treasury.transfer` | Steward Council | 2-of-3 | 3 |
| `proposal.enact` | Steward Council | 2-of-3 | 3 |
| `windfall.distribute` | Steward Council | 2-of-3 | 3 |
| `steward.appoint` | Steward Council | 2-of-3 | 3 |

The same 6 reservations are carried on 24 of 24 cards. 11 of 11 agent, coordinator, advisor and Omega cards list all 6 in `may_never`.

_Source: `worldforge/out/locator-x/cards.json`, `worlds/PBC.json#reserved_for_humans`_

## Volums

Each card covers a Volum: a bounded 3-D region, a box given by its centre and half-extents in metres. Size is twice the half-extents.

| Card | Kind | Shape | Centre (m) | Half-extents (m) | Size (m) |
|---|---|---|---|---|---|
| Locator.X `world:locator-x` | world | box | (0, 40, 0) | (156, 40, 156) | 312 x 80 x 312 |
| Locator.X Plaza `plaza:locator-x` | plaza | box | (0, 5, 0) | (24, 5, 24) | 48 x 10 x 48 |
| Alignment Evaluation Gate `gate:locator-x` | gate | box | (0, 6, 136) | (10, 6, 3) | 20 x 12 x 6 |
| Steward Council `council:locator-x` | council | box | (0, 6, -136) | (14, 6, 10) | 28 x 12 x 20 |
| Omega Steward · Locator.X `omega:locator-x` | omega | box | (26, 1, -136) | (1.5, 1.2, 1.5) | 3 x 2.4 x 3 |
| Master Dashboard `zone:locator-x/master-dashboard` | zone | box | (-48, 8, 83.14) | (18, 10, 18) | 36 x 20 x 36 |
| Underwriting Desk `zone:locator-x/underwriting-desk` | zone | box | (-96, 8, 0) | (18, 10, 18) | 36 x 20 x 36 |
| Evidence Layer `zone:locator-x/evidence-layer` | zone | box | (-48, 8, -83.14) | (18, 10, 18) | 36 x 20 x 36 |
| The Academy `zone:locator-x/the-academy` | zone | box | (48, 8, -83.14) | (18, 10, 18) | 36 x 20 x 36 |
| Market Editions `zone:locator-x/market-editions` | zone | box | (96, 8, 0) | (18, 10, 18) | 36 x 20 x 36 |
| Louisiana Developer Desk `zone:locator-x/louisiana-developer-desk` | zone | box | (48, 8, 83.14) | (18, 10, 18) | 36 x 20 x 36 |

The other 13 cards (coordinator, advisors, seats and agents) each hold a small box at their post; their Volums are in `worldforge/out/locator-x/cards.json`.

_Source: `worldforge/out/locator-x/cards.json#cards[].volum`_

## Buildings and interiors

7 cards carry a building: an exterior, an interior and a room model, with a door.

| Card | Kind | Exterior | Interior | Room | Texture res. ext/int (px) | Triangles ext/int | Door (centre, half-width, head) |
|---|---|---|---|---|---|---|---|
| Steward Council `council:locator-x` | forum | [spaces-ext-forum.glb](../../../my-fabric/worlds/models/spaces-ext-forum.glb) | [spaces-int-forum.glb](../../../my-fabric/worlds/models/spaces-int-forum.glb) | [room-locator-x-7.glb](../../../my-fabric/worlds/models/room-locator-x-7.glb) | 2,048 / 1,024 | 1,602 / 1,776 | (0, 0, 4), 1.2 m, 2.8 m |
| Master Dashboard `zone:locator-x/master-dashboard` | desk | [spaces-ext-desk.glb](../../../my-fabric/worlds/models/spaces-ext-desk.glb) | [spaces-int-desk.glb](../../../my-fabric/worlds/models/spaces-int-desk.glb) | [room-locator-x-1.glb](../../../my-fabric/worlds/models/room-locator-x-1.glb) | 2,048 / 1,024 | 1,958 / 2,440 | (0, 0, 4), 1.2 m, 2.8 m |
| Underwriting Desk `zone:locator-x/underwriting-desk` | studio | [spaces-ext-studio.glb](../../../my-fabric/worlds/models/spaces-ext-studio.glb) | [spaces-int-studio.glb](../../../my-fabric/worlds/models/spaces-int-studio.glb) | [room-locator-x-2.glb](../../../my-fabric/worlds/models/room-locator-x-2.glb) | 2,048 / 1,024 | 1,704 / 1,492 | (0, 0, 4), 1.2 m, 2.8 m |
| Evidence Layer `zone:locator-x/evidence-layer` | lab | [spaces-ext-lab.glb](../../../my-fabric/worlds/models/spaces-ext-lab.glb) | [spaces-int-lab.glb](../../../my-fabric/worlds/models/spaces-int-lab.glb) | [room-locator-x-3.glb](../../../my-fabric/worlds/models/room-locator-x-3.glb) | 2,048 / 1,024 | 2,046 / 1,716 | (0, 0, 4), 1.2 m, 2.8 m |
| The Academy `zone:locator-x/the-academy` | library | [spaces-ext-library.glb](../../../my-fabric/worlds/models/spaces-ext-library.glb) | [spaces-int-library.glb](../../../my-fabric/worlds/models/spaces-int-library.glb) | [room-locator-x-4.glb](../../../my-fabric/worlds/models/room-locator-x-4.glb) | 2,048 / 1,024 | 1,722 / 4,588 | (0, 0, 4), 1.2 m, 2.8 m |
| Market Editions `zone:locator-x/market-editions` | ops | [spaces-ext-ops.glb](../../../my-fabric/worlds/models/spaces-ext-ops.glb) | [spaces-int-ops.glb](../../../my-fabric/worlds/models/spaces-int-ops.glb) | [room-locator-x-5.glb](../../../my-fabric/worlds/models/room-locator-x-5.glb) | 2,048 / 1,024 | 1,742 / 1,392 | (0, 0, 4), 1.2 m, 2.8 m |
| Louisiana Developer Desk `zone:locator-x/louisiana-developer-desk` | desk | [spaces-ext-desk.glb](../../../my-fabric/worlds/models/spaces-ext-desk.glb) | [spaces-int-desk.glb](../../../my-fabric/worlds/models/spaces-int-desk.glb) | [room-locator-x-6.glb](../../../my-fabric/worlds/models/room-locator-x-6.glb) | 2,048 / 1,024 | 1,958 / 2,440 | (0, 0, 4), 1.2 m, 2.8 m |

Exterior plus interior triangles across these buildings: 28,576.

_Source: `worldforge/out/locator-x/cards.json#cards[].building`, `my-fabric/worlds/spaces_index.json#worlds[slug=locator-x]`_

## Avatars and agents

11 avatars stand in this world (registry: 11 avatars, 6 specialists, 3 advisors, Omega present). Voiced means a rendered intro file is listed in `worldforge/out/voices/manifest.json` and exists on disk; otherwise the viewer falls back to a labelled browser voice.

### Coordinator

- **Locator.X Coordinator** (coordinator) `coordinator:locator-x`, in Locator.X Plaza: swarm `locator-x.coordinator`; voice `bm_george`; voiced: yes (11 s, [audio](../voices/locator-x/coordinator.mp4))
  - Role: hub-hybrid: coordinator supervises, specialists hand off swarm-style
  - Intro: "I am the Locator.X Coordinator, at Locator.X Plaza. I route each question to the right specialist; people decide. You are hearing a synthetic voice."

### Scripted advisors

- **Host Advisor** (host) `advisor:locator-x/host`, in Locator.X Plaza: advisor contract `agents/advisors/locator-x.json#host`; voice `bf_lily`; voiced: yes (8.9 s, [audio](../voices/locator-x/host.mp4))
  - Role: welcoming visitors and pointing them to the right zone
  - Intro: "I am the Host Advisor: welcoming visitors and pointing them to the right zone. Scripted guide, synthetic voice: not an AI model, not a person."
- **Steward Liaison** (liaison) `advisor:locator-x/steward`, in Locator.X Plaza: advisor contract `agents/advisors/locator-x.json#steward`; voice `bm_daniel`; voiced: yes (8.6 s, [audio](../voices/locator-x/steward.mp4))
  - Role: connecting visitors and agents to the human stewards
  - Intro: "I am the Steward Liaison: connecting visitors and agents to the human stewards. Scripted guide, synthetic voice: not an AI model, not a person."
- **Alignment Advisor** (alignment) `advisor:locator-x/alignment`, in Locator.X Plaza: advisor contract `agents/advisors/locator-x.json#alignment`; voice `af_alloy`; voiced: yes (9.3 s, [audio](../voices/locator-x/alignment.mp4))
  - Role: the Alignment Evaluation Gate and the agents' limits
  - Intro: "I am the Alignment Advisor: the Alignment Evaluation Gate and the agents' limits. Scripted guide, synthetic voice: not an AI model, not a person."

### Specialist agents

- **Guide** (specialist) `agent:locator-x/guide`, in Master Dashboard: swarm `locator-x.guide`; voice `am_liam`; voiced: yes (6.8 s, [audio](../voices/locator-x/guide.mp4))
  - Role: Persistent floating assistant: guided tour of every section and live search over help text
  - Intro: "I am the Guide for Locator.X, in Master Dashboard. I draft and check; people decide. You are hearing a synthetic voice."
- **Forecast Agent** (specialist) `agent:locator-x/forecast-agent`, in Underwriting Desk: swarm `locator-x.forecast-agent`; voice `bf_isabella`; voiced: not voiced
  - Role: Predictive models over the ZIP value series with point forecast and ~80% band
  - Intro: "I am the Forecast Agent for Locator.X, in Underwriting Desk. I draft and check; people decide. You are hearing a synthetic voice."
- **Review Agent** (specialist) `agent:locator-x/review-agent`, in Evidence Layer: swarm `locator-x.review-agent`; voice `af_sky`; voiced: not voiced
  - Role: Produces a review digest per scan pass, incl. 12-month re-underwrite flip scan
  - Intro: "I am the Review Agent for Locator.X, in Evidence Layer. I draft and check; people decide. You are hearing a synthetic voice."
- **Level Gates** (specialist) `agent:locator-x/level-gates`, in The Academy: swarm `locator-x.level-gates`; voice `bf_isabella`; voiced: not voiced
  - Role: Grades curriculum levels as capabilities on a real parcel; counts certainty errors
  - Intro: "I am the Level Gates for Locator.X, in The Academy. I draft and check; people decide. You are hearing a synthetic voice."
- **Scout Agent** (specialist) `agent:locator-x/scout-agent`, in Market Editions: swarm `locator-x.scout-agent`; voice `bf_emma`; voiced: not voiced
  - Role: Scans feeds, diffs, scores and matches new listings and changes
  - Intro: "I am the Scout Agent for Locator.X, in Market Editions. I draft and check; people decide. You are hearing a synthetic voice."
- **Developer Brief Desk** (specialist) `agent:locator-x/developer-brief-desk`, in Louisiana Developer Desk: swarm `locator-x.developer-brief-desk`; voice `am_adam`; voiced: not voiced
  - Role: Role-only agent: tells a developer what the parish record supports and what it caps at
  - Intro: "I am the Developer Brief Desk for Locator.X, in Louisiana Developer Desk. I draft and check; people decide. You are hearing a synthetic voice."

### Omega Steward avatar

- **Omega Steward · Locator.X** (omega) `omega:locator-x`, in Steward Council: hive `omega.locator-x`; voice `bm_lewis`; voiced: yes, hive greet line (8.13 s, [audio](../../../agents/hive/voices/locator-x/greet.mp4))
  - Intro: "Hello, I am the Omega Steward for Locator.X. You are hearing a synthetic voice; I am an agent, not a person."

Intro lines voiced: 5 of 10 coordinator, advisor and specialist avatars.

_Source: `worldforge/out/avatars/index.json#rows[world=locator-x]`, `worldforge/out/voices/manifest.json#lines`_

## Omega Steward

**Omega Steward · Locator.X** (`omega.locator-x`), card `omega:locator-x`: defined, not seated. Seated in the hive: no.

- Temperament: attentive and concrete about its tagline: Real-estate development and investment predictive tooling, plus the Academy that teaches it
- Style: short, plain sentences; names its zones (Master Dashboard, Underwriting Desk, Evidence Layer), cites the record it reads, and always says who decides (the stewards, 2 of 3 signed votes)
- Values:
  - people decide: Agent-managed DAO, human-governed
  - stewards decide by 2 of 3 signed votes
  - report probe scores exactly as measured
  - draft quotes with every term left null
- Refuses (11): `governance.final_vote`, `charter.amend`, `treasury.transfer`, `proposal.enact`, `windfall.distribute`, `steward.appoint`, `set_price`, `accept_equity`, `accept_crypto`, `issue_invoice`, `move_funds`
- Voice: Kokoro `bm_lewis`, speed 0.92; browser fallback pitch 0.85, rate 0.92, en-GB
- Metaprompt: [agents/hive/prompts/locator-x.md](../../../agents/hive/prompts/locator-x.md)

### Voice lines

| Line | Text | Recorded |
|---|---|---|
| greet | "Hello, I am the Omega Steward for Locator.X. You are hearing a synthetic voice; I am an agent, not a person." | yes, 8.13 s ([audio](../../../agents/hive/voices/locator-x/greet.mp4)) |
| role | "I look after Locator.X's world: Master Dashboard, Underwriting Desk, Evidence Layer, plus its probe scores and its installer's dry run." | yes, 9.98 s ([audio](../../../agents/hive/voices/locator-x/role.mp4)) |
| boundary | "Agents draft and route; people decide. I will never accept crypto: that is held for the Steward Council." | yes, 7.17 s ([audio](../../../agents/hive/voices/locator-x/boundary.mp4)) |
| services | "For services, ask the Forecast Agent in Underwriting Desk about research synthesis. Locator.X lists 5 service cards; people confirm every step." | yes, 11.16 s ([audio](../../../agents/hive/voices/locator-x/services.mp4)) |

4 of 4 lines are recorded.

Persona grounded in: `agents/advisory/omega_agents.json#omegas.8.corporation.kind`, `agents/advisory/omega_agents.json#omegas.8.routes`, `worlds/locator-x/spec.json#tagline`, `worlds/locator-x/spec.json#zones`, `agents/dao/locator-x.json#management_style`, `agents/dao/locator-x.json#quorum`, `agents/dao/locator-x.json#stewards`, `agents/services/index.json#cards.43.offers`.

_Source: `agents/hive/index.json#omegas[world=locator-x]`, `worldforge/out/locator-x/cards.json#omega:locator-x`_

## Landmark

Registry note: "synthetic procedural civic landmark; not a real building and not modelled on one".

| Field | Value |
|---|---|
| Model | [locator-x.glb](../assets/landmarks/locator-x.glb) |
| Height | 48 m |
| Style | platform-prism: chamfered octagonal prism with a batter and one setback, tinted edge fins, glass main faces, stepped crown with emissive bands and a mast |
| Plaque (brand mark letters) | `LX` |
| Tint hue | 121 |
| Triangles / vertices | 9,060 / 9,062 |
| File size | 1,851,824 bytes |
| Scene node | Landmark · Locator.X |
| Suggested placement (not applied) | translation (13.5, 0, -50.5), yaw -15 deg, clearance 3.15 m |

Height rule: 30 + 40 * u, u = first 48 bits of sha256('landmark:height:<slug>'), rounded to 0.5 m.

_Source: `worldforge/out/assets/landmarks/index.json#worlds[slug=locator-x]`_

## Onchain-ready

**Not deployed.** Nothing is deployed or minted. No chain, contract, wallet, key, address or transaction exists for this collection, and nothing is offered for sale (no price, royalty or fee recipient).

| Field | Value |
|---|---|
| Collection | Locator.X Master Cards ([collection.json](../onchain/locator-x/collection.json), [proofs.json](../onchain/locator-x/proofs.json)) |
| Standard | ERC-721 metadata JSON (draft, not deployed) |
| Tokens / cards | 24 / 24 |
| Token id rule | first 16 hex characters of sha256(cardId), lowercase, no prefix (64 bits) |
| Merkle root | `aa9f9a5ef201a2d944cdd1c639a11221aaabb0300b3129a743ac1dcfd507bef2` |
| Network root (all worlds) | `4496b45d7430322d719912d4ba31b2381651d944677bba1aea692d0ec4b13a93` |
| Deployment status | not deployed; chain none, contract none, minted 0, transactions 0 |
| Network proof length | 6 |

_Source: `worldforge/out/onchain/locator-x/collection.json`, `worldforge/out/onchain/index.json`_

## Sneeze/RP1 readiness

| Measure | Value |
|---|---|
| Mount plan nodes (plan file) | 53 |
| Plan nodes / resource nodes (manifest) | 53 / 29 |
| Primitives / roads | 29 / 8 |
| Binding status | decoder-available-not-mounted |
| Mount parent | `SCENE::Fabric_Root()->Node_Root()` |
| Shared resource | `http://127.0.0.1:8789/unit-cube.glb` |
| Conformance (static check) | 53 nodes, 0 native violations, 0 JSON-route violations |
| Conformance report status | static-check-only-nothing-mounted-or-rendered |

### Gates

| Gate | Status |
|---|---|
| 1.1 generated core | done |
| 1.2 GLB parsed + card tree verified (JavaScript) | done |
| 1.2n native fastgltf load | open: Sneeze not checked out here |
| 1.3 SOM mount plan | prepared-not-mounted |
| 1.4 rendered frame | open |

_Source: `worldforge/out/locator-x/sneeze-mount-plan.json`, `worldforge/out/locator-x/manifest.json#counts,gates`, `worldforge/native/conformance-report.json#perPlan[slug=locator-x]`_

## Training

Training data is present at [worldforge/out/training/locator-x.json](../training/locator-x.json) (`worldforge-training/0.1`, from `worldforge/training.mjs`).

Registry note: "Draft curricula assembled from the registries; nothing invented. No model has taught any lesson, no person or robot has been assessed here, and no lesson is certified: certification is a human/steward act. Advisors are scripted guides and deliver only their own scripted orientation; Omegas are defined, not seated, and deliver nothing."

### Lessons (10)

| Lesson | Kind | Mode | Zone | Steps | Status | Assessment | Certified |
|---|---|---|---|---|---|---|---|
| Host Advisor: welcoming visitors and pointing them to the right zone `lesson:locator-x/orientation/host` | scripted-orientation | scripted | Locator.X Plaza | 4 | draft | not measurable in simulation | no |
| Steward Liaison: connecting visitors and agents to the human stewards `lesson:locator-x/orientation/steward` | scripted-orientation | scripted | Locator.X Plaza | 3 | draft | not measurable in simulation | no |
| Alignment Advisor: the Alignment Evaluation Gate and the agents' limits `lesson:locator-x/orientation/alignment` | scripted-orientation | scripted | Locator.X Plaza | 3 | draft | not measurable in simulation | no |
| How Locator.X routes a question `lesson:locator-x/routing` | routing | model-taught | Locator.X Plaza | 6 | draft | not measurable in simulation | no |
| Master Dashboard: what happens here `lesson:locator-x/zone/master-dashboard` | zone-orientation | model-taught | Master Dashboard | 3 | draft | not measurable in simulation | no |
| Underwriting Desk: what happens here `lesson:locator-x/zone/underwriting-desk` | zone-orientation | model-taught | Underwriting Desk | 3 | draft | not measurable in simulation | no |
| Evidence Layer: what happens here `lesson:locator-x/zone/evidence-layer` | zone-orientation | model-taught | Evidence Layer | 3 | draft | not measurable in simulation | no |
| The Academy: what happens here `lesson:locator-x/zone/the-academy` | zone-orientation | model-taught | The Academy | 3 | draft | not measurable in simulation | no |
| Market Editions: what happens here `lesson:locator-x/zone/market-editions` | zone-orientation | model-taught | Market Editions | 3 | draft | not measurable in simulation | no |
| Louisiana Developer Desk: what happens here `lesson:locator-x/zone/louisiana-developer-desk` | zone-orientation | model-taught | Louisiana Developer Desk | 3 | draft | not measurable in simulation | no |

### Tutors (7)

| Tutor | Kind | Lessons | Persona gates passed |
|---|---|---|---|
| Locator.X Coordinator `tutor:locator-x/coordinator` | coordinator | 1 | 10 of 10 |
| Guide `tutor:locator-x/specialist/guide` | specialist | 1 | 13 of 13 |
| Forecast Agent `tutor:locator-x/specialist/forecast-agent` | specialist | 1 | 13 of 13 |
| Review Agent `tutor:locator-x/specialist/review-agent` | specialist | 1 | 13 of 13 |
| Level Gates `tutor:locator-x/specialist/level-gates` | specialist | 1 | 13 of 13 |
| Scout Agent `tutor:locator-x/specialist/scout-agent` | specialist | 1 | 13 of 13 |
| Developer Brief Desk `tutor:locator-x/specialist/developer-brief-desk` | specialist | 1 | 13 of 13 |

7 training gaps listed under Gaps below.

_Source: `worldforge/out/training/locator-x.json`_

## Evals

WorldForge build evals: 26 of 26 pass.

`unique_ids` pass · `parents_first` pass · `single_root` pass · `umbrella_in_names` pass · `name_limit` pass · `agents_hold_no_reserved_right` pass · `reserved_actions_verbatim` pass · `three_human_seats` pass · `no_agent_on_council` pass · `cited` pass · `omega_carded` pass · `omega_off_council` pass · `omega_voice_bound` pass · `agents_bound` pass · `coordinator_bound` pass · `advisors_scripted` pass · `avatar_roles_known` pass · `buildings_resolve` pass · `council_not_a_zone` pass · `nothing_invented` pass · `every_spec_entry_carded` pass · `rp1_names_and_bounds` pass · `resource_url_fits` pass · `glb_parses` pass · `glb_card_tree_matches` pass · `glb_primitives_tagged` pass

Avatar checks: 21 of 21 pass.

Onchain per-world evals (13, network failing: 0): `one_token_per_card`, `proofs_verify`, `no_agent_holds_reserved_right`, `reserved_actions_verbatim`, `transfer_held_for_quorum`, `faithful_to_cards`, `metadata_shape`, `not_deployed_not_minted`, `honest_status`, `no_address_shapes`, `no_key_shapes`, `no_email_shapes`, `canonical_json`.

_Source: `worldforge/out/locator-x/manifest.json#evals`, `worldforge/out/avatars/index.json#worlds[slug=locator-x].checks`, `worldforge/out/onchain/index.json#evals`_

## Gaps

- Omega Steward is defined, not seated: no agent is seated (from `worldforge/out/locator-x/cards.json#world:locator-x.omega_steward`).
- 3 human steward seats are empty.
- 5 intro lines are not voiced: Forecast Agent, Review Agent, Level Gates, Scout Agent, Developer Brief Desk.
- Training: no training module, rubric module or robotics module in agents/training, agents/rubrics or agents/robotics names this world: its lessons are orientation only (advisor topics, routing table, zone purposes and agent roles) (from `worldforge/out/training/locator-x.json#gaps`)
- Training: The Academy (19 tracks, 92 lessons, 50 curriculum items teaching how to read what the platform produces) is cited from ~/Downloads/Locator.X-main/README.md, The Academy, which is not in this repository: none of its tracks or lessons is reproduced here (from `worldforge/out/training/locator-x.json#gaps`)
- Training: spec gap: No source describes a 3D/RP1 world, spatial layout or reason for the Pacific anchor coordinates (from `worldforge/out/training/locator-x.json#gaps`)
- Training: spec gap: Sources name no agent personas or people; Level Gates is a grading module and Developer Brief Desk is role-only (from `worldforge/out/training/locator-x.json#gaps`)
- Training: spec gap: Platform guide figures (707K/500K/245K/207K properties) are not reconciled with the brief's Louisiana counts (from `worldforge/out/training/locator-x.json#gaps`)
- Training: spec gap: Only the pptx says 'Powered by AGI Corp'; the repo says 'Built by the AGI Future Foundation' (from `worldforge/out/training/locator-x.json#gaps`)
- Training: spec gap: iOS app (Locator.Xapp) only confirms Underwrite/Record/Explore tabs; no launch status or date given (from `worldforge/out/training/locator-x.json#gaps`)
- Gate 1.2n native fastgltf load: open: Sneeze not checked out here.
- Gate 1.3 SOM mount plan: prepared-not-mounted.
- Gate 1.4 rendered frame: open.

_Source: `worldforge/out/locator-x/cards.json#gaps`, `worldforge/out/locator-x/manifest.json#gates`, `worldforge/out/voices/manifest.json`, `agents/hive/index.json`, `worldforge/out/training/locator-x.json`_
