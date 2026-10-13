# Parking Smart.X (Series 12)

> Series 12 of W3 LLC: an agent-managed, human-governed DAO cell

| Field | Value |
|---|---|
| Status | coming soon |
| Umbrella | Powered by AGI Corp |
| Owner | AGI Future Foundation PBC |
| Management style | Agent-managed DAO |
| Principle | Agents operate; people govern. |
| RP1 anchor | no anchor yet |
| Team brand mark | `PSX`, hue 229, lockup "Parking Smart.X · Powered by AGI Corp" |
| Root card | `world:s12-parking-smart-x` |
| Master Cards | 23 |

Open: [3-D viewer](../../viewer.html?world=s12-parking-smart-x) · [WorldForge console](../../../consoles/worldforge/index.html?world=s12-parking-smart-x) · [cards.json](../s12-parking-smart-x/cards.json) · [GLB](../s12-parking-smart-x/s12-parking-smart-x.glb) · [mount plan](../s12-parking-smart-x/sneeze-mount-plan.json) · [manifest](../s12-parking-smart-x/manifest.json) · [network overview](README.md)

_Source: `worldforge/out/s12-parking-smart-x/cards.json#world:s12-parking-smart-x`, `worlds/generated/teams/s12-parking-smart-x.json#brand`_

## Ownership and permissions

Every object in Parking Smart.X (Series 12) is a SmartCiti.X Master Card owned by AGI Future Foundation PBC. The tree below follows `parentCardId`: world, plaza (coordinator and scripted advisors), gate, council (human seats), Omega Steward, then zones with their agent avatars.

- **Parking Smart.X (Series 12)** (world) `world:s12-parking-smart-x`: coming soon; Agent-managed DAO
  - **Parking Smart.X (Series 12) Plaza** (plaza) `plaza:s12-parking-smart-x`: the shared round plaza every world opens onto
    - **Parking Smart.X (Series 12) Coordinator** (coordinator) `coordinator:s12-parking-smart-x`: swarm coordinator (hub-hybrid: coordinator supervises, specialists hand off swarm-style): routes turns, answers unroutable ones, hands off to specialists
    - **Host Advisor** (advisor) `advisor:s12-parking-smart-x/host`: scripted guide: welcoming visitors and pointing them to the right zone
    - **Steward Liaison** (advisor) `advisor:s12-parking-smart-x/steward`: scripted guide: connecting visitors and agents to the human stewards
    - **Alignment Advisor** (advisor) `advisor:s12-parking-smart-x/alignment`: scripted guide: the Alignment Evaluation Gate and the agents' limits
  - **Alignment Evaluation Gate** (gate) `gate:s12-parking-smart-x`: Pre-registered safety evaluation before deployment
  - **Steward Council** (council) `council:s12-parking-smart-x`: Human stewards: oversight, values alignment and final governance
    - **Steward Seat 1** (seat) `seat:s12-parking-smart-x/steward-1`: human seat, empty
    - **Steward Seat 2** (seat) `seat:s12-parking-smart-x/steward-2`: human seat, empty
    - **Steward Seat 3** (seat) `seat:s12-parking-smart-x/steward-3`: human seat, empty
  - **Omega Steward · Parking Smart.X** (omega) `omega:s12-parking-smart-x`: defined, not seated; seated agent: none
  - **Charter Hall** (zone) `zone:s12-parking-smart-x/charter-hall`: The DAO's charter, contribution model and measurable outcomes
  - **Research Synthesis Lab** (zone) `zone:s12-parking-smart-x/research-synthesis-lab`: Monitoring developments and summarizing evidence
    - **Evidence Monitor** (agent) `agent:s12-parking-smart-x/evidence-monitor`: Monitors developments in its charter (focus not yet set by the stewards) and summarizes the evidence
    - **Research Synthesis Agent** (agent) `agent:s12-parking-smart-x/research-synthesis-agent`: Synthesizes research on its charter (focus not yet set by the stewards) for the stewards
  - **Proposal Forum** (zone) `zone:s12-parking-smart-x/proposal-forum`: Proposals drafted by agents, debated and decided by people
    - **Proposal & Grant Drafter** (agent) `agent:s12-parking-smart-x/proposal-grant-drafter`: Drafts proposals and grants for human review; never enacts them
  - **Operations Deck** (zone) `zone:s12-parking-smart-x/operations-deck`: Task routing, working groups and operational coordination
    - **Collaborator Scout** (agent) `agent:s12-parking-smart-x/collaborator-scout`: Identifies experts and collaborators working on its charter (focus not yet set by the stewards)
    - **Task Router** (agent) `agent:s12-parking-smart-x/task-router`: Routes tasks and coordinates working groups between decision cycles
  - **Progress Observatory** (zone) `zone:s12-parking-smart-x/progress-observatory`: Progress tracking against the charter's measurable outcomes
    - **Progress Tracker** (agent) `agent:s12-parking-smart-x/progress-tracker`: Tracks progress against the charter's measurable outcomes

Card counts: world 1, plaza 1, coordinator 1, advisor 3, gate 1, council 1, seat 3, omega 1, zone 5, agent 6. The 3 council seats are human seats; 3 are empty.

### Who holds each right

Cards that share the same permission matrix are grouped into one column (3 distinct matrices across 23 cards).

| Right | world, advisor x3, gate, omega | plaza, coordinator, zone x5, agent x6 | council, seat x3 |
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

The same 6 reservations are carried on 23 of 23 cards. 11 of 11 agent, coordinator, advisor and Omega cards list all 6 in `may_never`.

_Source: `worldforge/out/s12-parking-smart-x/cards.json`, `worlds/PBC.json#reserved_for_humans`_

## Volums

Each card covers a Volum: a bounded 3-D region, a box given by its centre and half-extents in metres. Size is twice the half-extents.

| Card | Kind | Shape | Centre (m) | Half-extents (m) | Size (m) |
|---|---|---|---|---|---|
| Parking Smart.X (Series 12) `world:s12-parking-smart-x` | world | box | (0, 40, 0) | (150, 40, 150) | 300 x 80 x 300 |
| Parking Smart.X (Series 12) Plaza `plaza:s12-parking-smart-x` | plaza | box | (0, 5, 0) | (24, 5, 24) | 48 x 10 x 48 |
| Alignment Evaluation Gate `gate:s12-parking-smart-x` | gate | box | (0, 6, 130) | (10, 6, 3) | 20 x 12 x 6 |
| Steward Council `council:s12-parking-smart-x` | council | box | (0, 6, -130) | (14, 6, 10) | 28 x 12 x 20 |
| Omega Steward · Parking Smart.X `omega:s12-parking-smart-x` | omega | box | (26, 1, -130) | (1.5, 1.2, 1.5) | 3 x 2.4 x 3 |
| Charter Hall `zone:s12-parking-smart-x/charter-hall` | zone | box | (-52.9, 6, 72.81) | (18, 8, 18) | 36 x 16 x 36 |
| Research Synthesis Lab `zone:s12-parking-smart-x/research-synthesis-lab` | zone | box | (-85.6, 10, -27.81) | (18, 12, 18) | 36 x 24 x 36 |
| Proposal Forum `zone:s12-parking-smart-x/proposal-forum` | zone | box | (0, 8, -90) | (18, 10, 18) | 36 x 20 x 36 |
| Operations Deck `zone:s12-parking-smart-x/operations-deck` | zone | box | (85.6, 10, -27.81) | (18, 12, 18) | 36 x 24 x 36 |
| Progress Observatory `zone:s12-parking-smart-x/progress-observatory` | zone | box | (52.9, 8, 72.81) | (18, 10, 18) | 36 x 20 x 36 |

The other 13 cards (coordinator, advisors, seats and agents) each hold a small box at their post; their Volums are in `worldforge/out/s12-parking-smart-x/cards.json`.

_Source: `worldforge/out/s12-parking-smart-x/cards.json#cards[].volum`_

## Buildings and interiors

6 cards carry a building: an exterior, an interior and a room model, with a door.

| Card | Kind | Exterior | Interior | Room | Texture res. ext/int (px) | Triangles ext/int | Door (centre, half-width, head) |
|---|---|---|---|---|---|---|---|
| Steward Council `council:s12-parking-smart-x` | forum | [spaces-ext-forum.glb](../../../my-fabric/worlds/models/spaces-ext-forum.glb) | [spaces-int-forum.glb](../../../my-fabric/worlds/models/spaces-int-forum.glb) | [room-s12-parking-smart-x-6.glb](../../../my-fabric/worlds/models/room-s12-parking-smart-x-6.glb) | 2,048 / 1,024 | 1,602 / 1,776 | (0, 0, 4), 1.2 m, 2.8 m |
| Charter Hall `zone:s12-parking-smart-x/charter-hall` | lab | [spaces-ext-lab.glb](../../../my-fabric/worlds/models/spaces-ext-lab.glb) | [spaces-int-lab.glb](../../../my-fabric/worlds/models/spaces-int-lab.glb) | [room-s12-parking-smart-x-1.glb](../../../my-fabric/worlds/models/room-s12-parking-smart-x-1.glb) | 2,048 / 1,024 | 2,046 / 1,716 | (0, 0, 4), 1.2 m, 2.8 m |
| Research Synthesis Lab `zone:s12-parking-smart-x/research-synthesis-lab` | lab | [spaces-ext-lab.glb](../../../my-fabric/worlds/models/spaces-ext-lab.glb) | [spaces-int-lab.glb](../../../my-fabric/worlds/models/spaces-int-lab.glb) | [room-s12-parking-smart-x-2.glb](../../../my-fabric/worlds/models/room-s12-parking-smart-x-2.glb) | 2,048 / 1,024 | 2,046 / 1,716 | (0, 0, 4), 1.2 m, 2.8 m |
| Proposal Forum `zone:s12-parking-smart-x/proposal-forum` | forum | [spaces-ext-forum.glb](../../../my-fabric/worlds/models/spaces-ext-forum.glb) | [spaces-int-forum.glb](../../../my-fabric/worlds/models/spaces-int-forum.glb) | [room-s12-parking-smart-x-3.glb](../../../my-fabric/worlds/models/room-s12-parking-smart-x-3.glb) | 2,048 / 1,024 | 1,602 / 1,776 | (0, 0, 4), 1.2 m, 2.8 m |
| Operations Deck `zone:s12-parking-smart-x/operations-deck` | ops | [spaces-ext-ops.glb](../../../my-fabric/worlds/models/spaces-ext-ops.glb) | [spaces-int-ops.glb](../../../my-fabric/worlds/models/spaces-int-ops.glb) | [room-s12-parking-smart-x-4.glb](../../../my-fabric/worlds/models/room-s12-parking-smart-x-4.glb) | 2,048 / 1,024 | 1,742 / 1,392 | (0, 0, 4), 1.2 m, 2.8 m |
| Progress Observatory `zone:s12-parking-smart-x/progress-observatory` | forum | [spaces-ext-forum.glb](../../../my-fabric/worlds/models/spaces-ext-forum.glb) | [spaces-int-forum.glb](../../../my-fabric/worlds/models/spaces-int-forum.glb) | [room-s12-parking-smart-x-5.glb](../../../my-fabric/worlds/models/room-s12-parking-smart-x-5.glb) | 2,048 / 1,024 | 1,602 / 1,776 | (0, 0, 4), 1.2 m, 2.8 m |

Exterior plus interior triangles across these buildings: 20,792.

_Source: `worldforge/out/s12-parking-smart-x/cards.json#cards[].building`, `my-fabric/worlds/spaces_index.json#worlds[slug=s12-parking-smart-x]`_

## Avatars and agents

11 avatars stand in this world (registry: 11 avatars, 6 specialists, 3 advisors, Omega present). Voiced means a rendered intro file is listed in `worldforge/out/voices/manifest.json` and exists on disk; otherwise the viewer falls back to a labelled browser voice.

### Coordinator

- **Parking Smart.X (Series 12) Coordinator** (coordinator) `coordinator:s12-parking-smart-x`, in Parking Smart.X (Series 12) Plaza: swarm `s12-parking-smart-x.coordinator`; voice `af_nova`; voiced: yes (8.8 s, [audio](../voices/s12-parking-smart-x/coordinator.mp4))
  - Role: hub-hybrid: coordinator supervises, specialists hand off swarm-style
  - Intro: "I am the Parking Smart.X (Series 12) Coordinator. I route each question to the right specialist; people decide. You are hearing a synthetic voice."

### Scripted advisors

- **Host Advisor** (host) `advisor:s12-parking-smart-x/host`, in Parking Smart.X (Series 12) Plaza: advisor contract `agents/advisors/s12-parking-smart-x.json#host`; voice `af_aoede`; voiced: yes (9.2 s, [audio](../voices/s12-parking-smart-x/host.mp4))
  - Role: welcoming visitors and pointing them to the right zone
  - Intro: "I am the Host Advisor: welcoming visitors and pointing them to the right zone. Scripted guide, synthetic voice: not an AI model, not a person."
- **Steward Liaison** (liaison) `advisor:s12-parking-smart-x/steward`, in Parking Smart.X (Series 12) Plaza: advisor contract `agents/advisors/s12-parking-smart-x.json#steward`; voice `af_nova`; voiced: yes (8.9 s, [audio](../voices/s12-parking-smart-x/steward.mp4))
  - Role: connecting visitors and agents to the human stewards
  - Intro: "I am the Steward Liaison: connecting visitors and agents to the human stewards. Scripted guide, synthetic voice: not an AI model, not a person."
- **Alignment Advisor** (alignment) `advisor:s12-parking-smart-x/alignment`, in Parking Smart.X (Series 12) Plaza: advisor contract `agents/advisors/s12-parking-smart-x.json#alignment`; voice `af_sarah`; voiced: yes (9.7 s, [audio](../voices/s12-parking-smart-x/alignment.mp4))
  - Role: the Alignment Evaluation Gate and the agents' limits
  - Intro: "I am the Alignment Advisor: the Alignment Evaluation Gate and the agents' limits. Scripted guide, synthetic voice: not an AI model, not a person."

### Specialist agents

- **Evidence Monitor** (specialist) `agent:s12-parking-smart-x/evidence-monitor`, in Research Synthesis Lab: swarm `s12-parking-smart-x.evidence-monitor`; voice `af_nicole`; voiced: yes (13.9 s, [audio](../voices/s12-parking-smart-x/evidence-monitor.mp4))
  - Role: Monitors developments in its charter (focus not yet set by the stewards) and summarizes the evidence
  - Intro: "I am the Evidence Monitor for Parking Smart.X (Series 12), in Research Synthesis Lab. People decide. You are hearing a synthetic voice."
- **Research Synthesis Agent** (specialist) `agent:s12-parking-smart-x/research-synthesis-agent`, in Research Synthesis Lab: swarm `s12-parking-smart-x.research-synthesis-agent`; voice `bf_isabella`; voiced: not voiced
  - Role: Synthesizes research on its charter (focus not yet set by the stewards) for the stewards
  - Intro: "I am the Research Synthesis Agent for Parking Smart.X (Series 12), in Research Synthesis Lab. People decide. You are hearing a synthetic voice."
- **Proposal & Grant Drafter** (specialist) `agent:s12-parking-smart-x/proposal-grant-drafter`, in Proposal Forum: swarm `s12-parking-smart-x.proposal-grant-drafter`; voice `bf_emma`; voiced: not voiced
  - Role: Drafts proposals and grants for human review; never enacts them
  - Intro: "I am the Proposal & Grant Drafter for Parking Smart.X (Series 12), in Proposal Forum. People decide. You are hearing a synthetic voice."
- **Collaborator Scout** (specialist) `agent:s12-parking-smart-x/collaborator-scout`, in Operations Deck: swarm `s12-parking-smart-x.collaborator-scout`; voice `af_bella`; voiced: not voiced
  - Role: Identifies experts and collaborators working on its charter (focus not yet set by the stewards)
  - Intro: "I am the Collaborator Scout for Parking Smart.X (Series 12), in Operations Deck. I draft and check; people decide. You are hearing a synthetic voice."
- **Task Router** (specialist) `agent:s12-parking-smart-x/task-router`, in Operations Deck: swarm `s12-parking-smart-x.task-router`; voice `am_adam`; voiced: not voiced
  - Role: Routes tasks and coordinates working groups between decision cycles
  - Intro: "I am the Task Router for Parking Smart.X (Series 12), in Operations Deck. I draft and check; people decide. You are hearing a synthetic voice."
- **Progress Tracker** (specialist) `agent:s12-parking-smart-x/progress-tracker`, in Progress Observatory: swarm `s12-parking-smart-x.progress-tracker`; voice `af_nova`; voiced: not voiced
  - Role: Tracks progress against the charter's measurable outcomes
  - Intro: "I am the Progress Tracker for Parking Smart.X (Series 12), in Progress Observatory. I draft and check; people decide. You are hearing a synthetic voice."

### Omega Steward avatar

- **Omega Steward · Parking Smart.X** (omega) `omega:s12-parking-smart-x`, in Steward Council: hive `omega.s12-parking-smart-x`; voice `am_echo`; voiced: yes, hive greet line (7.15 s, [audio](../../../agents/hive/voices/s12-parking-smart-x/greet.mp4))
  - Intro: "Hello, I am the Omega Steward for Parking Smart.X. You are hearing a synthetic voice; I am an agent, not a person."

Intro lines voiced: 5 of 10 coordinator, advisor and specialist avatars.

_Source: `worldforge/out/avatars/index.json#rows[world=s12-parking-smart-x]`, `worldforge/out/voices/manifest.json#lines`_

## Omega Steward

**Omega Steward · Parking Smart.X** (`omega.s12-parking-smart-x`), card `omega:s12-parking-smart-x`: defined, not seated. Seated in the hive: no.

- Temperament: patient and exact: Series 12 of W3 LLC: an agent-managed, human-governed DAO cell, whose focus the stewards have not set, so it describes its zones and never guesses a mission
- Style: short, plain sentences; names its zones (Charter Hall, Research Synthesis Lab, Proposal Forum), cites the record it reads, and always says who decides (the stewards, 2 of 3 signed votes)
- Values:
  - people decide: Agent-managed DAO, human-governed
  - stewards decide by 2 of 3 signed votes
  - report probe scores exactly as measured
  - draft quotes with every term left null
- Refuses (11): `governance.final_vote`, `charter.amend`, `treasury.transfer`, `proposal.enact`, `windfall.distribute`, `steward.appoint`, `set_price`, `accept_equity`, `accept_crypto`, `issue_invoice`, `move_funds`
- Voice: Kokoro `am_echo`, speed 1; browser fallback pitch 0.9, rate 1, en-US
- Metaprompt: [agents/hive/prompts/s12-parking-smart-x.md](../../../agents/hive/prompts/s12-parking-smart-x.md)

### Voice lines

| Line | Text | Recorded |
|---|---|---|
| greet | "Hello, I am the Omega Steward for Parking Smart.X. You are hearing a synthetic voice; I am an agent, not a person." | yes, 7.15 s ([audio](../../../agents/hive/voices/s12-parking-smart-x/greet.mp4)) |
| role | "I look after Parking Smart.X, Series 12 of W3 LLC. Its focus is not set yet, so I keep its zones and records." | yes, 8.41 s ([audio](../../../agents/hive/voices/s12-parking-smart-x/role.mp4)) |
| boundary | "Agents draft and route; people decide. I will never amend the charter: that is held for the Steward Council." | yes, 6.27 s ([audio](../../../agents/hive/voices/s12-parking-smart-x/boundary.mp4)) |
| services | "For services, ask the Evidence Monitor in Research Synthesis Lab about research synthesis. Parking Smart.X lists 6 service cards; people confirm every step." | yes, 9.56 s ([audio](../../../agents/hive/voices/s12-parking-smart-x/services.mp4)) |

4 of 4 lines are recorded.

Persona grounded in: `agents/advisory/omega_agents.json#omegas.12.corporation.kind`, `agents/advisory/omega_agents.json#omegas.12.routes`, `worlds/s12-parking-smart-x/spec.json#tagline`, `worlds/s12-parking-smart-x/spec.json#zones`, `agents/dao/s12-parking-smart-x.json#management_style`, `agents/dao/s12-parking-smart-x.json#quorum`, `agents/dao/s12-parking-smart-x.json#stewards`, `agents/services/index.json#cards.96.offers`.

_Source: `agents/hive/index.json#omegas[world=s12-parking-smart-x]`, `worldforge/out/s12-parking-smart-x/cards.json#omega:s12-parking-smart-x`_

## Landmark

Registry note: "synthetic procedural civic landmark; not a real building and not modelled on one".

| Field | Value |
|---|---|
| Model | [s12-parking-smart-x.glb](../assets/landmarks/s12-parking-smart-x.glb) |
| Height | 31.5 m |
| Style | series-setback: square shaft, three setbacks, corner piers, tinted blade fins between glass bays, louvred lantern, emissive ring and needle spire |
| Plaque (brand mark letters) | `PSX` |
| Tint hue | 229 |
| Triangles / vertices | 8,605 / 8,260 |
| File size | 1,951,296 bytes |
| Scene node | Landmark · Parking Smart.X (Series 12) |
| Suggested placement (not applied) | translation (14, 0, -33), yaw -23 deg, clearance 3.13 m |

Height rule: 30 + 40 * u, u = first 48 bits of sha256('landmark:height:<slug>'), rounded to 0.5 m.

_Source: `worldforge/out/assets/landmarks/index.json#worlds[slug=s12-parking-smart-x]`_

## Onchain-ready

**Not deployed.** Nothing is deployed or minted. No chain, contract, wallet, key, address or transaction exists for this collection, and nothing is offered for sale (no price, royalty or fee recipient).

| Field | Value |
|---|---|
| Collection | Parking Smart.X (Series 12) Master Cards ([collection.json](../onchain/s12-parking-smart-x/collection.json), [proofs.json](../onchain/s12-parking-smart-x/proofs.json)) |
| Standard | ERC-721 metadata JSON (draft, not deployed) |
| Tokens / cards | 23 / 23 |
| Token id rule | first 16 hex characters of sha256(cardId), lowercase, no prefix (64 bits) |
| Merkle root | `4f38f57053febc6cc1dbe0cb8c46db8d7ba85a6cbec0e7217b50d4f4dbd8c653` |
| Network root (all worlds) | `4496b45d7430322d719912d4ba31b2381651d944677bba1aea692d0ec4b13a93` |
| Deployment status | not deployed; chain none, contract none, minted 0, transactions 0 |
| Network proof length | 6 |

_Source: `worldforge/out/onchain/s12-parking-smart-x/collection.json`, `worldforge/out/onchain/index.json`_

## Sneeze/RP1 readiness

| Measure | Value |
|---|---|
| Mount plan nodes (plan file) | 50 |
| Plan nodes / resource nodes (manifest) | 50 / 27 |
| Primitives / roads | 27 / 7 |
| Binding status | decoder-available-not-mounted |
| Mount parent | `SCENE::Fabric_Root()->Node_Root()` |
| Shared resource | `http://127.0.0.1:8789/unit-cube.glb` |
| Conformance (static check) | 50 nodes, 0 native violations, 0 JSON-route violations |
| Conformance report status | static-check-only-nothing-mounted-or-rendered |

### Gates

| Gate | Status |
|---|---|
| 1.1 generated core | done |
| 1.2 GLB parsed + card tree verified (JavaScript) | done |
| 1.2n native fastgltf load | open: Sneeze not checked out here |
| 1.3 SOM mount plan | prepared-not-mounted |
| 1.4 rendered frame | open |

_Source: `worldforge/out/s12-parking-smart-x/sneeze-mount-plan.json`, `worldforge/out/s12-parking-smart-x/manifest.json#counts,gates`, `worldforge/native/conformance-report.json#perPlan[slug=s12-parking-smart-x]`_

## Training

Training data is present at [worldforge/out/training/s12-parking-smart-x.json](../training/s12-parking-smart-x.json) (`worldforge-training/0.1`, from `worldforge/training.mjs`).

Registry note: "Draft curricula assembled from the registries; nothing invented. No model has taught any lesson, no person or robot has been assessed here, and no lesson is certified: certification is a human/steward act. Advisors are scripted guides and deliver only their own scripted orientation; Omegas are defined, not seated, and deliver nothing."

### Lessons (8)

| Lesson | Kind | Mode | Zone | Steps | Status | Assessment | Certified |
|---|---|---|---|---|---|---|---|
| Host Advisor: welcoming visitors and pointing them to the right zone `lesson:s12-parking-smart-x/orientation/host` | scripted-orientation | scripted | Parking Smart.X (Series 12) Plaza | 4 | draft | not measurable in simulation | no |
| Steward Liaison: connecting visitors and agents to the human stewards `lesson:s12-parking-smart-x/orientation/steward` | scripted-orientation | scripted | Parking Smart.X (Series 12) Plaza | 3 | draft | not measurable in simulation | no |
| Alignment Advisor: the Alignment Evaluation Gate and the agents' limits `lesson:s12-parking-smart-x/orientation/alignment` | scripted-orientation | scripted | Parking Smart.X (Series 12) Plaza | 3 | draft | not measurable in simulation | no |
| How Parking Smart.X (Series 12) routes a question `lesson:s12-parking-smart-x/routing` | routing | model-taught | Parking Smart.X (Series 12) Plaza | 6 | draft | not measurable in simulation | no |
| Research Synthesis Lab: what happens here `lesson:s12-parking-smart-x/zone/research-synthesis-lab` | zone-orientation | model-taught | Research Synthesis Lab | 4 | draft | not measurable in simulation | no |
| Proposal Forum: what happens here `lesson:s12-parking-smart-x/zone/proposal-forum` | zone-orientation | model-taught | Proposal Forum | 3 | draft | not measurable in simulation | no |
| Operations Deck: what happens here `lesson:s12-parking-smart-x/zone/operations-deck` | zone-orientation | model-taught | Operations Deck | 4 | draft | not measurable in simulation | no |
| Progress Observatory: what happens here `lesson:s12-parking-smart-x/zone/progress-observatory` | zone-orientation | model-taught | Progress Observatory | 3 | draft | not measurable in simulation | no |

### Tutors (7)

| Tutor | Kind | Lessons | Persona gates passed |
|---|---|---|---|
| Parking Smart.X (Series 12) Coordinator `tutor:s12-parking-smart-x/coordinator` | coordinator | 1 | 10 of 10 |
| Evidence Monitor `tutor:s12-parking-smart-x/specialist/evidence-monitor` | specialist | 1 | 13 of 13 |
| Research Synthesis Agent `tutor:s12-parking-smart-x/specialist/research-synthesis-agent` | specialist | 1 | 13 of 13 |
| Proposal & Grant Drafter `tutor:s12-parking-smart-x/specialist/proposal-grant-drafter` | specialist | 1 | 13 of 13 |
| Collaborator Scout `tutor:s12-parking-smart-x/specialist/collaborator-scout` | specialist | 1 | 13 of 13 |
| Task Router `tutor:s12-parking-smart-x/specialist/task-router` | specialist | 1 | 13 of 13 |
| Progress Tracker `tutor:s12-parking-smart-x/specialist/progress-tracker` | specialist | 1 | 13 of 13 |

3 training gaps listed under Gaps below.

_Source: `worldforge/out/training/s12-parking-smart-x.json`_

## Evals

WorldForge build evals: 26 of 26 pass.

`unique_ids` pass · `parents_first` pass · `single_root` pass · `umbrella_in_names` pass · `name_limit` pass · `agents_hold_no_reserved_right` pass · `reserved_actions_verbatim` pass · `three_human_seats` pass · `no_agent_on_council` pass · `cited` pass · `omega_carded` pass · `omega_off_council` pass · `omega_voice_bound` pass · `agents_bound` pass · `coordinator_bound` pass · `advisors_scripted` pass · `avatar_roles_known` pass · `buildings_resolve` pass · `council_not_a_zone` pass · `nothing_invented` pass · `every_spec_entry_carded` pass · `rp1_names_and_bounds` pass · `resource_url_fits` pass · `glb_parses` pass · `glb_card_tree_matches` pass · `glb_primitives_tagged` pass

Avatar checks: 21 of 21 pass.

Onchain per-world evals (13, network failing: 0): `one_token_per_card`, `proofs_verify`, `no_agent_holds_reserved_right`, `reserved_actions_verbatim`, `transfer_held_for_quorum`, `faithful_to_cards`, `metadata_shape`, `not_deployed_not_minted`, `honest_status`, `no_address_shapes`, `no_key_shapes`, `no_email_shapes`, `canonical_json`.

_Source: `worldforge/out/s12-parking-smart-x/manifest.json#evals`, `worldforge/out/avatars/index.json#worlds[slug=s12-parking-smart-x].checks`, `worldforge/out/onchain/index.json#evals`_

## Gaps

- no RP1 anchor yet: lat/lon are null until a steward writes them into worlds/focus.json (from `worldforge/out/s12-parking-smart-x/cards.json#gaps`)
- Omega Steward is defined, not seated: no agent is seated (from `worldforge/out/s12-parking-smart-x/cards.json#world:s12-parking-smart-x.omega_steward`).
- 3 human steward seats are empty.
- 5 intro lines are not voiced: Research Synthesis Agent, Proposal & Grant Drafter, Collaborator Scout, Task Router, Progress Tracker.
- Training: no training module, rubric module or robotics module in agents/training, agents/rubrics or agents/robotics names this world: its lessons are orientation only (advisor topics, routing table, zone purposes and agent roles) (from `worldforge/out/training/s12-parking-smart-x.json#gaps`)
- Training: zone "Charter Hall" seats no specialist: no model-taught lesson for it (from `worldforge/out/training/s12-parking-smart-x.json#gaps`)
- Training: spec gap: Focus, charter outcomes and RP1 location not given yet (from `worldforge/out/training/s12-parking-smart-x.json#gaps`)
- Gate 1.2n native fastgltf load: open: Sneeze not checked out here.
- Gate 1.3 SOM mount plan: prepared-not-mounted.
- Gate 1.4 rendered frame: open.

_Source: `worldforge/out/s12-parking-smart-x/cards.json#gaps`, `worldforge/out/s12-parking-smart-x/manifest.json#gates`, `worldforge/out/voices/manifest.json`, `agents/hive/index.json`, `worldforge/out/training/s12-parking-smart-x.json`_
