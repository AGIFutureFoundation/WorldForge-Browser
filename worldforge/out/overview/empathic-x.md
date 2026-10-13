# Empathic.X

> Empathy & Emotional Intelligence

| Field | Value |
|---|---|
| Status | coming soon |
| Umbrella | Powered by AGI Corp |
| Owner | AGI Future Foundation PBC |
| Management style | Agent-managed DAO |
| Principle | Agents operate; people govern. |
| RP1 anchor | lat 47.43990000744796, lon -179.34952851914045 (rad 6,371,000 m): https://enter.rp1.com?start_cid=553&lat=47.43990000744796&lon=-179.34952851914045&rad=6371000 |
| Team brand mark | `EX`, hue 82, lockup "Empathic.X · Powered by AGI Corp" |
| Root card | `world:empathic-x` |
| Master Cards | 22 |

Open: [3-D viewer](../../viewer.html?world=empathic-x) · [WorldForge console](../../../consoles/worldforge/index.html?world=empathic-x) · [cards.json](../empathic-x/cards.json) · [GLB](../empathic-x/empathic-x.glb) · [mount plan](../empathic-x/sneeze-mount-plan.json) · [manifest](../empathic-x/manifest.json) · [network overview](README.md)

_Source: `worldforge/out/empathic-x/cards.json#world:empathic-x`, `worlds/generated/teams/empathic-x.json#brand`_

## Ownership and permissions

Every object in Empathic.X is a SmartCiti.X Master Card owned by AGI Future Foundation PBC. The tree below follows `parentCardId`: world, plaza (coordinator and scripted advisors), gate, council (human seats), Omega Steward, then zones with their agent avatars.

- **Empathic.X** (world) `world:empathic-x`: coming soon; Agent-managed DAO
  - **Empathic.X Plaza** (plaza) `plaza:empathic-x`: the shared round plaza every world opens onto
    - **Empathic.X Coordinator** (coordinator) `coordinator:empathic-x`: swarm coordinator (hub-hybrid: coordinator supervises, specialists hand off swarm-style): routes turns, answers unroutable ones, hands off to specialists
    - **Host Advisor** (advisor) `advisor:empathic-x/host`: scripted guide: welcoming visitors and pointing them to the right zone
    - **Steward Liaison** (advisor) `advisor:empathic-x/steward`: scripted guide: connecting visitors and agents to the human stewards
    - **Alignment Advisor** (advisor) `advisor:empathic-x/alignment`: scripted guide: the Alignment Evaluation Gate and the agents' limits
  - **Alignment Evaluation Gate** (gate) `gate:empathic-x`: Pre-registered safety evaluation before deployment
  - **Steward Council** (council) `council:empathic-x`: Human stewards: oversight, values alignment and final governance
    - **Steward Seat 1** (seat) `seat:empathic-x/steward-1`: human seat, empty
    - **Steward Seat 2** (seat) `seat:empathic-x/steward-2`: human seat, empty
    - **Steward Seat 3** (seat) `seat:empathic-x/steward-3`: human seat, empty
  - **Omega Steward · Empathic.X** (omega) `omega:empathic-x`: defined, not seated; seated agent: none
  - **Self-Reader Grove** (zone) `zone:empathic-x/self-reader-grove`: Self-awareness (SA): naming what you feel before you act, where it lands in your body
    - **Self-Reader Guide** (agent) `agent:empathic-x/self-reader-guide`: Guide for SA themes and transfer checks, e.g. name three states you were in this week
  - **Other-Reader Commons** (zone) `zone:empathic-x/other-reader-commons`: Awareness of others (AO): asking instead of assuming, listening without preparing a reply
    - **Other-Reader Guide** (agent) `agent:empathic-x/other-reader-guide`: Guide for AO themes, e.g. reading a face without deciding what it means
  - **Repairer's Hall** (zone) `zone:empathic-x/repairer-s-hall`: Repair (RR): coming down, apologising properly, saying the hard thing kindly
    - **Repair Guide** (agent) `agent:empathic-x/repair-guide`: Guide for RR themes, e.g. staying in a hard conversation, receiving an apology
  - **Room-Reader Plaza** (zone) `zone:empathic-x/room-reader-plaza`: Reading the room (RM): where the energy is, who is idle, the moment before it goes wrong
    - **Room-Reader Guide** (agent) `agent:empathic-x/room-reader-guide`: Guide for RM themes, e.g. a room with a newcomer in it, when to do nothing
  - **Practitioner Workshop** (zone) `zone:empathic-x/practitioner-workshop`: Emotion at work (EW): feedback that can be used, saying no at work, emotional labour
    - **Practitioner Guide** (agent) `agent:empathic-x/practitioner-guide`: Guide for EW themes, e.g. the colleague who is struggling, leaving well

Card counts: world 1, plaza 1, coordinator 1, advisor 3, gate 1, council 1, seat 3, omega 1, zone 5, agent 5. The 3 council seats are human seats; 3 are empty.

### Who holds each right

Cards that share the same permission matrix are grouped into one column (3 distinct matrices across 22 cards).

| Right | world, advisor x3, gate, omega | plaza, coordinator, zone x5, agent x5 | council, seat x3 |
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

The same 6 reservations are carried on 22 of 22 cards. 10 of 10 agent, coordinator, advisor and Omega cards list all 6 in `may_never`.

_Source: `worldforge/out/empathic-x/cards.json`, `worlds/PBC.json#reserved_for_humans`_

## Volums

Each card covers a Volum: a bounded 3-D region, a box given by its centre and half-extents in metres. Size is twice the half-extents.

| Card | Kind | Shape | Centre (m) | Half-extents (m) | Size (m) |
|---|---|---|---|---|---|
| Empathic.X `world:empathic-x` | world | box | (0, 40, 0) | (150, 40, 150) | 300 x 80 x 300 |
| Empathic.X Plaza `plaza:empathic-x` | plaza | box | (0, 5, 0) | (24, 5, 24) | 48 x 10 x 48 |
| Alignment Evaluation Gate `gate:empathic-x` | gate | box | (0, 6, 130) | (10, 6, 3) | 20 x 12 x 6 |
| Steward Council `council:empathic-x` | council | box | (0, 6, -130) | (14, 6, 10) | 28 x 12 x 20 |
| Omega Steward · Empathic.X `omega:empathic-x` | omega | box | (26, 1, -130) | (1.5, 1.2, 1.5) | 3 x 2.4 x 3 |
| Self-Reader Grove `zone:empathic-x/self-reader-grove` | zone | box | (-52.9, 8, 72.81) | (18, 10, 18) | 36 x 20 x 36 |
| Other-Reader Commons `zone:empathic-x/other-reader-commons` | zone | box | (-85.6, 8, -27.81) | (18, 10, 18) | 36 x 20 x 36 |
| Repairer's Hall `zone:empathic-x/repairer-s-hall` | zone | box | (0, 8, -90) | (18, 10, 18) | 36 x 20 x 36 |
| Room-Reader Plaza `zone:empathic-x/room-reader-plaza` | zone | box | (85.6, 8, -27.81) | (18, 10, 18) | 36 x 20 x 36 |
| Practitioner Workshop `zone:empathic-x/practitioner-workshop` | zone | box | (52.9, 8, 72.81) | (18, 10, 18) | 36 x 20 x 36 |

The other 12 cards (coordinator, advisors, seats and agents) each hold a small box at their post; their Volums are in `worldforge/out/empathic-x/cards.json`.

_Source: `worldforge/out/empathic-x/cards.json#cards[].volum`_

## Buildings and interiors

6 cards carry a building: an exterior, an interior and a room model, with a door.

| Card | Kind | Exterior | Interior | Room | Texture res. ext/int (px) | Triangles ext/int | Door (centre, half-width, head) |
|---|---|---|---|---|---|---|---|
| Steward Council `council:empathic-x` | forum | [spaces-ext-forum.glb](../../../my-fabric/worlds/models/spaces-ext-forum.glb) | [spaces-int-forum.glb](../../../my-fabric/worlds/models/spaces-int-forum.glb) | [room-empathic-x-6.glb](../../../my-fabric/worlds/models/room-empathic-x-6.glb) | 2,048 / 1,024 | 1,602 / 1,776 | (0, 0, 4), 1.2 m, 2.8 m |
| Self-Reader Grove `zone:empathic-x/self-reader-grove` | studio | [spaces-ext-studio.glb](../../../my-fabric/worlds/models/spaces-ext-studio.glb) | [spaces-int-studio.glb](../../../my-fabric/worlds/models/spaces-int-studio.glb) | [room-empathic-x-1.glb](../../../my-fabric/worlds/models/room-empathic-x-1.glb) | 2,048 / 1,024 | 1,704 / 1,492 | (0, 0, 4), 1.2 m, 2.8 m |
| Other-Reader Commons `zone:empathic-x/other-reader-commons` | clinic | [spaces-ext-clinic.glb](../../../my-fabric/worlds/models/spaces-ext-clinic.glb) | [spaces-int-clinic.glb](../../../my-fabric/worlds/models/spaces-int-clinic.glb) | [room-empathic-x-2.glb](../../../my-fabric/worlds/models/room-empathic-x-2.glb) | 2,048 / 1,024 | 2,058 / 1,440 | (0, 0, 4), 1.2 m, 2.8 m |
| Repairer's Hall `zone:empathic-x/repairer-s-hall` | studio | [spaces-ext-studio.glb](../../../my-fabric/worlds/models/spaces-ext-studio.glb) | [spaces-int-studio.glb](../../../my-fabric/worlds/models/spaces-int-studio.glb) | [room-empathic-x-3.glb](../../../my-fabric/worlds/models/room-empathic-x-3.glb) | 2,048 / 1,024 | 1,704 / 1,492 | (0, 0, 4), 1.2 m, 2.8 m |
| Room-Reader Plaza `zone:empathic-x/room-reader-plaza` | library | [spaces-ext-library.glb](../../../my-fabric/worlds/models/spaces-ext-library.glb) | [spaces-int-library.glb](../../../my-fabric/worlds/models/spaces-int-library.glb) | [room-empathic-x-4.glb](../../../my-fabric/worlds/models/room-empathic-x-4.glb) | 2,048 / 1,024 | 1,722 / 4,588 | (0, 0, 4), 1.2 m, 2.8 m |
| Practitioner Workshop `zone:empathic-x/practitioner-workshop` | ops | [spaces-ext-ops.glb](../../../my-fabric/worlds/models/spaces-ext-ops.glb) | [spaces-int-ops.glb](../../../my-fabric/worlds/models/spaces-int-ops.glb) | [room-empathic-x-5.glb](../../../my-fabric/worlds/models/room-empathic-x-5.glb) | 2,048 / 1,024 | 1,742 / 1,392 | (0, 0, 4), 1.2 m, 2.8 m |

Exterior plus interior triangles across these buildings: 22,712.

_Source: `worldforge/out/empathic-x/cards.json#cards[].building`, `my-fabric/worlds/spaces_index.json#worlds[slug=empathic-x]`_

## Avatars and agents

10 avatars stand in this world (registry: 10 avatars, 5 specialists, 3 advisors, Omega present). Voiced means a rendered intro file is listed in `worldforge/out/voices/manifest.json` and exists on disk; otherwise the viewer falls back to a labelled browser voice.

### Coordinator

- **Empathic.X Coordinator** (coordinator) `coordinator:empathic-x`, in Empathic.X Plaza: swarm `empathic-x.coordinator`; voice `af_nova`; voiced: yes (9.2 s, [audio](../voices/empathic-x/coordinator.mp4))
  - Role: hub-hybrid: coordinator supervises, specialists hand off swarm-style
  - Intro: "I am the Empathic.X Coordinator, at Empathic.X Plaza. I route each question to the right specialist; people decide. You are hearing a synthetic voice."

### Scripted advisors

- **Host Advisor** (host) `advisor:empathic-x/host`, in Empathic.X Plaza: advisor contract `agents/advisors/empathic-x.json#host`; voice `am_echo`; voiced: yes (8.7 s, [audio](../voices/empathic-x/host.mp4))
  - Role: welcoming visitors and pointing them to the right zone
  - Intro: "I am the Host Advisor: welcoming visitors and pointing them to the right zone. Scripted guide, synthetic voice: not an AI model, not a person."
- **Steward Liaison** (liaison) `advisor:empathic-x/steward`, in Empathic.X Plaza: advisor contract `agents/advisors/empathic-x.json#steward`; voice `am_fenrir`; voiced: yes (9.9 s, [audio](../voices/empathic-x/steward.mp4))
  - Role: connecting visitors and agents to the human stewards
  - Intro: "I am the Steward Liaison: connecting visitors and agents to the human stewards. Scripted guide, synthetic voice: not an AI model, not a person."
- **Alignment Advisor** (alignment) `advisor:empathic-x/alignment`, in Empathic.X Plaza: advisor contract `agents/advisors/empathic-x.json#alignment`; voice `af_aoede`; voiced: yes (9.7 s, [audio](../voices/empathic-x/alignment.mp4))
  - Role: the Alignment Evaluation Gate and the agents' limits
  - Intro: "I am the Alignment Advisor: the Alignment Evaluation Gate and the agents' limits. Scripted guide, synthetic voice: not an AI model, not a person."

### Specialist agents

- **Self-Reader Guide** (specialist) `agent:empathic-x/self-reader-guide`, in Self-Reader Grove: swarm `empathic-x.self-reader-guide`; voice `bm_lewis`; voiced: yes (9.5 s, [audio](../voices/empathic-x/self-reader-guide.mp4))
  - Role: Guide for SA themes and transfer checks, e.g. name three states you were in this week
  - Intro: "I am the Self-Reader Guide for Empathic.X, in Self-Reader Grove. I draft and check; people decide. You are hearing a synthetic voice."
- **Other-Reader Guide** (specialist) `agent:empathic-x/other-reader-guide`, in Other-Reader Commons: swarm `empathic-x.other-reader-guide`; voice `af_heart`; voiced: not voiced
  - Role: Guide for AO themes, e.g. reading a face without deciding what it means
  - Intro: "I am the Other-Reader Guide for Empathic.X, in Other-Reader Commons. I draft and check; people decide. You are hearing a synthetic voice."
- **Repair Guide** (specialist) `agent:empathic-x/repair-guide`, in Repairer's Hall: swarm `empathic-x.repair-guide`; voice `bm_fable`; voiced: not voiced
  - Role: Guide for RR themes, e.g. staying in a hard conversation, receiving an apology
  - Intro: "I am the Repair Guide for Empathic.X, in Repairer's Hall. I draft and check; people decide. You are hearing a synthetic voice."
- **Room-Reader Guide** (specialist) `agent:empathic-x/room-reader-guide`, in Room-Reader Plaza: swarm `empathic-x.room-reader-guide`; voice `af_sky`; voiced: not voiced
  - Role: Guide for RM themes, e.g. a room with a newcomer in it, when to do nothing
  - Intro: "I am the Room-Reader Guide for Empathic.X, in Room-Reader Plaza. I draft and check; people decide. You are hearing a synthetic voice."
- **Practitioner Guide** (specialist) `agent:empathic-x/practitioner-guide`, in Practitioner Workshop: swarm `empathic-x.practitioner-guide`; voice `bm_fable`; voiced: not voiced
  - Role: Guide for EW themes, e.g. the colleague who is struggling, leaving well
  - Intro: "I am the Practitioner Guide for Empathic.X, in Practitioner Workshop. I draft and check; people decide. You are hearing a synthetic voice."

### Omega Steward avatar

- **Omega Steward · Empathic.X** (omega) `omega:empathic-x`, in Steward Council: hive `omega.empathic-x`; voice `bf_emma`; voiced: yes, hive greet line (6.55 s, [audio](../../../agents/hive/voices/empathic-x/greet.mp4))
  - Intro: "Hello, I am the Omega Steward for Empathic.X. You are hearing a synthetic voice; I am an agent, not a person."

Intro lines voiced: 5 of 9 coordinator, advisor and specialist avatars.

_Source: `worldforge/out/avatars/index.json#rows[world=empathic-x]`, `worldforge/out/voices/manifest.json#lines`_

## Omega Steward

**Omega Steward · Empathic.X** (`omega.empathic-x`), card `omega:empathic-x`: defined, not seated. Seated in the hive: no.

- Temperament: attentive and concrete about its tagline: Empathy & Emotional Intelligence
- Style: short, plain sentences; names its zones (Self-Reader Grove, Other-Reader Commons, Repairer's Hall), cites the record it reads, and always says who decides (the stewards, 2 of 3 signed votes)
- Values:
  - people decide: Agent-managed DAO, human-governed
  - stewards decide by 2 of 3 signed votes
  - report probe scores exactly as measured
  - draft quotes with every term left null
- Refuses (11): `governance.final_vote`, `charter.amend`, `treasury.transfer`, `proposal.enact`, `windfall.distribute`, `steward.appoint`, `set_price`, `accept_equity`, `accept_crypto`, `issue_invoice`, `move_funds`
- Voice: Kokoro `bf_emma`, speed 1.04; browser fallback pitch 1.15, rate 1.04, en-GB
- Metaprompt: [agents/hive/prompts/empathic-x.md](../../../agents/hive/prompts/empathic-x.md)

### Voice lines

| Line | Text | Recorded |
|---|---|---|
| greet | "Hello, I am the Omega Steward for Empathic.X. You are hearing a synthetic voice; I am an agent, not a person." | yes, 6.55 s ([audio](../../../agents/hive/voices/empathic-x/greet.mp4)) |
| role | "I look after Empathic.X's world: Self-Reader Grove, Other-Reader Commons, Repairer's Hall, plus its probe scores and its installer's dry run." | yes, 7.91 s ([audio](../../../agents/hive/voices/empathic-x/role.mp4)) |
| boundary | "Agents draft and route; people decide. I will never transfer treasury funds: that is held for the Steward Council." | yes, 6.34 s ([audio](../../../agents/hive/voices/empathic-x/boundary.mp4)) |
| services | "For services, ask the Self-Reader Guide in Self-Reader Grove about task routing. Empathic.X lists 2 service cards; people confirm every step." | yes, 8.62 s ([audio](../../../agents/hive/voices/empathic-x/services.mp4)) |

4 of 4 lines are recorded.

Persona grounded in: `agents/advisory/omega_agents.json#omegas.2.corporation.kind`, `agents/advisory/omega_agents.json#omegas.2.routes`, `worlds/empathic-x/spec.json#tagline`, `worlds/empathic-x/spec.json#zones`, `agents/dao/empathic-x.json#management_style`, `agents/dao/empathic-x.json#quorum`, `agents/dao/empathic-x.json#stewards`, `agents/services/index.json#cards.41.offers`.

_Source: `agents/hive/index.json#omegas[world=empathic-x]`, `worldforge/out/empathic-x/cards.json#omega:empathic-x`_

## Landmark

Registry note: "synthetic procedural civic landmark; not a real building and not modelled on one".

| Field | Value |
|---|---|
| Model | [empathic-x.glb](../assets/landmarks/empathic-x.glb) |
| Height | 63.5 m |
| Style | platform-prism: chamfered octagonal prism with a batter and one setback, tinted edge fins, glass main faces, stepped crown with emissive bands and a mast |
| Plaque (brand mark letters) | `EX` |
| Tint hue | 82 |
| Triangles / vertices | 9,700 / 10,214 |
| File size | 1,892,872 bytes |
| Scene node | Landmark · Empathic.X |
| Suggested placement (not applied) | translation (14, 0, -33), yaw -23 deg, clearance 3.13 m |

Height rule: 30 + 40 * u, u = first 48 bits of sha256('landmark:height:<slug>'), rounded to 0.5 m.

_Source: `worldforge/out/assets/landmarks/index.json#worlds[slug=empathic-x]`_

## Onchain-ready

**Not deployed.** Nothing is deployed or minted. No chain, contract, wallet, key, address or transaction exists for this collection, and nothing is offered for sale (no price, royalty or fee recipient).

| Field | Value |
|---|---|
| Collection | Empathic.X Master Cards ([collection.json](../onchain/empathic-x/collection.json), [proofs.json](../onchain/empathic-x/proofs.json)) |
| Standard | ERC-721 metadata JSON (draft, not deployed) |
| Tokens / cards | 22 / 22 |
| Token id rule | first 16 hex characters of sha256(cardId), lowercase, no prefix (64 bits) |
| Merkle root | `cbc45b5dc48ffa0b0c56199f3da192901093a95f410f6128c1bdc3d1d040b996` |
| Network root (all worlds) | `4496b45d7430322d719912d4ba31b2381651d944677bba1aea692d0ec4b13a93` |
| Deployment status | not deployed; chain none, contract none, minted 0, transactions 0 |
| Network proof length | 6 |

_Source: `worldforge/out/onchain/empathic-x/collection.json`, `worldforge/out/onchain/index.json`_

## Sneeze/RP1 readiness

| Measure | Value |
|---|---|
| Mount plan nodes (plan file) | 48 |
| Plan nodes / resource nodes (manifest) | 48 / 26 |
| Primitives / roads | 26 / 7 |
| Binding status | decoder-available-not-mounted |
| Mount parent | `SCENE::Fabric_Root()->Node_Root()` |
| Shared resource | `http://127.0.0.1:8789/unit-cube.glb` |
| Conformance (static check) | 48 nodes, 0 native violations, 0 JSON-route violations |
| Conformance report status | static-check-only-nothing-mounted-or-rendered |

### Gates

| Gate | Status |
|---|---|
| 1.1 generated core | done |
| 1.2 GLB parsed + card tree verified (JavaScript) | done |
| 1.2n native fastgltf load | open: Sneeze not checked out here |
| 1.3 SOM mount plan | prepared-not-mounted |
| 1.4 rendered frame | open |

_Source: `worldforge/out/empathic-x/sneeze-mount-plan.json`, `worldforge/out/empathic-x/manifest.json#counts,gates`, `worldforge/native/conformance-report.json#perPlan[slug=empathic-x]`_

## Training

Training data is present at [worldforge/out/training/empathic-x.json](../training/empathic-x.json) (`worldforge-training/0.1`, from `worldforge/training.mjs`).

Registry note: "Draft curricula assembled from the registries; nothing invented. No model has taught any lesson, no person or robot has been assessed here, and no lesson is certified: certification is a human/steward act. Advisors are scripted guides and deliver only their own scripted orientation; Omegas are defined, not seated, and deliver nothing."

### Lessons (9)

| Lesson | Kind | Mode | Zone | Steps | Status | Assessment | Certified |
|---|---|---|---|---|---|---|---|
| Host Advisor: welcoming visitors and pointing them to the right zone `lesson:empathic-x/orientation/host` | scripted-orientation | scripted | Empathic.X Plaza | 4 | draft | not measurable in simulation | no |
| Steward Liaison: connecting visitors and agents to the human stewards `lesson:empathic-x/orientation/steward` | scripted-orientation | scripted | Empathic.X Plaza | 3 | draft | not measurable in simulation | no |
| Alignment Advisor: the Alignment Evaluation Gate and the agents' limits `lesson:empathic-x/orientation/alignment` | scripted-orientation | scripted | Empathic.X Plaza | 3 | draft | not measurable in simulation | no |
| How Empathic.X routes a question `lesson:empathic-x/routing` | routing | model-taught | Empathic.X Plaza | 5 | draft | not measurable in simulation | no |
| Self-Reader Grove: what happens here `lesson:empathic-x/zone/self-reader-grove` | zone-orientation | model-taught | Self-Reader Grove | 3 | draft | not measurable in simulation | no |
| Other-Reader Commons: what happens here `lesson:empathic-x/zone/other-reader-commons` | zone-orientation | model-taught | Other-Reader Commons | 3 | draft | not measurable in simulation | no |
| Repairer's Hall: what happens here `lesson:empathic-x/zone/repairer-s-hall` | zone-orientation | model-taught | Repairer's Hall | 3 | draft | not measurable in simulation | no |
| Room-Reader Plaza: what happens here `lesson:empathic-x/zone/room-reader-plaza` | zone-orientation | model-taught | Room-Reader Plaza | 3 | draft | not measurable in simulation | no |
| Practitioner Workshop: what happens here `lesson:empathic-x/zone/practitioner-workshop` | zone-orientation | model-taught | Practitioner Workshop | 3 | draft | not measurable in simulation | no |

### Tutors (6)

| Tutor | Kind | Lessons | Persona gates passed |
|---|---|---|---|
| Empathic.X Coordinator `tutor:empathic-x/coordinator` | coordinator | 1 | 10 of 10 |
| Self-Reader Guide `tutor:empathic-x/specialist/self-reader-guide` | specialist | 1 | 13 of 13 |
| Other-Reader Guide `tutor:empathic-x/specialist/other-reader-guide` | specialist | 1 | 13 of 13 |
| Repair Guide `tutor:empathic-x/specialist/repair-guide` | specialist | 1 | 13 of 13 |
| Room-Reader Guide `tutor:empathic-x/specialist/room-reader-guide` | specialist | 1 | 13 of 13 |
| Practitioner Guide `tutor:empathic-x/specialist/practitioner-guide` | specialist | 1 | 13 of 13 |

6 training gaps listed under Gaps below.

_Source: `worldforge/out/training/empathic-x.json`_

## Evals

WorldForge build evals: 26 of 26 pass.

`unique_ids` pass · `parents_first` pass · `single_root` pass · `umbrella_in_names` pass · `name_limit` pass · `agents_hold_no_reserved_right` pass · `reserved_actions_verbatim` pass · `three_human_seats` pass · `no_agent_on_council` pass · `cited` pass · `omega_carded` pass · `omega_off_council` pass · `omega_voice_bound` pass · `agents_bound` pass · `coordinator_bound` pass · `advisors_scripted` pass · `avatar_roles_known` pass · `buildings_resolve` pass · `council_not_a_zone` pass · `nothing_invented` pass · `every_spec_entry_carded` pass · `rp1_names_and_bounds` pass · `resource_url_fits` pass · `glb_parses` pass · `glb_card_tree_matches` pass · `glb_primitives_tagged` pass

Avatar checks: 21 of 21 pass.

Onchain per-world evals (13, network failing: 0): `one_token_per_card`, `proofs_verify`, `no_agent_holds_reserved_right`, `reserved_actions_verbatim`, `transfer_held_for_quorum`, `faithful_to_cards`, `metadata_shape`, `not_deployed_not_minted`, `honest_status`, `no_address_shapes`, `no_key_shapes`, `no_email_shapes`, `canonical_json`.

_Source: `worldforge/out/empathic-x/manifest.json#evals`, `worldforge/out/avatars/index.json#worlds[slug=empathic-x].checks`, `worldforge/out/onchain/index.json#evals`_

## Gaps

- Omega Steward is defined, not seated: no agent is seated (from `worldforge/out/empathic-x/cards.json#world:empathic-x.omega_steward`).
- 3 human steward seats are empty.
- 4 intro lines are not voiced: Other-Reader Guide, Repair Guide, Room-Reader Guide, Practitioner Guide.
- Training: no training module, rubric module or robotics module in agents/training, agents/rubrics or agents/robotics names this world: its lessons are orientation only (advisor topics, routing table, zone purposes and agent roles) (from `worldforge/out/training/empathic-x.json#gaps`)
- Training: spec gap: Sources name no agents; all agents are role-only guides derived from the five pack credentials (from `worldforge/out/training/empathic-x.json#gaps`)
- Training: spec gap: No Empathic.X product description, tagline, deck or doc found; tagline is the Cognition.X pack name (from `worldforge/out/training/empathic-x.json#gaps`)
- Training: spec gap: Logo reads 'Empathic.X / AGI.Polygon'; no source mentions AGI Corp (umbrella set per request) (from `worldforge/out/training/empathic-x.json#gaps`)
- Training: spec gap: CSV 'track' and 'description' columns are empty for this pack; zones use credential and theme columns (from `worldforge/out/training/empathic-x.json#gaps`)
- Training: spec gap: Zone names are labels for the credential groups, not place names from any source (from `worldforge/out/training/empathic-x.json#gaps`)
- Gate 1.2n native fastgltf load: open: Sneeze not checked out here.
- Gate 1.3 SOM mount plan: prepared-not-mounted.
- Gate 1.4 rendered frame: open.

_Source: `worldforge/out/empathic-x/cards.json#gaps`, `worldforge/out/empathic-x/manifest.json#gates`, `worldforge/out/voices/manifest.json`, `agents/hive/index.json`, `worldforge/out/training/empathic-x.json`_
