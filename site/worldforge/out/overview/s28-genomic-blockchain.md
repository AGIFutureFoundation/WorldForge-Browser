# Genomic.Blockchain (Series 28)

> Series 28 of W3 LLC: an agent-managed, human-governed DAO cell

| Field | Value |
|---|---|
| Status | coming soon |
| Umbrella | Powered by AGI Corp |
| Owner | AGI Future Foundation PBC |
| Management style | Agent-managed DAO |
| Principle | Agents operate; people govern. |
| RP1 anchor | no anchor yet |
| Team brand mark | `GB(`, hue 256, lockup "Genomic.Blockchain · Powered by AGI Corp" |
| Root card | `world:s28-genomic-blockchain` |
| Master Cards | 23 |

Open: [3-D viewer](../../viewer.html?world=s28-genomic-blockchain) · [WorldForge console](../../../consoles/worldforge/index.html?world=s28-genomic-blockchain) · [cards.json](../s28-genomic-blockchain/cards.json) · [GLB](../s28-genomic-blockchain/s28-genomic-blockchain.glb) · [mount plan](../s28-genomic-blockchain/sneeze-mount-plan.json) · [manifest](../s28-genomic-blockchain/manifest.json) · [network overview](README.md)

_Source: `worldforge/out/s28-genomic-blockchain/cards.json#world:s28-genomic-blockchain`, `worlds/generated/teams/s28-genomic-blockchain.json#brand`_

## Ownership and permissions

Every object in Genomic.Blockchain (Series 28) is a SmartCiti.X Master Card owned by AGI Future Foundation PBC. The tree below follows `parentCardId`: world, plaza (coordinator and scripted advisors), gate, council (human seats), Omega Steward, then zones with their agent avatars.

- **Genomic.Blockchain (Series 28)** (world) `world:s28-genomic-blockchain`: coming soon; Agent-managed DAO
  - **Genomic.Blockchain (Series 28) Plaza** (plaza) `plaza:s28-genomic-blockchain`: the shared round plaza every world opens onto
    - **Genomic.Blockchain (Series 28) Coordinator** (coordinator) `coordinator:s28-genomic-blockchain`: swarm coordinator (hub-hybrid: coordinator supervises, specialists hand off swarm-style): routes turns, answers unroutable ones, hands off to specialists
    - **Host Advisor** (advisor) `advisor:s28-genomic-blockchain/host`: scripted guide: welcoming visitors and pointing them to the right zone
    - **Steward Liaison** (advisor) `advisor:s28-genomic-blockchain/steward`: scripted guide: connecting visitors and agents to the human stewards
    - **Alignment Advisor** (advisor) `advisor:s28-genomic-blockchain/alignment`: scripted guide: the Alignment Evaluation Gate and the agents' limits
  - **Alignment Evaluation Gate** (gate) `gate:s28-genomic-blockchain`: Pre-registered safety evaluation before deployment
  - **Steward Council** (council) `council:s28-genomic-blockchain`: Human stewards: oversight, values alignment and final governance
    - **Steward Seat 1** (seat) `seat:s28-genomic-blockchain/steward-1`: human seat, empty
    - **Steward Seat 2** (seat) `seat:s28-genomic-blockchain/steward-2`: human seat, empty
    - **Steward Seat 3** (seat) `seat:s28-genomic-blockchain/steward-3`: human seat, empty
  - **Omega Steward · Genomic.Blockchain** (omega) `omega:s28-genomic-blockchain`: defined, not seated; seated agent: none
  - **Charter Hall** (zone) `zone:s28-genomic-blockchain/charter-hall`: The DAO's charter, contribution model and measurable outcomes
  - **Research Synthesis Lab** (zone) `zone:s28-genomic-blockchain/research-synthesis-lab`: Monitoring developments and summarizing evidence
    - **Evidence Monitor** (agent) `agent:s28-genomic-blockchain/evidence-monitor`: Monitors developments in its charter (focus not yet set by the stewards) and summarizes the evidence
    - **Research Synthesis Agent** (agent) `agent:s28-genomic-blockchain/research-synthesis-agent`: Synthesizes research on its charter (focus not yet set by the stewards) for the stewards
  - **Proposal Forum** (zone) `zone:s28-genomic-blockchain/proposal-forum`: Proposals drafted by agents, debated and decided by people
    - **Proposal & Grant Drafter** (agent) `agent:s28-genomic-blockchain/proposal-grant-drafter`: Drafts proposals and grants for human review; never enacts them
  - **Operations Deck** (zone) `zone:s28-genomic-blockchain/operations-deck`: Task routing, working groups and operational coordination
    - **Collaborator Scout** (agent) `agent:s28-genomic-blockchain/collaborator-scout`: Identifies experts and collaborators working on its charter (focus not yet set by the stewards)
    - **Task Router** (agent) `agent:s28-genomic-blockchain/task-router`: Routes tasks and coordinates working groups between decision cycles
  - **Progress Observatory** (zone) `zone:s28-genomic-blockchain/progress-observatory`: Progress tracking against the charter's measurable outcomes
    - **Progress Tracker** (agent) `agent:s28-genomic-blockchain/progress-tracker`: Tracks progress against the charter's measurable outcomes

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

_Source: `worldforge/out/s28-genomic-blockchain/cards.json`, `worlds/PBC.json#reserved_for_humans`_

## Volums

Each card covers a Volum: a bounded 3-D region, a box given by its centre and half-extents in metres. Size is twice the half-extents.

| Card | Kind | Shape | Centre (m) | Half-extents (m) | Size (m) |
|---|---|---|---|---|---|
| Genomic.Blockchain (Series 28) `world:s28-genomic-blockchain` | world | box | (0, 40, 0) | (150, 40, 150) | 300 x 80 x 300 |
| Genomic.Blockchain (Series 28) Plaza `plaza:s28-genomic-blockchain` | plaza | box | (0, 5, 0) | (24, 5, 24) | 48 x 10 x 48 |
| Alignment Evaluation Gate `gate:s28-genomic-blockchain` | gate | box | (0, 6, 130) | (10, 6, 3) | 20 x 12 x 6 |
| Steward Council `council:s28-genomic-blockchain` | council | box | (0, 6, -130) | (14, 6, 10) | 28 x 12 x 20 |
| Omega Steward · Genomic.Blockchain `omega:s28-genomic-blockchain` | omega | box | (26, 1, -130) | (1.5, 1.2, 1.5) | 3 x 2.4 x 3 |
| Charter Hall `zone:s28-genomic-blockchain/charter-hall` | zone | box | (-52.9, 6, 72.81) | (18, 8, 18) | 36 x 16 x 36 |
| Research Synthesis Lab `zone:s28-genomic-blockchain/research-synthesis-lab` | zone | box | (-85.6, 10, -27.81) | (18, 12, 18) | 36 x 24 x 36 |
| Proposal Forum `zone:s28-genomic-blockchain/proposal-forum` | zone | box | (0, 8, -90) | (18, 10, 18) | 36 x 20 x 36 |
| Operations Deck `zone:s28-genomic-blockchain/operations-deck` | zone | box | (85.6, 10, -27.81) | (18, 12, 18) | 36 x 24 x 36 |
| Progress Observatory `zone:s28-genomic-blockchain/progress-observatory` | zone | box | (52.9, 8, 72.81) | (18, 10, 18) | 36 x 20 x 36 |

The other 13 cards (coordinator, advisors, seats and agents) each hold a small box at their post; their Volums are in `worldforge/out/s28-genomic-blockchain/cards.json`.

_Source: `worldforge/out/s28-genomic-blockchain/cards.json#cards[].volum`_

## Buildings and interiors

6 cards carry a building: an exterior, an interior and a room model, with a door.

| Card | Kind | Exterior | Interior | Room | Texture res. ext/int (px) | Triangles ext/int | Door (centre, half-width, head) |
|---|---|---|---|---|---|---|---|
| Steward Council `council:s28-genomic-blockchain` | forum | [spaces-ext-forum.glb](../../../my-fabric/worlds/models/spaces-ext-forum.glb) | [spaces-int-forum.glb](../../../my-fabric/worlds/models/spaces-int-forum.glb) | [room-s28-genomic-blockchain-6.glb](../../../my-fabric/worlds/models/room-s28-genomic-blockchain-6.glb) | 2,048 / 1,024 | 1,602 / 1,776 | (0, 0, 4), 1.2 m, 2.8 m |
| Charter Hall `zone:s28-genomic-blockchain/charter-hall` | lab | [spaces-ext-lab.glb](../../../my-fabric/worlds/models/spaces-ext-lab.glb) | [spaces-int-lab.glb](../../../my-fabric/worlds/models/spaces-int-lab.glb) | [room-s28-genomic-blockchain-1.glb](../../../my-fabric/worlds/models/room-s28-genomic-blockchain-1.glb) | 2,048 / 1,024 | 2,046 / 1,716 | (0, 0, 4), 1.2 m, 2.8 m |
| Research Synthesis Lab `zone:s28-genomic-blockchain/research-synthesis-lab` | lab | [spaces-ext-lab.glb](../../../my-fabric/worlds/models/spaces-ext-lab.glb) | [spaces-int-lab.glb](../../../my-fabric/worlds/models/spaces-int-lab.glb) | [room-s28-genomic-blockchain-2.glb](../../../my-fabric/worlds/models/room-s28-genomic-blockchain-2.glb) | 2,048 / 1,024 | 2,046 / 1,716 | (0, 0, 4), 1.2 m, 2.8 m |
| Proposal Forum `zone:s28-genomic-blockchain/proposal-forum` | forum | [spaces-ext-forum.glb](../../../my-fabric/worlds/models/spaces-ext-forum.glb) | [spaces-int-forum.glb](../../../my-fabric/worlds/models/spaces-int-forum.glb) | [room-s28-genomic-blockchain-3.glb](../../../my-fabric/worlds/models/room-s28-genomic-blockchain-3.glb) | 2,048 / 1,024 | 1,602 / 1,776 | (0, 0, 4), 1.2 m, 2.8 m |
| Operations Deck `zone:s28-genomic-blockchain/operations-deck` | ops | [spaces-ext-ops.glb](../../../my-fabric/worlds/models/spaces-ext-ops.glb) | [spaces-int-ops.glb](../../../my-fabric/worlds/models/spaces-int-ops.glb) | [room-s28-genomic-blockchain-4.glb](../../../my-fabric/worlds/models/room-s28-genomic-blockchain-4.glb) | 2,048 / 1,024 | 1,742 / 1,392 | (0, 0, 4), 1.2 m, 2.8 m |
| Progress Observatory `zone:s28-genomic-blockchain/progress-observatory` | forum | [spaces-ext-forum.glb](../../../my-fabric/worlds/models/spaces-ext-forum.glb) | [spaces-int-forum.glb](../../../my-fabric/worlds/models/spaces-int-forum.glb) | [room-s28-genomic-blockchain-5.glb](../../../my-fabric/worlds/models/room-s28-genomic-blockchain-5.glb) | 2,048 / 1,024 | 1,602 / 1,776 | (0, 0, 4), 1.2 m, 2.8 m |

Exterior plus interior triangles across these buildings: 20,792.

_Source: `worldforge/out/s28-genomic-blockchain/cards.json#cards[].building`, `my-fabric/worlds/spaces_index.json#worlds[slug=s28-genomic-blockchain]`_

## Avatars and agents

11 avatars stand in this world (registry: 11 avatars, 6 specialists, 3 advisors, Omega present). Voiced means a rendered intro file is listed in `worldforge/out/voices/manifest.json` and exists on disk; otherwise the viewer falls back to a labelled browser voice.

### Coordinator

- **Genomic.Blockchain (Series 28) Coordinator** (coordinator) `coordinator:s28-genomic-blockchain`, in Genomic.Blockchain (Series 28) Plaza: swarm `s28-genomic-blockchain.coordinator`; voice `am_echo`; voiced: yes (9.1 s, [audio](../voices/s28-genomic-blockchain/coordinator.mp4))
  - Role: hub-hybrid: coordinator supervises, specialists hand off swarm-style
  - Intro: "I am the Genomic.Blockchain (Series 28) Coordinator. I route each question to the right specialist; people decide. You are hearing a synthetic voice."

### Scripted advisors

- **Host Advisor** (host) `advisor:s28-genomic-blockchain/host`, in Genomic.Blockchain (Series 28) Plaza: advisor contract `agents/advisors/s28-genomic-blockchain.json#host`; voice `bf_lily`; voiced: not voiced
  - Role: welcoming visitors and pointing them to the right zone
  - Intro: "I am the Host Advisor: welcoming visitors and pointing them to the right zone. Scripted guide, synthetic voice: not an AI model, not a person."
- **Steward Liaison** (liaison) `advisor:s28-genomic-blockchain/steward`, in Genomic.Blockchain (Series 28) Plaza: advisor contract `agents/advisors/s28-genomic-blockchain.json#steward`; voice `am_puck`; voiced: not voiced
  - Role: connecting visitors and agents to the human stewards
  - Intro: "I am the Steward Liaison: connecting visitors and agents to the human stewards. Scripted guide, synthetic voice: not an AI model, not a person."
- **Alignment Advisor** (alignment) `advisor:s28-genomic-blockchain/alignment`, in Genomic.Blockchain (Series 28) Plaza: advisor contract `agents/advisors/s28-genomic-blockchain.json#alignment`; voice `af_sarah`; voiced: not voiced
  - Role: the Alignment Evaluation Gate and the agents' limits
  - Intro: "I am the Alignment Advisor: the Alignment Evaluation Gate and the agents' limits. Scripted guide, synthetic voice: not an AI model, not a person."

### Specialist agents

- **Evidence Monitor** (specialist) `agent:s28-genomic-blockchain/evidence-monitor`, in Research Synthesis Lab: swarm `s28-genomic-blockchain.evidence-monitor`; voice `af_nicole`; voiced: yes (16.6 s, [audio](../voices/s28-genomic-blockchain/evidence-monitor.mp4))
  - Role: Monitors developments in its charter (focus not yet set by the stewards) and summarizes the evidence
  - Intro: "I am the Evidence Monitor for Genomic.Blockchain (Series 28), in Research Synthesis Lab. I draft and check; people decide. You are hearing a synthetic voice."
- **Research Synthesis Agent** (specialist) `agent:s28-genomic-blockchain/research-synthesis-agent`, in Research Synthesis Lab: swarm `s28-genomic-blockchain.research-synthesis-agent`; voice `bm_daniel`; voiced: not voiced
  - Role: Synthesizes research on its charter (focus not yet set by the stewards) for the stewards
  - Intro: "I am the Research Synthesis Agent for Genomic.Blockchain (Series 28), in Research Synthesis Lab. People decide. You are hearing a synthetic voice."
- **Proposal & Grant Drafter** (specialist) `agent:s28-genomic-blockchain/proposal-grant-drafter`, in Proposal Forum: swarm `s28-genomic-blockchain.proposal-grant-drafter`; voice `af_heart`; voiced: not voiced
  - Role: Drafts proposals and grants for human review; never enacts them
  - Intro: "I am the Proposal & Grant Drafter for Genomic.Blockchain (Series 28), in Proposal Forum. People decide. You are hearing a synthetic voice."
- **Collaborator Scout** (specialist) `agent:s28-genomic-blockchain/collaborator-scout`, in Operations Deck: swarm `s28-genomic-blockchain.collaborator-scout`; voice `am_echo`; voiced: not voiced
  - Role: Identifies experts and collaborators working on its charter (focus not yet set by the stewards)
  - Intro: "I am the Collaborator Scout for Genomic.Blockchain (Series 28), in Operations Deck. I draft and check; people decide. You are hearing a synthetic voice."
- **Task Router** (specialist) `agent:s28-genomic-blockchain/task-router`, in Operations Deck: swarm `s28-genomic-blockchain.task-router`; voice `bm_lewis`; voiced: not voiced
  - Role: Routes tasks and coordinates working groups between decision cycles
  - Intro: "I am the Task Router for Genomic.Blockchain (Series 28), in Operations Deck. I draft and check; people decide. You are hearing a synthetic voice."
- **Progress Tracker** (specialist) `agent:s28-genomic-blockchain/progress-tracker`, in Progress Observatory: swarm `s28-genomic-blockchain.progress-tracker`; voice `bf_lily`; voiced: not voiced
  - Role: Tracks progress against the charter's measurable outcomes
  - Intro: "I am the Progress Tracker for Genomic.Blockchain (Series 28), in Progress Observatory. I draft and check; people decide. You are hearing a synthetic voice."

### Omega Steward avatar

- **Omega Steward · Genomic.Blockchain** (omega) `omega:s28-genomic-blockchain`, in Steward Council: hive `omega.s28-genomic-blockchain`; voice `af_sky`; voiced: yes, hive greet line (7.15 s, [audio](../../../agents/hive/voices/s28-genomic-blockchain/greet.mp4))
  - Intro: "Hello, I am the Omega Steward for Genomic.Blockchain. You are hearing a synthetic voice; I am an agent, not a person."

Intro lines voiced: 2 of 10 coordinator, advisor and specialist avatars.

_Source: `worldforge/out/avatars/index.json#rows[world=s28-genomic-blockchain]`, `worldforge/out/voices/manifest.json#lines`_

## Omega Steward

**Omega Steward · Genomic.Blockchain** (`omega.s28-genomic-blockchain`), card `omega:s28-genomic-blockchain`: defined, not seated. Seated in the hive: no.

- Temperament: patient and exact: Series 28 of W3 LLC: an agent-managed, human-governed DAO cell, whose focus the stewards have not set, so it describes its zones and never guesses a mission
- Style: short, plain sentences; names its zones (Charter Hall, Research Synthesis Lab, Proposal Forum), cites the record it reads, and always says who decides (the stewards, 2 of 3 signed votes)
- Values:
  - people decide: Agent-managed DAO, human-governed
  - stewards decide by 2 of 3 signed votes
  - report probe scores exactly as measured
  - draft quotes with every term left null
- Refuses (11): `governance.final_vote`, `charter.amend`, `treasury.transfer`, `proposal.enact`, `windfall.distribute`, `steward.appoint`, `set_price`, `accept_equity`, `accept_crypto`, `issue_invoice`, `move_funds`
- Voice: Kokoro `af_sky`, speed 1.04; browser fallback pitch 1.05, rate 1.04, en-US
- Metaprompt: [agents/hive/prompts/s28-genomic-blockchain.md](../../../agents/hive/prompts/s28-genomic-blockchain.md)

### Voice lines

| Line | Text | Recorded |
|---|---|---|
| greet | "Hello, I am the Omega Steward for Genomic.Blockchain. You are hearing a synthetic voice; I am an agent, not a person." | yes, 7.15 s ([audio](../../../agents/hive/voices/s28-genomic-blockchain/greet.mp4)) |
| role | "I look after Genomic.Blockchain, Series 28 of W3 LLC. Its focus is not set yet, so I keep its zones and records." | yes, 8.7 s ([audio](../../../agents/hive/voices/s28-genomic-blockchain/role.mp4)) |
| boundary | "Agents draft and route; people decide. I will never set a price: that is held for the Steward Council." | yes, 5.67 s ([audio](../../../agents/hive/voices/s28-genomic-blockchain/boundary.mp4)) |
| services | "For services, ask the Evidence Monitor in Research Synthesis Lab about research synthesis. Genomic.Blockchain lists 6 service cards; people confirm every step." | yes, 9.96 s ([audio](../../../agents/hive/voices/s28-genomic-blockchain/services.mp4)) |

4 of 4 lines are recorded.

Persona grounded in: `agents/advisory/omega_agents.json#omegas.28.corporation.kind`, `agents/advisory/omega_agents.json#omegas.28.routes`, `worlds/s28-genomic-blockchain/spec.json#tagline`, `worlds/s28-genomic-blockchain/spec.json#zones`, `agents/dao/s28-genomic-blockchain.json#management_style`, `agents/dao/s28-genomic-blockchain.json#quorum`, `agents/dao/s28-genomic-blockchain.json#stewards`, `agents/services/index.json#cards.186.offers`.

_Source: `agents/hive/index.json#omegas[world=s28-genomic-blockchain]`, `worldforge/out/s28-genomic-blockchain/cards.json#omega:s28-genomic-blockchain`_

## Landmark

Registry note: "synthetic procedural civic landmark; not a real building and not modelled on one".

| Field | Value |
|---|---|
| Model | [s28-genomic-blockchain.glb](../assets/landmarks/s28-genomic-blockchain.glb) |
| Height | 31 m |
| Style | series-setback: square shaft, three setbacks, corner piers, tinted blade fins between glass bays, louvred lantern, emissive ring and needle spire |
| Plaque (brand mark letters) | `GB` |
| Tint hue | 256 |
| Triangles / vertices | 8,605 / 8,260 |
| File size | 1,945,156 bytes |
| Scene node | Landmark · Genomic.Blockchain (Series 28) |
| Suggested placement (not applied) | translation (14, 0, -33), yaw -23 deg, clearance 3.13 m |

Height rule: 30 + 40 * u, u = first 48 bits of sha256('landmark:height:<slug>'), rounded to 0.5 m.

_Source: `worldforge/out/assets/landmarks/index.json#worlds[slug=s28-genomic-blockchain]`_

## Onchain-ready

**Not deployed.** Nothing is deployed or minted. No chain, contract, wallet, key, address or transaction exists for this collection, and nothing is offered for sale (no price, royalty or fee recipient).

| Field | Value |
|---|---|
| Collection | Genomic.Blockchain (Series 28) Master Cards ([collection.json](../onchain/s28-genomic-blockchain/collection.json), [proofs.json](../onchain/s28-genomic-blockchain/proofs.json)) |
| Standard | ERC-721 metadata JSON (draft, not deployed) |
| Tokens / cards | 23 / 23 |
| Token id rule | first 16 hex characters of sha256(cardId), lowercase, no prefix (64 bits) |
| Merkle root | `d5ba6ce0008e84bdc8234e79263a15374c94b47a57b904e18e2ab46f0e08d8a0` |
| Network root (all worlds) | `4496b45d7430322d719912d4ba31b2381651d944677bba1aea692d0ec4b13a93` |
| Deployment status | not deployed; chain none, contract none, minted 0, transactions 0 |
| Network proof length | 5 |

_Source: `worldforge/out/onchain/s28-genomic-blockchain/collection.json`, `worldforge/out/onchain/index.json`_

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

_Source: `worldforge/out/s28-genomic-blockchain/sneeze-mount-plan.json`, `worldforge/out/s28-genomic-blockchain/manifest.json#counts,gates`, `worldforge/native/conformance-report.json#perPlan[slug=s28-genomic-blockchain]`_

## Training

Training data is present at [worldforge/out/training/s28-genomic-blockchain.json](../training/s28-genomic-blockchain.json) (`worldforge-training/0.1`, from `worldforge/training.mjs`).

Registry note: "Draft curricula assembled from the registries; nothing invented. No model has taught any lesson, no person or robot has been assessed here, and no lesson is certified: certification is a human/steward act. Advisors are scripted guides and deliver only their own scripted orientation; Omegas are defined, not seated, and deliver nothing."

### Lessons (8)

| Lesson | Kind | Mode | Zone | Steps | Status | Assessment | Certified |
|---|---|---|---|---|---|---|---|
| Host Advisor: welcoming visitors and pointing them to the right zone `lesson:s28-genomic-blockchain/orientation/host` | scripted-orientation | scripted | Genomic.Blockchain (Series 28) Plaza | 4 | draft | not measurable in simulation | no |
| Steward Liaison: connecting visitors and agents to the human stewards `lesson:s28-genomic-blockchain/orientation/steward` | scripted-orientation | scripted | Genomic.Blockchain (Series 28) Plaza | 3 | draft | not measurable in simulation | no |
| Alignment Advisor: the Alignment Evaluation Gate and the agents' limits `lesson:s28-genomic-blockchain/orientation/alignment` | scripted-orientation | scripted | Genomic.Blockchain (Series 28) Plaza | 3 | draft | not measurable in simulation | no |
| How Genomic.Blockchain (Series 28) routes a question `lesson:s28-genomic-blockchain/routing` | routing | model-taught | Genomic.Blockchain (Series 28) Plaza | 6 | draft | not measurable in simulation | no |
| Research Synthesis Lab: what happens here `lesson:s28-genomic-blockchain/zone/research-synthesis-lab` | zone-orientation | model-taught | Research Synthesis Lab | 4 | draft | not measurable in simulation | no |
| Proposal Forum: what happens here `lesson:s28-genomic-blockchain/zone/proposal-forum` | zone-orientation | model-taught | Proposal Forum | 3 | draft | not measurable in simulation | no |
| Operations Deck: what happens here `lesson:s28-genomic-blockchain/zone/operations-deck` | zone-orientation | model-taught | Operations Deck | 4 | draft | not measurable in simulation | no |
| Progress Observatory: what happens here `lesson:s28-genomic-blockchain/zone/progress-observatory` | zone-orientation | model-taught | Progress Observatory | 3 | draft | not measurable in simulation | no |

### Tutors (7)

| Tutor | Kind | Lessons | Persona gates passed |
|---|---|---|---|
| Genomic.Blockchain (Series 28) Coordinator `tutor:s28-genomic-blockchain/coordinator` | coordinator | 1 | 10 of 10 |
| Evidence Monitor `tutor:s28-genomic-blockchain/specialist/evidence-monitor` | specialist | 1 | 13 of 13 |
| Research Synthesis Agent `tutor:s28-genomic-blockchain/specialist/research-synthesis-agent` | specialist | 1 | 13 of 13 |
| Proposal & Grant Drafter `tutor:s28-genomic-blockchain/specialist/proposal-grant-drafter` | specialist | 1 | 13 of 13 |
| Collaborator Scout `tutor:s28-genomic-blockchain/specialist/collaborator-scout` | specialist | 1 | 13 of 13 |
| Task Router `tutor:s28-genomic-blockchain/specialist/task-router` | specialist | 1 | 13 of 13 |
| Progress Tracker `tutor:s28-genomic-blockchain/specialist/progress-tracker` | specialist | 1 | 13 of 13 |

3 training gaps listed under Gaps below.

_Source: `worldforge/out/training/s28-genomic-blockchain.json`_

## Evals

WorldForge build evals: 26 of 26 pass.

`unique_ids` pass · `parents_first` pass · `single_root` pass · `umbrella_in_names` pass · `name_limit` pass · `agents_hold_no_reserved_right` pass · `reserved_actions_verbatim` pass · `three_human_seats` pass · `no_agent_on_council` pass · `cited` pass · `omega_carded` pass · `omega_off_council` pass · `omega_voice_bound` pass · `agents_bound` pass · `coordinator_bound` pass · `advisors_scripted` pass · `avatar_roles_known` pass · `buildings_resolve` pass · `council_not_a_zone` pass · `nothing_invented` pass · `every_spec_entry_carded` pass · `rp1_names_and_bounds` pass · `resource_url_fits` pass · `glb_parses` pass · `glb_card_tree_matches` pass · `glb_primitives_tagged` pass

Avatar checks: 21 of 21 pass.

Onchain per-world evals (13, network failing: 0): `one_token_per_card`, `proofs_verify`, `no_agent_holds_reserved_right`, `reserved_actions_verbatim`, `transfer_held_for_quorum`, `faithful_to_cards`, `metadata_shape`, `not_deployed_not_minted`, `honest_status`, `no_address_shapes`, `no_key_shapes`, `no_email_shapes`, `canonical_json`.

_Source: `worldforge/out/s28-genomic-blockchain/manifest.json#evals`, `worldforge/out/avatars/index.json#worlds[slug=s28-genomic-blockchain].checks`, `worldforge/out/onchain/index.json#evals`_

## Gaps

- no RP1 anchor yet: lat/lon are null until a steward writes them into worlds/focus.json (from `worldforge/out/s28-genomic-blockchain/cards.json#gaps`)
- Omega Steward is defined, not seated: no agent is seated (from `worldforge/out/s28-genomic-blockchain/cards.json#world:s28-genomic-blockchain.omega_steward`).
- 3 human steward seats are empty.
- 8 intro lines are not voiced: Host Advisor, Steward Liaison, Alignment Advisor, Research Synthesis Agent, Proposal & Grant Drafter, Collaborator Scout, Task Router, Progress Tracker.
- Training: no training module, rubric module or robotics module in agents/training, agents/rubrics or agents/robotics names this world: its lessons are orientation only (advisor topics, routing table, zone purposes and agent roles) (from `worldforge/out/training/s28-genomic-blockchain.json#gaps`)
- Training: zone "Charter Hall" seats no specialist: no model-taught lesson for it (from `worldforge/out/training/s28-genomic-blockchain.json#gaps`)
- Training: spec gap: Focus, charter outcomes and RP1 location not given yet (from `worldforge/out/training/s28-genomic-blockchain.json#gaps`)
- Gate 1.2n native fastgltf load: open: Sneeze not checked out here.
- Gate 1.3 SOM mount plan: prepared-not-mounted.
- Gate 1.4 rendered frame: open.

_Source: `worldforge/out/s28-genomic-blockchain/cards.json#gaps`, `worldforge/out/s28-genomic-blockchain/manifest.json#gates`, `worldforge/out/voices/manifest.json`, `agents/hive/index.json`, `worldforge/out/training/s28-genomic-blockchain.json`_
