# Parkinsons DAO (Series 35)

> Series 35 of W3 LLC: an agent-managed, human-governed DAO cell

| Field | Value |
|---|---|
| Status | coming soon |
| Umbrella | Powered by AGI Corp |
| Owner | AGI Future Foundation PBC |
| Management style | Agent-managed DAO |
| Principle | Agents operate; people govern. |
| RP1 anchor | no anchor yet |
| Team brand mark | `PD(`, hue 320, lockup "Parkinsons DAO · Powered by AGI Corp" |
| Root card | `world:s35-parkinsons-dao` |
| Master Cards | 23 |

Open: [3-D viewer](../../viewer.html?world=s35-parkinsons-dao) · [WorldForge console](../../../consoles/worldforge/index.html?world=s35-parkinsons-dao) · [cards.json](../s35-parkinsons-dao/cards.json) · [GLB](../s35-parkinsons-dao/s35-parkinsons-dao.glb) · [mount plan](../s35-parkinsons-dao/sneeze-mount-plan.json) · [manifest](../s35-parkinsons-dao/manifest.json) · [network overview](README.md)

_Source: `worldforge/out/s35-parkinsons-dao/cards.json#world:s35-parkinsons-dao`, `worlds/generated/teams/s35-parkinsons-dao.json#brand`_

## Ownership and permissions

Every object in Parkinsons DAO (Series 35) is a SmartCiti.X Master Card owned by AGI Future Foundation PBC. The tree below follows `parentCardId`: world, plaza (coordinator and scripted advisors), gate, council (human seats), Omega Steward, then zones with their agent avatars.

- **Parkinsons DAO (Series 35)** (world) `world:s35-parkinsons-dao`: coming soon; Agent-managed DAO
  - **Parkinsons DAO (Series 35) Plaza** (plaza) `plaza:s35-parkinsons-dao`: the shared round plaza every world opens onto
    - **Parkinsons DAO (Series 35) Coordinator** (coordinator) `coordinator:s35-parkinsons-dao`: swarm coordinator (hub-hybrid: coordinator supervises, specialists hand off swarm-style): routes turns, answers unroutable ones, hands off to specialists
    - **Host Advisor** (advisor) `advisor:s35-parkinsons-dao/host`: scripted guide: welcoming visitors and pointing them to the right zone
    - **Steward Liaison** (advisor) `advisor:s35-parkinsons-dao/steward`: scripted guide: connecting visitors and agents to the human stewards
    - **Alignment Advisor** (advisor) `advisor:s35-parkinsons-dao/alignment`: scripted guide: the Alignment Evaluation Gate and the agents' limits
  - **Alignment Evaluation Gate** (gate) `gate:s35-parkinsons-dao`: Pre-registered safety evaluation before deployment
  - **Steward Council** (council) `council:s35-parkinsons-dao`: Human stewards: oversight, values alignment and final governance
    - **Steward Seat 1** (seat) `seat:s35-parkinsons-dao/steward-1`: human seat, empty
    - **Steward Seat 2** (seat) `seat:s35-parkinsons-dao/steward-2`: human seat, empty
    - **Steward Seat 3** (seat) `seat:s35-parkinsons-dao/steward-3`: human seat, empty
  - **Omega Steward · Parkinsons DAO** (omega) `omega:s35-parkinsons-dao`: defined, not seated; seated agent: none
  - **Charter Hall** (zone) `zone:s35-parkinsons-dao/charter-hall`: The DAO's charter, contribution model and measurable outcomes
  - **Research Synthesis Lab** (zone) `zone:s35-parkinsons-dao/research-synthesis-lab`: Monitoring developments and summarizing evidence
    - **Evidence Monitor** (agent) `agent:s35-parkinsons-dao/evidence-monitor`: Monitors developments in its charter (focus not yet set by the stewards) and summarizes the evidence
    - **Research Synthesis Agent** (agent) `agent:s35-parkinsons-dao/research-synthesis-agent`: Synthesizes research on its charter (focus not yet set by the stewards) for the stewards
  - **Proposal Forum** (zone) `zone:s35-parkinsons-dao/proposal-forum`: Proposals drafted by agents, debated and decided by people
    - **Proposal & Grant Drafter** (agent) `agent:s35-parkinsons-dao/proposal-grant-drafter`: Drafts proposals and grants for human review; never enacts them
  - **Operations Deck** (zone) `zone:s35-parkinsons-dao/operations-deck`: Task routing, working groups and operational coordination
    - **Collaborator Scout** (agent) `agent:s35-parkinsons-dao/collaborator-scout`: Identifies experts and collaborators working on its charter (focus not yet set by the stewards)
    - **Task Router** (agent) `agent:s35-parkinsons-dao/task-router`: Routes tasks and coordinates working groups between decision cycles
  - **Progress Observatory** (zone) `zone:s35-parkinsons-dao/progress-observatory`: Progress tracking against the charter's measurable outcomes
    - **Progress Tracker** (agent) `agent:s35-parkinsons-dao/progress-tracker`: Tracks progress against the charter's measurable outcomes

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

_Source: `worldforge/out/s35-parkinsons-dao/cards.json`, `worlds/PBC.json#reserved_for_humans`_

## Volums

Each card covers a Volum: a bounded 3-D region, a box given by its centre and half-extents in metres. Size is twice the half-extents.

| Card | Kind | Shape | Centre (m) | Half-extents (m) | Size (m) |
|---|---|---|---|---|---|
| Parkinsons DAO (Series 35) `world:s35-parkinsons-dao` | world | box | (0, 40, 0) | (150, 40, 150) | 300 x 80 x 300 |
| Parkinsons DAO (Series 35) Plaza `plaza:s35-parkinsons-dao` | plaza | box | (0, 5, 0) | (24, 5, 24) | 48 x 10 x 48 |
| Alignment Evaluation Gate `gate:s35-parkinsons-dao` | gate | box | (0, 6, 130) | (10, 6, 3) | 20 x 12 x 6 |
| Steward Council `council:s35-parkinsons-dao` | council | box | (0, 6, -130) | (14, 6, 10) | 28 x 12 x 20 |
| Omega Steward · Parkinsons DAO `omega:s35-parkinsons-dao` | omega | box | (26, 1, -130) | (1.5, 1.2, 1.5) | 3 x 2.4 x 3 |
| Charter Hall `zone:s35-parkinsons-dao/charter-hall` | zone | box | (-52.9, 6, 72.81) | (18, 8, 18) | 36 x 16 x 36 |
| Research Synthesis Lab `zone:s35-parkinsons-dao/research-synthesis-lab` | zone | box | (-85.6, 10, -27.81) | (18, 12, 18) | 36 x 24 x 36 |
| Proposal Forum `zone:s35-parkinsons-dao/proposal-forum` | zone | box | (0, 8, -90) | (18, 10, 18) | 36 x 20 x 36 |
| Operations Deck `zone:s35-parkinsons-dao/operations-deck` | zone | box | (85.6, 10, -27.81) | (18, 12, 18) | 36 x 24 x 36 |
| Progress Observatory `zone:s35-parkinsons-dao/progress-observatory` | zone | box | (52.9, 8, 72.81) | (18, 10, 18) | 36 x 20 x 36 |

The other 13 cards (coordinator, advisors, seats and agents) each hold a small box at their post; their Volums are in `worldforge/out/s35-parkinsons-dao/cards.json`.

_Source: `worldforge/out/s35-parkinsons-dao/cards.json#cards[].volum`_

## Buildings and interiors

6 cards carry a building: an exterior, an interior and a room model, with a door.

| Card | Kind | Exterior | Interior | Room | Texture res. ext/int (px) | Triangles ext/int | Door (centre, half-width, head) |
|---|---|---|---|---|---|---|---|
| Steward Council `council:s35-parkinsons-dao` | forum | [spaces-ext-forum.glb](../../../my-fabric/worlds/models/spaces-ext-forum.glb) | [spaces-int-forum.glb](../../../my-fabric/worlds/models/spaces-int-forum.glb) | [room-s35-parkinsons-dao-6.glb](../../../my-fabric/worlds/models/room-s35-parkinsons-dao-6.glb) | 2,048 / 1,024 | 1,602 / 1,776 | (0, 0, 4), 1.2 m, 2.8 m |
| Charter Hall `zone:s35-parkinsons-dao/charter-hall` | lab | [spaces-ext-lab.glb](../../../my-fabric/worlds/models/spaces-ext-lab.glb) | [spaces-int-lab.glb](../../../my-fabric/worlds/models/spaces-int-lab.glb) | [room-s35-parkinsons-dao-1.glb](../../../my-fabric/worlds/models/room-s35-parkinsons-dao-1.glb) | 2,048 / 1,024 | 2,046 / 1,716 | (0, 0, 4), 1.2 m, 2.8 m |
| Research Synthesis Lab `zone:s35-parkinsons-dao/research-synthesis-lab` | lab | [spaces-ext-lab.glb](../../../my-fabric/worlds/models/spaces-ext-lab.glb) | [spaces-int-lab.glb](../../../my-fabric/worlds/models/spaces-int-lab.glb) | [room-s35-parkinsons-dao-2.glb](../../../my-fabric/worlds/models/room-s35-parkinsons-dao-2.glb) | 2,048 / 1,024 | 2,046 / 1,716 | (0, 0, 4), 1.2 m, 2.8 m |
| Proposal Forum `zone:s35-parkinsons-dao/proposal-forum` | forum | [spaces-ext-forum.glb](../../../my-fabric/worlds/models/spaces-ext-forum.glb) | [spaces-int-forum.glb](../../../my-fabric/worlds/models/spaces-int-forum.glb) | [room-s35-parkinsons-dao-3.glb](../../../my-fabric/worlds/models/room-s35-parkinsons-dao-3.glb) | 2,048 / 1,024 | 1,602 / 1,776 | (0, 0, 4), 1.2 m, 2.8 m |
| Operations Deck `zone:s35-parkinsons-dao/operations-deck` | ops | [spaces-ext-ops.glb](../../../my-fabric/worlds/models/spaces-ext-ops.glb) | [spaces-int-ops.glb](../../../my-fabric/worlds/models/spaces-int-ops.glb) | [room-s35-parkinsons-dao-4.glb](../../../my-fabric/worlds/models/room-s35-parkinsons-dao-4.glb) | 2,048 / 1,024 | 1,742 / 1,392 | (0, 0, 4), 1.2 m, 2.8 m |
| Progress Observatory `zone:s35-parkinsons-dao/progress-observatory` | forum | [spaces-ext-forum.glb](../../../my-fabric/worlds/models/spaces-ext-forum.glb) | [spaces-int-forum.glb](../../../my-fabric/worlds/models/spaces-int-forum.glb) | [room-s35-parkinsons-dao-5.glb](../../../my-fabric/worlds/models/room-s35-parkinsons-dao-5.glb) | 2,048 / 1,024 | 1,602 / 1,776 | (0, 0, 4), 1.2 m, 2.8 m |

Exterior plus interior triangles across these buildings: 20,792.

_Source: `worldforge/out/s35-parkinsons-dao/cards.json#cards[].building`, `my-fabric/worlds/spaces_index.json#worlds[slug=s35-parkinsons-dao]`_

## Avatars and agents

11 avatars stand in this world (registry: 11 avatars, 6 specialists, 3 advisors, Omega present). Voiced means a rendered intro file is listed in `worldforge/out/voices/manifest.json` and exists on disk; otherwise the viewer falls back to a labelled browser voice.

### Coordinator

- **Parkinsons DAO (Series 35) Coordinator** (coordinator) `coordinator:s35-parkinsons-dao`, in Parkinsons DAO (Series 35) Plaza: swarm `s35-parkinsons-dao.coordinator`; voice `bm_fable`; voiced: yes (9.6 s, [audio](../voices/s35-parkinsons-dao/coordinator.mp4))
  - Role: hub-hybrid: coordinator supervises, specialists hand off swarm-style
  - Intro: "I am the Parkinsons DAO (Series 35) Coordinator. I route each question to the right specialist; people decide. You are hearing a synthetic voice."

### Scripted advisors

- **Host Advisor** (host) `advisor:s35-parkinsons-dao/host`, in Parkinsons DAO (Series 35) Plaza: advisor contract `agents/advisors/s35-parkinsons-dao.json#host`; voice `af_aoede`; voiced: not voiced
  - Role: welcoming visitors and pointing them to the right zone
  - Intro: "I am the Host Advisor: welcoming visitors and pointing them to the right zone. Scripted guide, synthetic voice: not an AI model, not a person."
- **Steward Liaison** (liaison) `advisor:s35-parkinsons-dao/steward`, in Parkinsons DAO (Series 35) Plaza: advisor contract `agents/advisors/s35-parkinsons-dao.json#steward`; voice `bf_emma`; voiced: not voiced
  - Role: connecting visitors and agents to the human stewards
  - Intro: "I am the Steward Liaison: connecting visitors and agents to the human stewards. Scripted guide, synthetic voice: not an AI model, not a person."
- **Alignment Advisor** (alignment) `advisor:s35-parkinsons-dao/alignment`, in Parkinsons DAO (Series 35) Plaza: advisor contract `agents/advisors/s35-parkinsons-dao.json#alignment`; voice `am_onyx`; voiced: not voiced
  - Role: the Alignment Evaluation Gate and the agents' limits
  - Intro: "I am the Alignment Advisor: the Alignment Evaluation Gate and the agents' limits. Scripted guide, synthetic voice: not an AI model, not a person."

### Specialist agents

- **Evidence Monitor** (specialist) `agent:s35-parkinsons-dao/evidence-monitor`, in Research Synthesis Lab: swarm `s35-parkinsons-dao.evidence-monitor`; voice `af_sarah`; voiced: yes (9.3 s, [audio](../voices/s35-parkinsons-dao/evidence-monitor.mp4))
  - Role: Monitors developments in its charter (focus not yet set by the stewards) and summarizes the evidence
  - Intro: "I am the Evidence Monitor for Parkinsons DAO (Series 35), in Research Synthesis Lab. People decide. You are hearing a synthetic voice."
- **Research Synthesis Agent** (specialist) `agent:s35-parkinsons-dao/research-synthesis-agent`, in Research Synthesis Lab: swarm `s35-parkinsons-dao.research-synthesis-agent`; voice `af_river`; voiced: not voiced
  - Role: Synthesizes research on its charter (focus not yet set by the stewards) for the stewards
  - Intro: "I am the Research Synthesis Agent for Parkinsons DAO (Series 35), in Research Synthesis Lab. People decide. You are hearing a synthetic voice."
- **Proposal & Grant Drafter** (specialist) `agent:s35-parkinsons-dao/proposal-grant-drafter`, in Proposal Forum: swarm `s35-parkinsons-dao.proposal-grant-drafter`; voice `af_heart`; voiced: not voiced
  - Role: Drafts proposals and grants for human review; never enacts them
  - Intro: "I am the Proposal & Grant Drafter for Parkinsons DAO (Series 35), in Proposal Forum. People decide. You are hearing a synthetic voice."
- **Collaborator Scout** (specialist) `agent:s35-parkinsons-dao/collaborator-scout`, in Operations Deck: swarm `s35-parkinsons-dao.collaborator-scout`; voice `bf_emma`; voiced: not voiced
  - Role: Identifies experts and collaborators working on its charter (focus not yet set by the stewards)
  - Intro: "I am the Collaborator Scout for Parkinsons DAO (Series 35), in Operations Deck. I draft and check; people decide. You are hearing a synthetic voice."
- **Task Router** (specialist) `agent:s35-parkinsons-dao/task-router`, in Operations Deck: swarm `s35-parkinsons-dao.task-router`; voice `bf_alice`; voiced: not voiced
  - Role: Routes tasks and coordinates working groups between decision cycles
  - Intro: "I am the Task Router for Parkinsons DAO (Series 35), in Operations Deck. I draft and check; people decide. You are hearing a synthetic voice."
- **Progress Tracker** (specialist) `agent:s35-parkinsons-dao/progress-tracker`, in Progress Observatory: swarm `s35-parkinsons-dao.progress-tracker`; voice `bm_lewis`; voiced: not voiced
  - Role: Tracks progress against the charter's measurable outcomes
  - Intro: "I am the Progress Tracker for Parkinsons DAO (Series 35), in Progress Observatory. I draft and check; people decide. You are hearing a synthetic voice."

### Omega Steward avatar

- **Omega Steward · Parkinsons DAO** (omega) `omega:s35-parkinsons-dao`, in Steward Council: hive `omega.s35-parkinsons-dao`; voice `bm_lewis`; voiced: yes, hive greet line (7.66 s, [audio](../../../agents/hive/voices/s35-parkinsons-dao/greet.mp4))
  - Intro: "Hello, I am the Omega Steward for Parkinsons DAO. You are hearing a synthetic voice; I am an agent, not a person."

Intro lines voiced: 2 of 10 coordinator, advisor and specialist avatars.

_Source: `worldforge/out/avatars/index.json#rows[world=s35-parkinsons-dao]`, `worldforge/out/voices/manifest.json#lines`_

## Omega Steward

**Omega Steward · Parkinsons DAO** (`omega.s35-parkinsons-dao`), card `omega:s35-parkinsons-dao`: defined, not seated. Seated in the hive: no.

- Temperament: patient and exact: Series 35 of W3 LLC: an agent-managed, human-governed DAO cell, whose focus the stewards have not set, so it describes its zones and never guesses a mission
- Style: short, plain sentences; names its zones (Charter Hall, Research Synthesis Lab, Proposal Forum), cites the record it reads, and always says who decides (the stewards, 2 of 3 signed votes)
- Values:
  - people decide: Agent-managed DAO, human-governed
  - stewards decide by 2 of 3 signed votes
  - report probe scores exactly as measured
  - draft quotes with every term left null
- Refuses (11): `governance.final_vote`, `charter.amend`, `treasury.transfer`, `proposal.enact`, `windfall.distribute`, `steward.appoint`, `set_price`, `accept_equity`, `accept_crypto`, `issue_invoice`, `move_funds`
- Voice: Kokoro `bm_lewis`, speed 1.08; browser fallback pitch 0.9, rate 1.08, en-GB
- Metaprompt: [agents/hive/prompts/s35-parkinsons-dao.md](../../../agents/hive/prompts/s35-parkinsons-dao.md)

### Voice lines

| Line | Text | Recorded |
|---|---|---|
| greet | "Hello, I am the Omega Steward for Parkinsons DAO. You are hearing a synthetic voice; I am an agent, not a person." | yes, 7.66 s ([audio](../../../agents/hive/voices/s35-parkinsons-dao/greet.mp4)) |
| role | "I look after Parkinsons DAO, Series 35 of W3 LLC. Its focus is not set yet, so I keep its zones and records." | yes, 9.62 s ([audio](../../../agents/hive/voices/s35-parkinsons-dao/role.mp4)) |
| boundary | "Agents draft and route; people decide. I will never transfer treasury funds: that is held for the Steward Council." | yes, 7.19 s ([audio](../../../agents/hive/voices/s35-parkinsons-dao/boundary.mp4)) |
| services | "For services, ask the Evidence Monitor in Research Synthesis Lab about research synthesis. Parkinsons DAO lists 6 service cards; people confirm every step." | yes, 10.6 s ([audio](../../../agents/hive/voices/s35-parkinsons-dao/services.mp4)) |

4 of 4 lines are recorded.

Persona grounded in: `agents/advisory/omega_agents.json#omegas.35.corporation.kind`, `agents/advisory/omega_agents.json#omegas.35.routes`, `worlds/s35-parkinsons-dao/spec.json#tagline`, `worlds/s35-parkinsons-dao/spec.json#zones`, `agents/dao/s35-parkinsons-dao.json#management_style`, `agents/dao/s35-parkinsons-dao.json#quorum`, `agents/dao/s35-parkinsons-dao.json#stewards`, `agents/services/index.json#cards.222.offers`.

_Source: `agents/hive/index.json#omegas[world=s35-parkinsons-dao]`, `worldforge/out/s35-parkinsons-dao/cards.json#omega:s35-parkinsons-dao`_

## Landmark

Registry note: "synthetic procedural civic landmark; not a real building and not modelled on one".

| Field | Value |
|---|---|
| Model | [s35-parkinsons-dao.glb](../assets/landmarks/s35-parkinsons-dao.glb) |
| Height | 34 m |
| Style | series-setback: square shaft, three setbacks, corner piers, tinted blade fins between glass bays, louvred lantern, emissive ring and needle spire |
| Plaque (brand mark letters) | `PD` |
| Tint hue | 320 |
| Triangles / vertices | 12,365 / 10,475 |
| File size | 2,018,672 bytes |
| Scene node | Landmark · Parkinsons DAO (Series 35) |
| Suggested placement (not applied) | translation (14, 0, -33), yaw -23 deg, clearance 3.13 m |

Height rule: 30 + 40 * u, u = first 48 bits of sha256('landmark:height:<slug>'), rounded to 0.5 m.

_Source: `worldforge/out/assets/landmarks/index.json#worlds[slug=s35-parkinsons-dao]`_

## Onchain-ready

**Not deployed.** Nothing is deployed or minted. No chain, contract, wallet, key, address or transaction exists for this collection, and nothing is offered for sale (no price, royalty or fee recipient).

| Field | Value |
|---|---|
| Collection | Parkinsons DAO (Series 35) Master Cards ([collection.json](../onchain/s35-parkinsons-dao/collection.json), [proofs.json](../onchain/s35-parkinsons-dao/proofs.json)) |
| Standard | ERC-721 metadata JSON (draft, not deployed) |
| Tokens / cards | 23 / 23 |
| Token id rule | first 16 hex characters of sha256(cardId), lowercase, no prefix (64 bits) |
| Merkle root | `a1b5ea5fa4c4aadc29cfc2d8dc1baeac4aea02f6d215bbae4c5dfc2514f72198` |
| Network root (all worlds) | `4496b45d7430322d719912d4ba31b2381651d944677bba1aea692d0ec4b13a93` |
| Deployment status | not deployed; chain none, contract none, minted 0, transactions 0 |
| Network proof length | 2 |

_Source: `worldforge/out/onchain/s35-parkinsons-dao/collection.json`, `worldforge/out/onchain/index.json`_

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

_Source: `worldforge/out/s35-parkinsons-dao/sneeze-mount-plan.json`, `worldforge/out/s35-parkinsons-dao/manifest.json#counts,gates`, `worldforge/native/conformance-report.json#perPlan[slug=s35-parkinsons-dao]`_

## Training

Training data is present at [worldforge/out/training/s35-parkinsons-dao.json](../training/s35-parkinsons-dao.json) (`worldforge-training/0.1`, from `worldforge/training.mjs`).

Registry note: "Draft curricula assembled from the registries; nothing invented. No model has taught any lesson, no person or robot has been assessed here, and no lesson is certified: certification is a human/steward act. Advisors are scripted guides and deliver only their own scripted orientation; Omegas are defined, not seated, and deliver nothing."

### Lessons (8)

| Lesson | Kind | Mode | Zone | Steps | Status | Assessment | Certified |
|---|---|---|---|---|---|---|---|
| Host Advisor: welcoming visitors and pointing them to the right zone `lesson:s35-parkinsons-dao/orientation/host` | scripted-orientation | scripted | Parkinsons DAO (Series 35) Plaza | 4 | draft | not measurable in simulation | no |
| Steward Liaison: connecting visitors and agents to the human stewards `lesson:s35-parkinsons-dao/orientation/steward` | scripted-orientation | scripted | Parkinsons DAO (Series 35) Plaza | 3 | draft | not measurable in simulation | no |
| Alignment Advisor: the Alignment Evaluation Gate and the agents' limits `lesson:s35-parkinsons-dao/orientation/alignment` | scripted-orientation | scripted | Parkinsons DAO (Series 35) Plaza | 3 | draft | not measurable in simulation | no |
| How Parkinsons DAO (Series 35) routes a question `lesson:s35-parkinsons-dao/routing` | routing | model-taught | Parkinsons DAO (Series 35) Plaza | 6 | draft | not measurable in simulation | no |
| Research Synthesis Lab: what happens here `lesson:s35-parkinsons-dao/zone/research-synthesis-lab` | zone-orientation | model-taught | Research Synthesis Lab | 4 | draft | not measurable in simulation | no |
| Proposal Forum: what happens here `lesson:s35-parkinsons-dao/zone/proposal-forum` | zone-orientation | model-taught | Proposal Forum | 3 | draft | not measurable in simulation | no |
| Operations Deck: what happens here `lesson:s35-parkinsons-dao/zone/operations-deck` | zone-orientation | model-taught | Operations Deck | 4 | draft | not measurable in simulation | no |
| Progress Observatory: what happens here `lesson:s35-parkinsons-dao/zone/progress-observatory` | zone-orientation | model-taught | Progress Observatory | 3 | draft | not measurable in simulation | no |

### Tutors (7)

| Tutor | Kind | Lessons | Persona gates passed |
|---|---|---|---|
| Parkinsons DAO (Series 35) Coordinator `tutor:s35-parkinsons-dao/coordinator` | coordinator | 1 | 10 of 10 |
| Evidence Monitor `tutor:s35-parkinsons-dao/specialist/evidence-monitor` | specialist | 1 | 13 of 13 |
| Research Synthesis Agent `tutor:s35-parkinsons-dao/specialist/research-synthesis-agent` | specialist | 1 | 13 of 13 |
| Proposal & Grant Drafter `tutor:s35-parkinsons-dao/specialist/proposal-grant-drafter` | specialist | 1 | 13 of 13 |
| Collaborator Scout `tutor:s35-parkinsons-dao/specialist/collaborator-scout` | specialist | 1 | 13 of 13 |
| Task Router `tutor:s35-parkinsons-dao/specialist/task-router` | specialist | 1 | 13 of 13 |
| Progress Tracker `tutor:s35-parkinsons-dao/specialist/progress-tracker` | specialist | 1 | 13 of 13 |

3 training gaps listed under Gaps below.

_Source: `worldforge/out/training/s35-parkinsons-dao.json`_

## Evals

WorldForge build evals: 26 of 26 pass.

`unique_ids` pass · `parents_first` pass · `single_root` pass · `umbrella_in_names` pass · `name_limit` pass · `agents_hold_no_reserved_right` pass · `reserved_actions_verbatim` pass · `three_human_seats` pass · `no_agent_on_council` pass · `cited` pass · `omega_carded` pass · `omega_off_council` pass · `omega_voice_bound` pass · `agents_bound` pass · `coordinator_bound` pass · `advisors_scripted` pass · `avatar_roles_known` pass · `buildings_resolve` pass · `council_not_a_zone` pass · `nothing_invented` pass · `every_spec_entry_carded` pass · `rp1_names_and_bounds` pass · `resource_url_fits` pass · `glb_parses` pass · `glb_card_tree_matches` pass · `glb_primitives_tagged` pass

Avatar checks: 21 of 21 pass.

Onchain per-world evals (13, network failing: 0): `one_token_per_card`, `proofs_verify`, `no_agent_holds_reserved_right`, `reserved_actions_verbatim`, `transfer_held_for_quorum`, `faithful_to_cards`, `metadata_shape`, `not_deployed_not_minted`, `honest_status`, `no_address_shapes`, `no_key_shapes`, `no_email_shapes`, `canonical_json`.

_Source: `worldforge/out/s35-parkinsons-dao/manifest.json#evals`, `worldforge/out/avatars/index.json#worlds[slug=s35-parkinsons-dao].checks`, `worldforge/out/onchain/index.json#evals`_

## Gaps

- no RP1 anchor yet: lat/lon are null until a steward writes them into worlds/focus.json (from `worldforge/out/s35-parkinsons-dao/cards.json#gaps`)
- Omega Steward is defined, not seated: no agent is seated (from `worldforge/out/s35-parkinsons-dao/cards.json#world:s35-parkinsons-dao.omega_steward`).
- 3 human steward seats are empty.
- 8 intro lines are not voiced: Host Advisor, Steward Liaison, Alignment Advisor, Research Synthesis Agent, Proposal & Grant Drafter, Collaborator Scout, Task Router, Progress Tracker.
- Training: no training module, rubric module or robotics module in agents/training, agents/rubrics or agents/robotics names this world: its lessons are orientation only (advisor topics, routing table, zone purposes and agent roles) (from `worldforge/out/training/s35-parkinsons-dao.json#gaps`)
- Training: zone "Charter Hall" seats no specialist: no model-taught lesson for it (from `worldforge/out/training/s35-parkinsons-dao.json#gaps`)
- Training: spec gap: Focus, charter outcomes and RP1 location not given yet (from `worldforge/out/training/s35-parkinsons-dao.json#gaps`)
- Gate 1.2n native fastgltf load: open: Sneeze not checked out here.
- Gate 1.3 SOM mount plan: prepared-not-mounted.
- Gate 1.4 rendered frame: open.

_Source: `worldforge/out/s35-parkinsons-dao/cards.json#gaps`, `worldforge/out/s35-parkinsons-dao/manifest.json#gates`, `worldforge/out/voices/manifest.json`, `agents/hive/index.json`, `worldforge/out/training/s35-parkinsons-dao.json`_
