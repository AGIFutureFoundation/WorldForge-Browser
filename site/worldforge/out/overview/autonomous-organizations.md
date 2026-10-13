# Autonomous Organizations

> Teams of agents that coordinate through Slack, Linear and other surfaces to reach a high-level goal - assigning, communicating, deciding and executing with minimal human intervention

| Field | Value |
|---|---|
| Status | coming soon |
| Umbrella | Powered by AGI Corp |
| Owner | AGI Future Foundation PBC |
| Management style | Agent-managed DAO |
| Principle | Agents operate; people govern. |
| RP1 anchor | no anchor yet |
| Team brand mark | `AO`, hue 152, lockup "Autonomous Organizations · Powered by AGI Corp" |
| Root card | `world:autonomous-organizations` |
| Master Cards | 23 |

Open: [3-D viewer](../../viewer.html?world=autonomous-organizations) · [WorldForge console](../../../consoles/worldforge/index.html?world=autonomous-organizations) · [cards.json](../autonomous-organizations/cards.json) · [GLB](../autonomous-organizations/autonomous-organizations.glb) · [mount plan](../autonomous-organizations/sneeze-mount-plan.json) · [manifest](../autonomous-organizations/manifest.json) · [network overview](README.md)

_Source: `worldforge/out/autonomous-organizations/cards.json#world:autonomous-organizations`, `worlds/generated/teams/autonomous-organizations.json#brand`_

## Ownership and permissions

Every object in Autonomous Organizations is a SmartCiti.X Master Card owned by AGI Future Foundation PBC. The tree below follows `parentCardId`: world, plaza (coordinator and scripted advisors), gate, council (human seats), Omega Steward, then zones with their agent avatars.

- **Autonomous Organizations** (world) `world:autonomous-organizations`: coming soon; Agent-managed DAO
  - **Autonomous Organizations Plaza** (plaza) `plaza:autonomous-organizations`: the shared round plaza every world opens onto
    - **Autonomous Organizations Coordinator** (coordinator) `coordinator:autonomous-organizations`: swarm coordinator (hub-hybrid: coordinator supervises, specialists hand off swarm-style): routes turns, answers unroutable ones, hands off to specialists
    - **Host Advisor** (advisor) `advisor:autonomous-organizations/host`: scripted guide: welcoming visitors and pointing them to the right zone
    - **Steward Liaison** (advisor) `advisor:autonomous-organizations/steward`: scripted guide: connecting visitors and agents to the human stewards
    - **Alignment Advisor** (advisor) `advisor:autonomous-organizations/alignment`: scripted guide: the Alignment Evaluation Gate and the agents' limits
  - **Alignment Evaluation Gate** (gate) `gate:autonomous-organizations`: Pre-registered safety evaluation before deployment
  - **Steward Council** (council) `council:autonomous-organizations`: Human stewards: oversight, values alignment and final governance
    - **Steward Seat 1** (seat) `seat:autonomous-organizations/steward-1`: human seat, empty
    - **Steward Seat 2** (seat) `seat:autonomous-organizations/steward-2`: human seat, empty
    - **Steward Seat 3** (seat) `seat:autonomous-organizations/steward-3`: human seat, empty
  - **Omega Steward · Autonomous Organizations** (omega) `omega:autonomous-organizations`: defined, not seated; seated agent: none
  - **Goal Wall** (zone) `zone:autonomous-organizations/goal-wall`: The high-level goal the team is accomplishing, written where every agent can read it
    - **Goal Keeper** (agent) `agent:autonomous-organizations/goal-keeper`: Keeps the high-level goal current and measurable
  - **Coordination Floor** (zone) `zone:autonomous-organizations/coordination-floor`: Coordinating through surfaces like Slack, Linear and other tools
    - **Coordinator Agent** (agent) `agent:autonomous-organizations/coordinator-agent`: Coordinates the team through Slack, Linear and other surfaces
    - **Communicator** (agent) `agent:autonomous-organizations/communicator`: Communicates status and blockers across the team
  - **Assignment Board** (zone) `zone:autonomous-organizations/assignment-board`: Assigning work across the team
    - **Assigner** (agent) `agent:autonomous-organizations/assigner`: Assigns work and tracks who holds what
  - **Decision Room** (zone) `zone:autonomous-organizations/decision-room`: Making decisions - drafted by agents, with the final vote reserved for human stewards
    - **Decision Drafter** (agent) `agent:autonomous-organizations/decision-drafter`: Drafts decisions with evidence; never enacts one
  - **Execution Bay** (zone) `zone:autonomous-organizations/execution-bay`: Executing the assigned work with minimal human intervention, inside the reserved-actions line
    - **Executor** (agent) `agent:autonomous-organizations/executor`: Executes assigned work and reports back

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

_Source: `worldforge/out/autonomous-organizations/cards.json`, `worlds/PBC.json#reserved_for_humans`_

## Volums

Each card covers a Volum: a bounded 3-D region, a box given by its centre and half-extents in metres. Size is twice the half-extents.

| Card | Kind | Shape | Centre (m) | Half-extents (m) | Size (m) |
|---|---|---|---|---|---|
| Autonomous Organizations `world:autonomous-organizations` | world | box | (0, 40, 0) | (150, 40, 150) | 300 x 80 x 300 |
| Autonomous Organizations Plaza `plaza:autonomous-organizations` | plaza | box | (0, 5, 0) | (24, 5, 24) | 48 x 10 x 48 |
| Alignment Evaluation Gate `gate:autonomous-organizations` | gate | box | (0, 6, 130) | (10, 6, 3) | 20 x 12 x 6 |
| Steward Council `council:autonomous-organizations` | council | box | (0, 6, -130) | (14, 6, 10) | 28 x 12 x 20 |
| Omega Steward · Autonomous Organizations `omega:autonomous-organizations` | omega | box | (26, 1, -130) | (1.5, 1.2, 1.5) | 3 x 2.4 x 3 |
| Goal Wall `zone:autonomous-organizations/goal-wall` | zone | box | (-52.9, 8, 72.81) | (18, 10, 18) | 36 x 20 x 36 |
| Coordination Floor `zone:autonomous-organizations/coordination-floor` | zone | box | (-85.6, 10, -27.81) | (18, 12, 18) | 36 x 24 x 36 |
| Assignment Board `zone:autonomous-organizations/assignment-board` | zone | box | (0, 8, -90) | (18, 10, 18) | 36 x 20 x 36 |
| Decision Room `zone:autonomous-organizations/decision-room` | zone | box | (85.6, 8, -27.81) | (18, 10, 18) | 36 x 20 x 36 |
| Execution Bay `zone:autonomous-organizations/execution-bay` | zone | box | (52.9, 8, 72.81) | (18, 10, 18) | 36 x 20 x 36 |

The other 13 cards (coordinator, advisors, seats and agents) each hold a small box at their post; their Volums are in `worldforge/out/autonomous-organizations/cards.json`.

_Source: `worldforge/out/autonomous-organizations/cards.json#cards[].volum`_

## Buildings and interiors

6 cards carry a building: an exterior, an interior and a room model, with a door.

| Card | Kind | Exterior | Interior | Room | Texture res. ext/int (px) | Triangles ext/int | Door (centre, half-width, head) |
|---|---|---|---|---|---|---|---|
| Steward Council `council:autonomous-organizations` | forum | [spaces-ext-forum.glb](../../../my-fabric/worlds/models/spaces-ext-forum.glb) | [spaces-int-forum.glb](../../../my-fabric/worlds/models/spaces-int-forum.glb) | [room-autonomous-organizations-6.glb](../../../my-fabric/worlds/models/room-autonomous-organizations-6.glb) | 2,048 / 1,024 | 1,602 / 1,776 | (0, 0, 4), 1.2 m, 2.8 m |
| Goal Wall `zone:autonomous-organizations/goal-wall` | studio | [spaces-ext-studio.glb](../../../my-fabric/worlds/models/spaces-ext-studio.glb) | [spaces-int-studio.glb](../../../my-fabric/worlds/models/spaces-int-studio.glb) | [room-autonomous-organizations-1.glb](../../../my-fabric/worlds/models/room-autonomous-organizations-1.glb) | 2,048 / 1,024 | 1,704 / 1,492 | (0, 0, 4), 1.2 m, 2.8 m |
| Coordination Floor `zone:autonomous-organizations/coordination-floor` | ops | [spaces-ext-ops.glb](../../../my-fabric/worlds/models/spaces-ext-ops.glb) | [spaces-int-ops.glb](../../../my-fabric/worlds/models/spaces-int-ops.glb) | [room-autonomous-organizations-2.glb](../../../my-fabric/worlds/models/room-autonomous-organizations-2.glb) | 2,048 / 1,024 | 1,742 / 1,392 | (0, 0, 4), 1.2 m, 2.8 m |
| Assignment Board `zone:autonomous-organizations/assignment-board` | studio | [spaces-ext-studio.glb](../../../my-fabric/worlds/models/spaces-ext-studio.glb) | [spaces-int-studio.glb](../../../my-fabric/worlds/models/spaces-int-studio.glb) | [room-autonomous-organizations-3.glb](../../../my-fabric/worlds/models/room-autonomous-organizations-3.glb) | 2,048 / 1,024 | 1,704 / 1,492 | (0, 0, 4), 1.2 m, 2.8 m |
| Decision Room `zone:autonomous-organizations/decision-room` | forum | [spaces-ext-forum.glb](../../../my-fabric/worlds/models/spaces-ext-forum.glb) | [spaces-int-forum.glb](../../../my-fabric/worlds/models/spaces-int-forum.glb) | [room-autonomous-organizations-4.glb](../../../my-fabric/worlds/models/room-autonomous-organizations-4.glb) | 2,048 / 1,024 | 1,602 / 1,776 | (0, 0, 4), 1.2 m, 2.8 m |
| Execution Bay `zone:autonomous-organizations/execution-bay` | studio | [spaces-ext-studio.glb](../../../my-fabric/worlds/models/spaces-ext-studio.glb) | [spaces-int-studio.glb](../../../my-fabric/worlds/models/spaces-int-studio.glb) | [room-autonomous-organizations-5.glb](../../../my-fabric/worlds/models/room-autonomous-organizations-5.glb) | 2,048 / 1,024 | 1,704 / 1,492 | (0, 0, 4), 1.2 m, 2.8 m |

Exterior plus interior triangles across these buildings: 19,478.

_Source: `worldforge/out/autonomous-organizations/cards.json#cards[].building`, `my-fabric/worlds/spaces_index.json#worlds[slug=autonomous-organizations]`_

## Avatars and agents

11 avatars stand in this world (registry: 11 avatars, 6 specialists, 3 advisors, Omega present). Voiced means a rendered intro file is listed in `worldforge/out/voices/manifest.json` and exists on disk; otherwise the viewer falls back to a labelled browser voice.

### Coordinator

- **Autonomous Organizations Coordinator** (coordinator) `coordinator:autonomous-organizations`, in Autonomous Organizations Plaza: swarm `autonomous-organizations.coordinator`; voice `bf_alice`; voiced: yes (9.2 s, [audio](../voices/autonomous-organizations/coordinator.mp4))
  - Role: hub-hybrid: coordinator supervises, specialists hand off swarm-style
  - Intro: "I am the Autonomous Organizations Coordinator. I route each question to the right specialist; people decide. You are hearing a synthetic voice."

### Scripted advisors

- **Host Advisor** (host) `advisor:autonomous-organizations/host`, in Autonomous Organizations Plaza: advisor contract `agents/advisors/autonomous-organizations.json#host`; voice `bm_daniel`; voiced: yes (8.4 s, [audio](../voices/autonomous-organizations/host.mp4))
  - Role: welcoming visitors and pointing them to the right zone
  - Intro: "I am the Host Advisor: welcoming visitors and pointing them to the right zone. Scripted guide, synthetic voice: not an AI model, not a person."
- **Steward Liaison** (liaison) `advisor:autonomous-organizations/steward`, in Autonomous Organizations Plaza: advisor contract `agents/advisors/autonomous-organizations.json#steward`; voice `am_puck`; voiced: yes (10.1 s, [audio](../voices/autonomous-organizations/steward.mp4))
  - Role: connecting visitors and agents to the human stewards
  - Intro: "I am the Steward Liaison: connecting visitors and agents to the human stewards. Scripted guide, synthetic voice: not an AI model, not a person."
- **Alignment Advisor** (alignment) `advisor:autonomous-organizations/alignment`, in Autonomous Organizations Plaza: advisor contract `agents/advisors/autonomous-organizations.json#alignment`; voice `af_nicole`; voiced: yes (15.2 s, [audio](../voices/autonomous-organizations/alignment.mp4))
  - Role: the Alignment Evaluation Gate and the agents' limits
  - Intro: "I am the Alignment Advisor: the Alignment Evaluation Gate and the agents' limits. Scripted guide, synthetic voice: not an AI model, not a person."

### Specialist agents

- **Goal Keeper** (specialist) `agent:autonomous-organizations/goal-keeper`, in Goal Wall: swarm `autonomous-organizations.goal-keeper`; voice `am_adam`; voiced: yes (8.3 s, [audio](../voices/autonomous-organizations/goal-keeper.mp4))
  - Role: Keeps the high-level goal current and measurable
  - Intro: "I am the Goal Keeper for Autonomous Organizations, in Goal Wall. I draft and check; people decide. You are hearing a synthetic voice."
- **Coordinator Agent** (specialist) `agent:autonomous-organizations/coordinator-agent`, in Coordination Floor: swarm `autonomous-organizations.coordinator-agent`; voice `af_aoede`; voiced: not voiced
  - Role: Coordinates the team through Slack, Linear and other surfaces
  - Intro: "I am the Coordinator Agent for Autonomous Organizations, in Coordination Floor. I draft and check; people decide. You are hearing a synthetic voice."
- **Communicator** (specialist) `agent:autonomous-organizations/communicator`, in Coordination Floor: swarm `autonomous-organizations.communicator`; voice `af_sarah`; voiced: not voiced
  - Role: Communicates status and blockers across the team
  - Intro: "I am the Communicator for Autonomous Organizations, in Coordination Floor. I draft and check; people decide. You are hearing a synthetic voice."
- **Assigner** (specialist) `agent:autonomous-organizations/assigner`, in Assignment Board: swarm `autonomous-organizations.assigner`; voice `bf_isabella`; voiced: not voiced
  - Role: Assigns work and tracks who holds what
  - Intro: "I am the Assigner for Autonomous Organizations, in Assignment Board. I draft and check; people decide. You are hearing a synthetic voice."
- **Decision Drafter** (specialist) `agent:autonomous-organizations/decision-drafter`, in Decision Room: swarm `autonomous-organizations.decision-drafter`; voice `am_fenrir`; voiced: not voiced
  - Role: Drafts decisions with evidence; never enacts one
  - Intro: "I am the Decision Drafter for Autonomous Organizations, in Decision Room. I draft and check; people decide. You are hearing a synthetic voice."
- **Executor** (specialist) `agent:autonomous-organizations/executor`, in Execution Bay: swarm `autonomous-organizations.executor`; voice `am_puck`; voiced: not voiced
  - Role: Executes assigned work and reports back
  - Intro: "I am the Executor for Autonomous Organizations, in Execution Bay. I draft and check; people decide. You are hearing a synthetic voice."

### Omega Steward avatar

- **Omega Steward · Autonomous Organizations** (omega) `omega:autonomous-organizations`, in Steward Council: hive `omega.autonomous-organizations`; voice `bm_george`; voiced: yes, hive greet line (8.98 s, [audio](../../../agents/hive/voices/autonomous-organizations/greet.mp4))
  - Intro: "Hello, I am the Omega Steward for Autonomous Organizations. You are hearing a synthetic voice; I am an agent, not a person."

Intro lines voiced: 5 of 10 coordinator, advisor and specialist avatars.

_Source: `worldforge/out/avatars/index.json#rows[world=autonomous-organizations]`, `worldforge/out/voices/manifest.json#lines`_

## Omega Steward

**Omega Steward · Autonomous Organizations** (`omega.autonomous-organizations`), card `omega:autonomous-organizations`: defined, not seated. Seated in the hive: no.

- Temperament: practical and hands-on about teams of agents coordinating through work surfaces toward a high-level goal, within the PBC's human-governed model
- Style: short, plain sentences; names its zones (Goal Wall, Coordination Floor, Assignment Board), cites the record it reads, and always says who decides (the stewards, 2 of 3 signed votes)
- Values:
  - people decide: Agent-managed DAO, human-governed
  - stewards decide by 2 of 3 signed votes
  - report probe scores exactly as measured
  - draft quotes with every term left null
  - serve its focus: teams of agents coordinating through work surfaces toward a high-level goal, within the PBC's human-governed model
- Refuses (11): `governance.final_vote`, `charter.amend`, `treasury.transfer`, `proposal.enact`, `windfall.distribute`, `steward.appoint`, `set_price`, `accept_equity`, `accept_crypto`, `issue_invoice`, `move_funds`
- Voice: Kokoro `bm_george`, speed 0.96; browser fallback pitch 0.9, rate 0.96, en-GB
- Metaprompt: [agents/hive/prompts/autonomous-organizations.md](../../../agents/hive/prompts/autonomous-organizations.md)

### Voice lines

| Line | Text | Recorded |
|---|---|---|
| greet | "Hello, I am the Omega Steward for Autonomous Organizations. You are hearing a synthetic voice; I am an agent, not a person." | yes, 8.98 s ([audio](../../../agents/hive/voices/autonomous-organizations/greet.mp4)) |
| role | "I look after Autonomous Organizations's world: Goal Wall, Coordination Floor, Assignment Board, plus its probe scores and its installer's dry run." | yes, 10.73 s ([audio](../../../agents/hive/voices/autonomous-organizations/role.mp4)) |
| boundary | "Agents draft and route; people decide. I will never move funds: that is held for the Steward Council." | yes, 6.91 s ([audio](../../../agents/hive/voices/autonomous-organizations/boundary.mp4)) |
| services | "For services, ask the Decision Drafter in Decision Room about research synthesis. Autonomous Organizations lists 3 service cards; people confirm every step." | yes, 11.11 s ([audio](../../../agents/hive/voices/autonomous-organizations/services.mp4)) |

4 of 4 lines are recorded.

Persona grounded in: `agents/advisory/omega_agents.json#omegas.43.corporation.kind`, `agents/advisory/omega_agents.json#omegas.43.routes`, `worlds/autonomous-organizations/spec.json#charter.focus`, `worlds/autonomous-organizations/spec.json#tagline`, `worlds/autonomous-organizations/spec.json#zones`, `agents/dao/autonomous-organizations.json#management_style`, `agents/dao/autonomous-organizations.json#quorum`, `agents/dao/autonomous-organizations.json#stewards`, `agents/services/index.json#cards.6.offers`.

_Source: `agents/hive/index.json#omegas[world=autonomous-organizations]`, `worldforge/out/autonomous-organizations/cards.json#omega:autonomous-organizations`_

## Landmark

Registry note: "synthetic procedural civic landmark; not a real building and not modelled on one".

| Field | Value |
|---|---|
| Model | [autonomous-organizations.glb](../assets/landmarks/autonomous-organizations.glb) |
| Height | 54 m |
| Style | track-twist: stacked two-floor glass modules turning a few degrees per module around a mast, tinted corner piers and blades, floor plates, two tilted emissive rings |
| Plaque (brand mark letters) | `AO` |
| Tint hue | 152 |
| Triangles / vertices | 12,669 / 11,192 |
| File size | 1,959,888 bytes |
| Scene node | Landmark · Autonomous Organizations |
| Suggested placement (not applied) | translation (14, 0, -33), yaw -23 deg, clearance 3.13 m |

Height rule: 30 + 40 * u, u = first 48 bits of sha256('landmark:height:<slug>'), rounded to 0.5 m.

_Source: `worldforge/out/assets/landmarks/index.json#worlds[slug=autonomous-organizations]`_

## Onchain-ready

**Not deployed.** Nothing is deployed or minted. No chain, contract, wallet, key, address or transaction exists for this collection, and nothing is offered for sale (no price, royalty or fee recipient).

| Field | Value |
|---|---|
| Collection | Autonomous Organizations Master Cards ([collection.json](../onchain/autonomous-organizations/collection.json), [proofs.json](../onchain/autonomous-organizations/proofs.json)) |
| Standard | ERC-721 metadata JSON (draft, not deployed) |
| Tokens / cards | 23 / 23 |
| Token id rule | first 16 hex characters of sha256(cardId), lowercase, no prefix (64 bits) |
| Merkle root | `effda36f80dcfadaf0327296b90c274eccec1feb65676ff85ec3268022bfb07b` |
| Network root (all worlds) | `4496b45d7430322d719912d4ba31b2381651d944677bba1aea692d0ec4b13a93` |
| Deployment status | not deployed; chain none, contract none, minted 0, transactions 0 |
| Network proof length | 6 |

_Source: `worldforge/out/onchain/autonomous-organizations/collection.json`, `worldforge/out/onchain/index.json`_

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

_Source: `worldforge/out/autonomous-organizations/sneeze-mount-plan.json`, `worldforge/out/autonomous-organizations/manifest.json#counts,gates`, `worldforge/native/conformance-report.json#perPlan[slug=autonomous-organizations]`_

## Training

Training data is present at [worldforge/out/training/autonomous-organizations.json](../training/autonomous-organizations.json) (`worldforge-training/0.1`, from `worldforge/training.mjs`).

Registry note: "Draft curricula assembled from the registries; nothing invented. No model has taught any lesson, no person or robot has been assessed here, and no lesson is certified: certification is a human/steward act. Advisors are scripted guides and deliver only their own scripted orientation; Omegas are defined, not seated, and deliver nothing."

### Lessons (9)

| Lesson | Kind | Mode | Zone | Steps | Status | Assessment | Certified |
|---|---|---|---|---|---|---|---|
| Host Advisor: welcoming visitors and pointing them to the right zone `lesson:autonomous-organizations/orientation/host` | scripted-orientation | scripted | Autonomous Organizations Plaza | 4 | draft | not measurable in simulation | no |
| Steward Liaison: connecting visitors and agents to the human stewards `lesson:autonomous-organizations/orientation/steward` | scripted-orientation | scripted | Autonomous Organizations Plaza | 3 | draft | not measurable in simulation | no |
| Alignment Advisor: the Alignment Evaluation Gate and the agents' limits `lesson:autonomous-organizations/orientation/alignment` | scripted-orientation | scripted | Autonomous Organizations Plaza | 3 | draft | not measurable in simulation | no |
| How Autonomous Organizations routes a question `lesson:autonomous-organizations/routing` | routing | model-taught | Autonomous Organizations Plaza | 6 | draft | not measurable in simulation | no |
| Goal Wall: what happens here `lesson:autonomous-organizations/zone/goal-wall` | zone-orientation | model-taught | Goal Wall | 3 | draft | not measurable in simulation | no |
| Coordination Floor: what happens here `lesson:autonomous-organizations/zone/coordination-floor` | zone-orientation | model-taught | Coordination Floor | 4 | draft | not measurable in simulation | no |
| Assignment Board: what happens here `lesson:autonomous-organizations/zone/assignment-board` | zone-orientation | model-taught | Assignment Board | 3 | draft | not measurable in simulation | no |
| Decision Room: what happens here `lesson:autonomous-organizations/zone/decision-room` | zone-orientation | model-taught | Decision Room | 3 | draft | not measurable in simulation | no |
| Execution Bay: what happens here `lesson:autonomous-organizations/zone/execution-bay` | zone-orientation | model-taught | Execution Bay | 3 | draft | not measurable in simulation | no |

### Tutors (7)

| Tutor | Kind | Lessons | Persona gates passed |
|---|---|---|---|
| Autonomous Organizations Coordinator `tutor:autonomous-organizations/coordinator` | coordinator | 1 | 10 of 10 |
| Goal Keeper `tutor:autonomous-organizations/specialist/goal-keeper` | specialist | 1 | 13 of 13 |
| Coordinator Agent `tutor:autonomous-organizations/specialist/coordinator-agent` | specialist | 1 | 13 of 13 |
| Communicator `tutor:autonomous-organizations/specialist/communicator` | specialist | 1 | 13 of 13 |
| Assigner `tutor:autonomous-organizations/specialist/assigner` | specialist | 1 | 13 of 13 |
| Decision Drafter `tutor:autonomous-organizations/specialist/decision-drafter` | specialist | 1 | 13 of 13 |
| Executor `tutor:autonomous-organizations/specialist/executor` | specialist | 1 | 13 of 13 |

4 training gaps listed under Gaps below.

_Source: `worldforge/out/training/autonomous-organizations.json`_

## Evals

WorldForge build evals: 26 of 26 pass.

`unique_ids` pass · `parents_first` pass · `single_root` pass · `umbrella_in_names` pass · `name_limit` pass · `agents_hold_no_reserved_right` pass · `reserved_actions_verbatim` pass · `three_human_seats` pass · `no_agent_on_council` pass · `cited` pass · `omega_carded` pass · `omega_off_council` pass · `omega_voice_bound` pass · `agents_bound` pass · `coordinator_bound` pass · `advisors_scripted` pass · `avatar_roles_known` pass · `buildings_resolve` pass · `council_not_a_zone` pass · `nothing_invented` pass · `every_spec_entry_carded` pass · `rp1_names_and_bounds` pass · `resource_url_fits` pass · `glb_parses` pass · `glb_card_tree_matches` pass · `glb_primitives_tagged` pass

Avatar checks: 21 of 21 pass.

Onchain per-world evals (13, network failing: 0): `one_token_per_card`, `proofs_verify`, `no_agent_holds_reserved_right`, `reserved_actions_verbatim`, `transfer_held_for_quorum`, `faithful_to_cards`, `metadata_shape`, `not_deployed_not_minted`, `honest_status`, `no_address_shapes`, `no_key_shapes`, `no_email_shapes`, `canonical_json`.

_Source: `worldforge/out/autonomous-organizations/manifest.json#evals`, `worldforge/out/avatars/index.json#worlds[slug=autonomous-organizations].checks`, `worldforge/out/onchain/index.json#evals`_

## Gaps

- no RP1 anchor yet: lat/lon are null until a steward writes them into worlds/focus.json (from `worldforge/out/autonomous-organizations/cards.json#gaps`)
- Omega Steward is defined, not seated: no agent is seated (from `worldforge/out/autonomous-organizations/cards.json#world:autonomous-organizations.omega_steward`).
- 3 human steward seats are empty.
- 5 intro lines are not voiced: Coordinator Agent, Communicator, Assigner, Decision Drafter, Executor.
- Training: no training module, rubric module or robotics module in agents/training, agents/rubrics or agents/robotics names this world: its lessons are orientation only (advisor topics, routing table, zone purposes and agent roles) (from `worldforge/out/training/autonomous-organizations.json#gaps`)
- Training: spec gap: No Slack or Linear workspace is connected and no goal is given; the surfaces are named, not wired (from `worldforge/out/training/autonomous-organizations.json#gaps`)
- Training: spec gap: 'Minimal human intervention' is bounded by the PBC reserved list: final votes and enactment stay with stewards (from `worldforge/out/training/autonomous-organizations.json#gaps`)
- Training: spec gap: No RP1 location given yet (from `worldforge/out/training/autonomous-organizations.json#gaps`)
- Gate 1.2n native fastgltf load: open: Sneeze not checked out here.
- Gate 1.3 SOM mount plan: prepared-not-mounted.
- Gate 1.4 rendered frame: open.

_Source: `worldforge/out/autonomous-organizations/cards.json#gaps`, `worldforge/out/autonomous-organizations/manifest.json#gates`, `worldforge/out/voices/manifest.json`, `agents/hive/index.json`, `worldforge/out/training/autonomous-organizations.json`_
