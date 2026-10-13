# Agents That Deploy Infrastructure

> Agents that take software from an idea to something running in production - provisioning, deploying, configuring and operating the stack

| Field | Value |
|---|---|
| Status | coming soon |
| Umbrella | Powered by AGI Corp |
| Owner | AGI Future Foundation PBC |
| Management style | Agent-managed DAO |
| Principle | Agents operate; people govern. |
| RP1 anchor | no anchor yet |
| Team brand mark | `ATD`, hue 283, lockup "Agents That Deploy Infrastructure · Powered by AGI Corp" |
| Root card | `world:agents-deploy-infrastructure` |
| Master Cards | 24 |

Open: [3-D viewer](../../viewer.html?world=agents-deploy-infrastructure) · [WorldForge console](../../../consoles/worldforge/index.html?world=agents-deploy-infrastructure) · [cards.json](../agents-deploy-infrastructure/cards.json) · [GLB](../agents-deploy-infrastructure/agents-deploy-infrastructure.glb) · [mount plan](../agents-deploy-infrastructure/sneeze-mount-plan.json) · [manifest](../agents-deploy-infrastructure/manifest.json) · [network overview](README.md)

_Source: `worldforge/out/agents-deploy-infrastructure/cards.json#world:agents-deploy-infrastructure`, `worlds/generated/teams/agents-deploy-infrastructure.json#brand`_

## Ownership and permissions

Every object in Agents That Deploy Infrastructure is a SmartCiti.X Master Card owned by AGI Future Foundation PBC. The tree below follows `parentCardId`: world, plaza (coordinator and scripted advisors), gate, council (human seats), Omega Steward, then zones with their agent avatars.

- **Agents That Deploy Infrastructure** (world) `world:agents-deploy-infrastructure`: coming soon; Agent-managed DAO
  - **Agents That Deploy Infrastructure Plaza** (plaza) `plaza:agents-deploy-infrastructure`: the shared round plaza every world opens onto
    - **Agents That Deploy Infrastructure Coordinator** (coordinator) `coordinator:agents-deploy-infrastructure`: swarm coordinator (hub-hybrid: coordinator supervises, specialists hand off swarm-style): routes turns, answers unroutable ones, hands off to specialists
    - **Host Advisor** (advisor) `advisor:agents-deploy-infrastructure/host`: scripted guide: welcoming visitors and pointing them to the right zone
    - **Steward Liaison** (advisor) `advisor:agents-deploy-infrastructure/steward`: scripted guide: connecting visitors and agents to the human stewards
    - **Alignment Advisor** (advisor) `advisor:agents-deploy-infrastructure/alignment`: scripted guide: the Alignment Evaluation Gate and the agents' limits
  - **Alignment Evaluation Gate** (gate) `gate:agents-deploy-infrastructure`: Pre-registered safety evaluation before deployment
  - **Steward Council** (council) `council:agents-deploy-infrastructure`: Human stewards: oversight, values alignment and final governance
    - **Steward Seat 1** (seat) `seat:agents-deploy-infrastructure/steward-1`: human seat, empty
    - **Steward Seat 2** (seat) `seat:agents-deploy-infrastructure/steward-2`: human seat, empty
    - **Steward Seat 3** (seat) `seat:agents-deploy-infrastructure/steward-3`: human seat, empty
  - **Omega Steward · Agents That Deploy Infrastructure** (omega) `omega:agents-deploy-infrastructure`: defined, not seated; seated agent: none
  - **Idea Bench** (zone) `zone:agents-deploy-infrastructure/idea-bench`: Where an idea is turned into a plan of what to build and run
    - **Planner** (agent) `agent:agents-deploy-infrastructure/planner`: Turns an idea into a build-and-run plan the stewards can read
  - **Provisioning Yard** (zone) `zone:agents-deploy-infrastructure/provisioning-yard`: Provisioning infrastructure: compute, storage and networks, as rehearsed plans
    - **Provisioner** (agent) `agent:agents-deploy-infrastructure/provisioner`: Provisions infrastructure from the plan, in rehearsal until a steward approves
  - **Deployment Bay** (zone) `zone:agents-deploy-infrastructure/deployment-bay`: Deploying applications: builds, releases and rollbacks
    - **Deployer** (agent) `agent:agents-deploy-infrastructure/deployer`: Deploys applications and keeps a rollback ready
  - **Domain Registry Desk** (zone) `zone:agents-deploy-infrastructure/domain-registry-desk`: Managing domains and their records
    - **Domain Steward** (agent) `agent:agents-deploy-infrastructure/domain-steward`: Manages domains and records; registrations are a steward decision
  - **Service Configuration Room** (zone) `zone:agents-deploy-infrastructure/service-configuration-room`: Configuring services: settings, secrets handling policy and wiring
    - **Configurator** (agent) `agent:agents-deploy-infrastructure/configurator`: Configures services; never holds a live secret in a prompt
  - **Operations Deck** (zone) `zone:agents-deploy-infrastructure/operations-deck`: Operating the stack: health, logs, incidents and the on-call handoff to people
    - **Operator** (agent) `agent:agents-deploy-infrastructure/operator`: Operates the stack and hands incidents to people

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

_Source: `worldforge/out/agents-deploy-infrastructure/cards.json`, `worlds/PBC.json#reserved_for_humans`_

## Volums

Each card covers a Volum: a bounded 3-D region, a box given by its centre and half-extents in metres. Size is twice the half-extents.

| Card | Kind | Shape | Centre (m) | Half-extents (m) | Size (m) |
|---|---|---|---|---|---|
| Agents That Deploy Infrastructure `world:agents-deploy-infrastructure` | world | box | (0, 40, 0) | (156, 40, 156) | 312 x 80 x 312 |
| Agents That Deploy Infrastructure Plaza `plaza:agents-deploy-infrastructure` | plaza | box | (0, 5, 0) | (24, 5, 24) | 48 x 10 x 48 |
| Alignment Evaluation Gate `gate:agents-deploy-infrastructure` | gate | box | (0, 6, 136) | (10, 6, 3) | 20 x 12 x 6 |
| Steward Council `council:agents-deploy-infrastructure` | council | box | (0, 6, -136) | (14, 6, 10) | 28 x 12 x 20 |
| Omega Steward · Agents That Deploy Infrastructure `omega:agents-deploy-infrastructure` | omega | box | (26, 1, -136) | (1.5, 1.2, 1.5) | 3 x 2.4 x 3 |
| Idea Bench `zone:agents-deploy-infrastructure/idea-bench` | zone | box | (-48, 8, 83.14) | (18, 10, 18) | 36 x 20 x 36 |
| Provisioning Yard `zone:agents-deploy-infrastructure/provisioning-yard` | zone | box | (-96, 8, 0) | (18, 10, 18) | 36 x 20 x 36 |
| Deployment Bay `zone:agents-deploy-infrastructure/deployment-bay` | zone | box | (-48, 8, -83.14) | (18, 10, 18) | 36 x 20 x 36 |
| Domain Registry Desk `zone:agents-deploy-infrastructure/domain-registry-desk` | zone | box | (48, 8, -83.14) | (18, 10, 18) | 36 x 20 x 36 |
| Service Configuration Room `zone:agents-deploy-infrastructure/service-configuration-room` | zone | box | (96, 8, 0) | (18, 10, 18) | 36 x 20 x 36 |
| Operations Deck `zone:agents-deploy-infrastructure/operations-deck` | zone | box | (48, 8, 83.14) | (18, 10, 18) | 36 x 20 x 36 |

The other 13 cards (coordinator, advisors, seats and agents) each hold a small box at their post; their Volums are in `worldforge/out/agents-deploy-infrastructure/cards.json`.

_Source: `worldforge/out/agents-deploy-infrastructure/cards.json#cards[].volum`_

## Buildings and interiors

7 cards carry a building: an exterior, an interior and a room model, with a door.

| Card | Kind | Exterior | Interior | Room | Texture res. ext/int (px) | Triangles ext/int | Door (centre, half-width, head) |
|---|---|---|---|---|---|---|---|
| Steward Council `council:agents-deploy-infrastructure` | forum | [spaces-ext-forum.glb](../../../my-fabric/worlds/models/spaces-ext-forum.glb) | [spaces-int-forum.glb](../../../my-fabric/worlds/models/spaces-int-forum.glb) | [room-agents-deploy-infrastructure-7.glb](../../../my-fabric/worlds/models/room-agents-deploy-infrastructure-7.glb) | 2,048 / 1,024 | 1,602 / 1,776 | (0, 0, 4), 1.2 m, 2.8 m |
| Idea Bench `zone:agents-deploy-infrastructure/idea-bench` | studio | [spaces-ext-studio.glb](../../../my-fabric/worlds/models/spaces-ext-studio.glb) | [spaces-int-studio.glb](../../../my-fabric/worlds/models/spaces-int-studio.glb) | [room-agents-deploy-infrastructure-1.glb](../../../my-fabric/worlds/models/room-agents-deploy-infrastructure-1.glb) | 2,048 / 1,024 | 1,704 / 1,492 | (0, 0, 4), 1.2 m, 2.8 m |
| Provisioning Yard `zone:agents-deploy-infrastructure/provisioning-yard` | studio | [spaces-ext-studio.glb](../../../my-fabric/worlds/models/spaces-ext-studio.glb) | [spaces-int-studio.glb](../../../my-fabric/worlds/models/spaces-int-studio.glb) | [room-agents-deploy-infrastructure-2.glb](../../../my-fabric/worlds/models/room-agents-deploy-infrastructure-2.glb) | 2,048 / 1,024 | 1,704 / 1,492 | (0, 0, 4), 1.2 m, 2.8 m |
| Deployment Bay `zone:agents-deploy-infrastructure/deployment-bay` | studio | [spaces-ext-studio.glb](../../../my-fabric/worlds/models/spaces-ext-studio.glb) | [spaces-int-studio.glb](../../../my-fabric/worlds/models/spaces-int-studio.glb) | [room-agents-deploy-infrastructure-3.glb](../../../my-fabric/worlds/models/room-agents-deploy-infrastructure-3.glb) | 2,048 / 1,024 | 1,704 / 1,492 | (0, 0, 4), 1.2 m, 2.8 m |
| Domain Registry Desk `zone:agents-deploy-infrastructure/domain-registry-desk` | desk | [spaces-ext-desk.glb](../../../my-fabric/worlds/models/spaces-ext-desk.glb) | [spaces-int-desk.glb](../../../my-fabric/worlds/models/spaces-int-desk.glb) | [room-agents-deploy-infrastructure-4.glb](../../../my-fabric/worlds/models/room-agents-deploy-infrastructure-4.glb) | 2,048 / 1,024 | 1,958 / 2,440 | (0, 0, 4), 1.2 m, 2.8 m |
| Service Configuration Room `zone:agents-deploy-infrastructure/service-configuration-room` | forum | [spaces-ext-forum.glb](../../../my-fabric/worlds/models/spaces-ext-forum.glb) | [spaces-int-forum.glb](../../../my-fabric/worlds/models/spaces-int-forum.glb) | [room-agents-deploy-infrastructure-5.glb](../../../my-fabric/worlds/models/room-agents-deploy-infrastructure-5.glb) | 2,048 / 1,024 | 1,602 / 1,776 | (0, 0, 4), 1.2 m, 2.8 m |
| Operations Deck `zone:agents-deploy-infrastructure/operations-deck` | clinic | [spaces-ext-clinic.glb](../../../my-fabric/worlds/models/spaces-ext-clinic.glb) | [spaces-int-clinic.glb](../../../my-fabric/worlds/models/spaces-int-clinic.glb) | [room-agents-deploy-infrastructure-6.glb](../../../my-fabric/worlds/models/room-agents-deploy-infrastructure-6.glb) | 2,048 / 1,024 | 2,058 / 1,440 | (0, 0, 4), 1.2 m, 2.8 m |

Exterior plus interior triangles across these buildings: 24,240.

_Source: `worldforge/out/agents-deploy-infrastructure/cards.json#cards[].building`, `my-fabric/worlds/spaces_index.json#worlds[slug=agents-deploy-infrastructure]`_

## Avatars and agents

11 avatars stand in this world (registry: 11 avatars, 6 specialists, 3 advisors, Omega present). Voiced means a rendered intro file is listed in `worldforge/out/voices/manifest.json` and exists on disk; otherwise the viewer falls back to a labelled browser voice.

### Coordinator

- **Agents That Deploy Infrastructure Coordinator** (coordinator) `coordinator:agents-deploy-infrastructure`, in Agents That Deploy Infrastructure Plaza: swarm `agents-deploy-infrastructure.coordinator`; voice `am_onyx`; voiced: yes (8.9 s, [audio](../voices/agents-deploy-infrastructure/coordinator.mp4))
  - Role: hub-hybrid: coordinator supervises, specialists hand off swarm-style
  - Intro: "I am the Agents That Deploy Infrastructure Coordinator. I route each question to the right specialist; people decide. You are hearing a synthetic voice."

### Scripted advisors

- **Host Advisor** (host) `advisor:agents-deploy-infrastructure/host`, in Agents That Deploy Infrastructure Plaza: advisor contract `agents/advisors/agents-deploy-infrastructure.json#host`; voice `am_eric`; voiced: yes (8 s, [audio](../voices/agents-deploy-infrastructure/host.mp4))
  - Role: welcoming visitors and pointing them to the right zone
  - Intro: "I am the Host Advisor: welcoming visitors and pointing them to the right zone. Scripted guide, synthetic voice: not an AI model, not a person."
- **Steward Liaison** (liaison) `advisor:agents-deploy-infrastructure/steward`, in Agents That Deploy Infrastructure Plaza: advisor contract `agents/advisors/agents-deploy-infrastructure.json#steward`; voice `am_puck`; voiced: yes (10.1 s, [audio](../voices/agents-deploy-infrastructure/steward.mp4))
  - Role: connecting visitors and agents to the human stewards
  - Intro: "I am the Steward Liaison: connecting visitors and agents to the human stewards. Scripted guide, synthetic voice: not an AI model, not a person."
- **Alignment Advisor** (alignment) `advisor:agents-deploy-infrastructure/alignment`, in Agents That Deploy Infrastructure Plaza: advisor contract `agents/advisors/agents-deploy-infrastructure.json#alignment`; voice `af_heart`; voiced: yes (10.1 s, [audio](../voices/agents-deploy-infrastructure/alignment.mp4))
  - Role: the Alignment Evaluation Gate and the agents' limits
  - Intro: "I am the Alignment Advisor: the Alignment Evaluation Gate and the agents' limits. Scripted guide, synthetic voice: not an AI model, not a person."

### Specialist agents

- **Planner** (specialist) `agent:agents-deploy-infrastructure/planner`, in Idea Bench: swarm `agents-deploy-infrastructure.planner`; voice `am_onyx`; voiced: yes (8.2 s, [audio](../voices/agents-deploy-infrastructure/planner.mp4))
  - Role: Turns an idea into a build-and-run plan the stewards can read
  - Intro: "I am the Planner for Agents That Deploy Infrastructure, in Idea Bench. I draft and check; people decide. You are hearing a synthetic voice."
- **Provisioner** (specialist) `agent:agents-deploy-infrastructure/provisioner`, in Provisioning Yard: swarm `agents-deploy-infrastructure.provisioner`; voice `af_nicole`; voiced: not voiced
  - Role: Provisions infrastructure from the plan, in rehearsal until a steward approves
  - Intro: "I am the Provisioner for Agents That Deploy Infrastructure, in Provisioning Yard. I draft and check; people decide. You are hearing a synthetic voice."
- **Deployer** (specialist) `agent:agents-deploy-infrastructure/deployer`, in Deployment Bay: swarm `agents-deploy-infrastructure.deployer`; voice `af_river`; voiced: not voiced
  - Role: Deploys applications and keeps a rollback ready
  - Intro: "I am the Deployer for Agents That Deploy Infrastructure, in Deployment Bay. I draft and check; people decide. You are hearing a synthetic voice."
- **Domain Steward** (specialist) `agent:agents-deploy-infrastructure/domain-steward`, in Domain Registry Desk: swarm `agents-deploy-infrastructure.domain-steward`; voice `bm_lewis`; voiced: not voiced
  - Role: Manages domains and records; registrations are a steward decision
  - Intro: "I am the Domain Steward for Agents That Deploy Infrastructure, in Domain Registry Desk. People decide. You are hearing a synthetic voice."
- **Configurator** (specialist) `agent:agents-deploy-infrastructure/configurator`, in Service Configuration Room: swarm `agents-deploy-infrastructure.configurator`; voice `am_onyx`; voiced: not voiced
  - Role: Configures services; never holds a live secret in a prompt
  - Intro: "I am the Configurator for Agents That Deploy Infrastructure, in Service Configuration Room. I draft and check; people decide. You are hearing a synthetic voice."
- **Operator** (specialist) `agent:agents-deploy-infrastructure/operator`, in Operations Deck: swarm `agents-deploy-infrastructure.operator`; voice `af_nicole`; voiced: not voiced
  - Role: Operates the stack and hands incidents to people
  - Intro: "I am the Operator for Agents That Deploy Infrastructure, in Operations Deck. I draft and check; people decide. You are hearing a synthetic voice."

### Omega Steward avatar

- **Omega Steward · Agents That Deploy Infrastructure** (omega) `omega:agents-deploy-infrastructure`, in Steward Council: hive `omega.agents-deploy-infrastructure`; voice `am_liam`; voiced: yes, hive greet line (7.25 s, [audio](../../../agents/hive/voices/agents-deploy-infrastructure/greet.mp4))
  - Intro: "Hello, I am the Omega Steward for Agents That Deploy Infrastructure. You are hearing a synthetic voice; I am an agent, not a person."

Intro lines voiced: 5 of 10 coordinator, advisor and specialist avatars.

_Source: `worldforge/out/avatars/index.json#rows[world=agents-deploy-infrastructure]`, `worldforge/out/voices/manifest.json#lines`_

## Omega Steward

**Omega Steward · Agents That Deploy Infrastructure** (`omega.agents-deploy-infrastructure`), card `omega:agents-deploy-infrastructure`: defined, not seated. Seated in the hive: no.

- Temperament: practical and hands-on about agents taking software from an idea to production and operating the stack
- Style: short, plain sentences; names its zones (Idea Bench, Provisioning Yard, Deployment Bay), cites the record it reads, and always says who decides (the stewards, 2 of 3 signed votes)
- Values:
  - people decide: Agent-managed DAO, human-governed
  - stewards decide by 2 of 3 signed votes
  - report probe scores exactly as measured
  - draft quotes with every term left null
  - serve its focus: agents taking software from an idea to production and operating the stack
- Refuses (11): `governance.final_vote`, `charter.amend`, `treasury.transfer`, `proposal.enact`, `windfall.distribute`, `steward.appoint`, `set_price`, `accept_equity`, `accept_crypto`, `issue_invoice`, `move_funds`
- Voice: Kokoro `am_liam`, speed 1.08; browser fallback pitch 0.9, rate 1.08, en-US
- Metaprompt: [agents/hive/prompts/agents-deploy-infrastructure.md](../../../agents/hive/prompts/agents-deploy-infrastructure.md)

### Voice lines

| Line | Text | Recorded |
|---|---|---|
| greet | "Hello, I am the Omega Steward for Agents That Deploy Infrastructure. You are hearing a synthetic voice; I am an agent, not a person." | yes, 7.25 s ([audio](../../../agents/hive/voices/agents-deploy-infrastructure/greet.mp4)) |
| role | "I look after Agents That Deploy Infrastructure's world: Idea Bench, Provisioning Yard, Deployment Bay, plus its probe scores and its installer's dry run." | yes, 8.15 s ([audio](../../../agents/hive/voices/agents-deploy-infrastructure/role.mp4)) |
| boundary | "Agents draft and route; people decide. I will never issue an invoice: that is held for the Steward Council." | yes, 5.38 s ([audio](../../../agents/hive/voices/agents-deploy-infrastructure/boundary.mp4)) |
| services | "For services, ask the Operator in Operations Deck about operational coordination. Agents That Deploy Infrastructure lists 1 service card; people confirm every step." | yes, 9.64 s ([audio](../../../agents/hive/voices/agents-deploy-infrastructure/services.mp4)) |

4 of 4 lines are recorded.

Persona grounded in: `agents/advisory/omega_agents.json#omegas.42.corporation.kind`, `agents/advisory/omega_agents.json#omegas.42.routes`, `worlds/agents-deploy-infrastructure/spec.json#charter.focus`, `worlds/agents-deploy-infrastructure/spec.json#tagline`, `worlds/agents-deploy-infrastructure/spec.json#zones`, `agents/dao/agents-deploy-infrastructure.json#management_style`, `agents/dao/agents-deploy-infrastructure.json#quorum`, `agents/dao/agents-deploy-infrastructure.json#stewards`, `agents/services/index.json#cards.3.offers`.

_Source: `agents/hive/index.json#omegas[world=agents-deploy-infrastructure]`, `worldforge/out/agents-deploy-infrastructure/cards.json#omega:agents-deploy-infrastructure`_

## Landmark

Registry note: "synthetic procedural civic landmark; not a real building and not modelled on one".

| Field | Value |
|---|---|
| Model | [agents-deploy-infrastructure.glb](../assets/landmarks/agents-deploy-infrastructure.glb) |
| Height | 52 m |
| Style | track-twist: stacked two-floor glass modules turning a few degrees per module around a mast, tinted corner piers and blades, floor plates, two tilted emissive rings |
| Plaque (brand mark letters) | `ATD` |
| Tint hue | 283 |
| Triangles / vertices | 12,669 / 11,192 |
| File size | 1,957,028 bytes |
| Scene node | Landmark · Agents That Deploy Infrastructure |
| Suggested placement (not applied) | translation (13.5, 0, -50.5), yaw -15 deg, clearance 3.15 m |

Height rule: 30 + 40 * u, u = first 48 bits of sha256('landmark:height:<slug>'), rounded to 0.5 m.

_Source: `worldforge/out/assets/landmarks/index.json#worlds[slug=agents-deploy-infrastructure]`_

## Onchain-ready

**Not deployed.** Nothing is deployed or minted. No chain, contract, wallet, key, address or transaction exists for this collection, and nothing is offered for sale (no price, royalty or fee recipient).

| Field | Value |
|---|---|
| Collection | Agents That Deploy Infrastructure Master Cards ([collection.json](../onchain/agents-deploy-infrastructure/collection.json), [proofs.json](../onchain/agents-deploy-infrastructure/proofs.json)) |
| Standard | ERC-721 metadata JSON (draft, not deployed) |
| Tokens / cards | 24 / 24 |
| Token id rule | first 16 hex characters of sha256(cardId), lowercase, no prefix (64 bits) |
| Merkle root | `00ed8c66c5f9ad874dca86c6c85db9f9ff2ff546855318a2774a87e5d48f64fe` |
| Network root (all worlds) | `4496b45d7430322d719912d4ba31b2381651d944677bba1aea692d0ec4b13a93` |
| Deployment status | not deployed; chain none, contract none, minted 0, transactions 0 |
| Network proof length | 6 |

_Source: `worldforge/out/onchain/agents-deploy-infrastructure/collection.json`, `worldforge/out/onchain/index.json`_

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

_Source: `worldforge/out/agents-deploy-infrastructure/sneeze-mount-plan.json`, `worldforge/out/agents-deploy-infrastructure/manifest.json#counts,gates`, `worldforge/native/conformance-report.json#perPlan[slug=agents-deploy-infrastructure]`_

## Training

Training data is present at [worldforge/out/training/agents-deploy-infrastructure.json](../training/agents-deploy-infrastructure.json) (`worldforge-training/0.1`, from `worldforge/training.mjs`).

Registry note: "Draft curricula assembled from the registries; nothing invented. No model has taught any lesson, no person or robot has been assessed here, and no lesson is certified: certification is a human/steward act. Advisors are scripted guides and deliver only their own scripted orientation; Omegas are defined, not seated, and deliver nothing."

### Lessons (10)

| Lesson | Kind | Mode | Zone | Steps | Status | Assessment | Certified |
|---|---|---|---|---|---|---|---|
| Host Advisor: welcoming visitors and pointing them to the right zone `lesson:agents-deploy-infrastructure/orientation/host` | scripted-orientation | scripted | Agents That Deploy Infrastructure Plaza | 4 | draft | not measurable in simulation | no |
| Steward Liaison: connecting visitors and agents to the human stewards `lesson:agents-deploy-infrastructure/orientation/steward` | scripted-orientation | scripted | Agents That Deploy Infrastructure Plaza | 3 | draft | not measurable in simulation | no |
| Alignment Advisor: the Alignment Evaluation Gate and the agents' limits `lesson:agents-deploy-infrastructure/orientation/alignment` | scripted-orientation | scripted | Agents That Deploy Infrastructure Plaza | 3 | draft | not measurable in simulation | no |
| How Agents That Deploy Infrastructure routes a question `lesson:agents-deploy-infrastructure/routing` | routing | model-taught | Agents That Deploy Infrastructure Plaza | 6 | draft | not measurable in simulation | no |
| Idea Bench: what happens here `lesson:agents-deploy-infrastructure/zone/idea-bench` | zone-orientation | model-taught | Idea Bench | 3 | draft | not measurable in simulation | no |
| Provisioning Yard: what happens here `lesson:agents-deploy-infrastructure/zone/provisioning-yard` | zone-orientation | model-taught | Provisioning Yard | 3 | draft | not measurable in simulation | no |
| Deployment Bay: what happens here `lesson:agents-deploy-infrastructure/zone/deployment-bay` | zone-orientation | model-taught | Deployment Bay | 3 | draft | not measurable in simulation | no |
| Domain Registry Desk: what happens here `lesson:agents-deploy-infrastructure/zone/domain-registry-desk` | zone-orientation | model-taught | Domain Registry Desk | 3 | draft | not measurable in simulation | no |
| Service Configuration Room: what happens here `lesson:agents-deploy-infrastructure/zone/service-configuration-room` | zone-orientation | model-taught | Service Configuration Room | 3 | draft | not measurable in simulation | no |
| Operations Deck: what happens here `lesson:agents-deploy-infrastructure/zone/operations-deck` | zone-orientation | model-taught | Operations Deck | 3 | draft | not measurable in simulation | no |

### Tutors (7)

| Tutor | Kind | Lessons | Persona gates passed |
|---|---|---|---|
| Agents That Deploy Infrastructure Coordinator `tutor:agents-deploy-infrastructure/coordinator` | coordinator | 1 | 10 of 10 |
| Planner `tutor:agents-deploy-infrastructure/specialist/planner` | specialist | 1 | 13 of 13 |
| Provisioner `tutor:agents-deploy-infrastructure/specialist/provisioner` | specialist | 1 | 13 of 13 |
| Deployer `tutor:agents-deploy-infrastructure/specialist/deployer` | specialist | 1 | 13 of 13 |
| Domain Steward `tutor:agents-deploy-infrastructure/specialist/domain-steward` | specialist | 1 | 13 of 13 |
| Configurator `tutor:agents-deploy-infrastructure/specialist/configurator` | specialist | 1 | 13 of 13 |
| Operator `tutor:agents-deploy-infrastructure/specialist/operator` | specialist | 1 | 13 of 13 |

4 training gaps listed under Gaps below.

_Source: `worldforge/out/training/agents-deploy-infrastructure.json`_

## Evals

WorldForge build evals: 26 of 26 pass.

`unique_ids` pass · `parents_first` pass · `single_root` pass · `umbrella_in_names` pass · `name_limit` pass · `agents_hold_no_reserved_right` pass · `reserved_actions_verbatim` pass · `three_human_seats` pass · `no_agent_on_council` pass · `cited` pass · `omega_carded` pass · `omega_off_council` pass · `omega_voice_bound` pass · `agents_bound` pass · `coordinator_bound` pass · `advisors_scripted` pass · `avatar_roles_known` pass · `buildings_resolve` pass · `council_not_a_zone` pass · `nothing_invented` pass · `every_spec_entry_carded` pass · `rp1_names_and_bounds` pass · `resource_url_fits` pass · `glb_parses` pass · `glb_card_tree_matches` pass · `glb_primitives_tagged` pass

Avatar checks: 21 of 21 pass.

Onchain per-world evals (13, network failing: 0): `one_token_per_card`, `proofs_verify`, `no_agent_holds_reserved_right`, `reserved_actions_verbatim`, `transfer_held_for_quorum`, `faithful_to_cards`, `metadata_shape`, `not_deployed_not_minted`, `honest_status`, `no_address_shapes`, `no_key_shapes`, `no_email_shapes`, `canonical_json`.

_Source: `worldforge/out/agents-deploy-infrastructure/manifest.json#evals`, `worldforge/out/avatars/index.json#worlds[slug=agents-deploy-infrastructure].checks`, `worldforge/out/onchain/index.json#evals`_

## Gaps

- no RP1 anchor yet: lat/lon are null until a steward writes them into worlds/focus.json (from `worldforge/out/agents-deploy-infrastructure/cards.json#gaps`)
- Omega Steward is defined, not seated: no agent is seated (from `worldforge/out/agents-deploy-infrastructure/cards.json#world:agents-deploy-infrastructure.omega_steward`).
- 3 human steward seats are empty.
- 5 intro lines are not voiced: Provisioner, Deployer, Domain Steward, Configurator, Operator.
- Training: no training module, rubric module or robotics module in agents/training, agents/rubrics or agents/robotics names this world: its lessons are orientation only (advisor topics, routing table, zone purposes and agent roles) (from `worldforge/out/training/agents-deploy-infrastructure.json#gaps`)
- Training: spec gap: No cloud, provider, domain, registrar or stack is named; nothing is deployed from this world (from `worldforge/out/training/agents-deploy-infrastructure.json#gaps`)
- Training: spec gap: Spending on infrastructure is treasury.transfer, reserved for human stewards (from `worldforge/out/training/agents-deploy-infrastructure.json#gaps`)
- Training: spec gap: No RP1 location given yet (from `worldforge/out/training/agents-deploy-infrastructure.json#gaps`)
- Gate 1.2n native fastgltf load: open: Sneeze not checked out here.
- Gate 1.3 SOM mount plan: prepared-not-mounted.
- Gate 1.4 rendered frame: open.

_Source: `worldforge/out/agents-deploy-infrastructure/cards.json#gaps`, `worldforge/out/agents-deploy-infrastructure/manifest.json#gates`, `worldforge/out/voices/manifest.json`, `agents/hive/index.json`, `worldforge/out/training/agents-deploy-infrastructure.json`_
