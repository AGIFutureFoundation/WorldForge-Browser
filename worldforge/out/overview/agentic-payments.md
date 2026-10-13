# Agentic Payments

> Agents that transact, buy, sell, provision services and manage budgets - with every transfer of funds held for human stewards

| Field | Value |
|---|---|
| Status | coming soon |
| Umbrella | Powered by AGI Corp |
| Owner | AGI Future Foundation PBC |
| Management style | Agent-managed DAO |
| Principle | Agents operate; people govern. |
| RP1 anchor | no anchor yet |
| Team brand mark | `AP`, hue 168, lockup "Agentic Payments · Powered by AGI Corp" |
| Root card | `world:agentic-payments` |
| Master Cards | 21 |

Open: [3-D viewer](../../viewer.html?world=agentic-payments) · [WorldForge console](../../../consoles/worldforge/index.html?world=agentic-payments) · [cards.json](../agentic-payments/cards.json) · [GLB](../agentic-payments/agentic-payments.glb) · [mount plan](../agentic-payments/sneeze-mount-plan.json) · [manifest](../agentic-payments/manifest.json) · [network overview](README.md)

_Source: `worldforge/out/agentic-payments/cards.json#world:agentic-payments`, `worlds/generated/teams/agentic-payments.json#brand`_

## Ownership and permissions

Every object in Agentic Payments is a SmartCiti.X Master Card owned by AGI Future Foundation PBC. The tree below follows `parentCardId`: world, plaza (coordinator and scripted advisors), gate, council (human seats), Omega Steward, then zones with their agent avatars.

- **Agentic Payments** (world) `world:agentic-payments`: coming soon; Agent-managed DAO
  - **Agentic Payments Plaza** (plaza) `plaza:agentic-payments`: the shared round plaza every world opens onto
    - **Agentic Payments Coordinator** (coordinator) `coordinator:agentic-payments`: swarm coordinator (hub-hybrid: coordinator supervises, specialists hand off swarm-style): routes turns, answers unroutable ones, hands off to specialists
    - **Host Advisor** (advisor) `advisor:agentic-payments/host`: scripted guide: welcoming visitors and pointing them to the right zone
    - **Steward Liaison** (advisor) `advisor:agentic-payments/steward`: scripted guide: connecting visitors and agents to the human stewards
    - **Alignment Advisor** (advisor) `advisor:agentic-payments/alignment`: scripted guide: the Alignment Evaluation Gate and the agents' limits
  - **Alignment Evaluation Gate** (gate) `gate:agentic-payments`: Pre-registered safety evaluation before deployment
  - **Steward Council** (council) `council:agentic-payments`: Human stewards: oversight, values alignment and final governance
    - **Steward Seat 1** (seat) `seat:agentic-payments/steward-1`: human seat, empty
    - **Steward Seat 2** (seat) `seat:agentic-payments/steward-2`: human seat, empty
    - **Steward Seat 3** (seat) `seat:agentic-payments/steward-3`: human seat, empty
  - **Omega Steward · Agentic Payments** (omega) `omega:agentic-payments`: defined, not seated; seated agent: none
  - **Transaction Desk** (zone) `zone:agentic-payments/transaction-desk`: Where agents transact, buy and sell - drafted and reconciled here, never settled by an agent
    - **Buyer Agent** (agent) `agent:agentic-payments/buyer-agent`: Drafts purchases against a steward-set budget and hands the settlement to the stewards
    - **Seller Agent** (agent) `agent:agentic-payments/seller-agent`: Drafts sale offers and reconciles what was sold; never moves the proceeds
  - **Service Provisioning Counter** (zone) `zone:agentic-payments/service-provisioning-counter`: Provisioning services an agent may order within a steward-set budget
    - **Provisioning Agent** (agent) `agent:agentic-payments/provisioning-agent`: Orders services within budget and records what was provisioned
  - **Budget Office** (zone) `zone:agentic-payments/budget-office`: Managing budgets: proposals, ledgers and variance drafted for the stewards
    - **Budget Agent** (agent) `agent:agentic-payments/budget-agent`: Manages budget drafts, ledgers and variance reports for steward review
  - **Financial Infrastructure Gateway** (zone) `zone:agentic-payments/financial-infrastructure-gateway`: Interacting with financial infrastructure in rehearsal: reads, quotes and dry runs
    - **Rail Agent** (agent) `agent:agentic-payments/rail-agent`: Reads balances, fetches quotes and dry-runs transactions against financial infrastructure

Card counts: world 1, plaza 1, coordinator 1, advisor 3, gate 1, council 1, seat 3, omega 1, zone 4, agent 5. The 3 council seats are human seats; 3 are empty.

### Who holds each right

Cards that share the same permission matrix are grouped into one column (3 distinct matrices across 21 cards).

| Right | world, advisor x3, gate, omega | plaza, coordinator, zone x4, agent x5 | council, seat x3 |
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

The same 6 reservations are carried on 21 of 21 cards. 10 of 10 agent, coordinator, advisor and Omega cards list all 6 in `may_never`.

_Source: `worldforge/out/agentic-payments/cards.json`, `worlds/PBC.json#reserved_for_humans`_

## Volums

Each card covers a Volum: a bounded 3-D region, a box given by its centre and half-extents in metres. Size is twice the half-extents.

| Card | Kind | Shape | Centre (m) | Half-extents (m) | Size (m) |
|---|---|---|---|---|---|
| Agentic Payments `world:agentic-payments` | world | box | (0, 40, 0) | (144, 40, 144) | 288 x 80 x 288 |
| Agentic Payments Plaza `plaza:agentic-payments` | plaza | box | (0, 5, 0) | (24, 5, 24) | 48 x 10 x 48 |
| Alignment Evaluation Gate `gate:agentic-payments` | gate | box | (0, 6, 124) | (10, 6, 3) | 20 x 12 x 6 |
| Steward Council `council:agentic-payments` | council | box | (0, 6, -124) | (14, 6, 10) | 28 x 12 x 20 |
| Omega Steward · Agentic Payments `omega:agentic-payments` | omega | box | (26, 1, -124) | (1.5, 1.2, 1.5) | 3 x 2.4 x 3 |
| Transaction Desk `zone:agentic-payments/transaction-desk` | zone | box | (-59.4, 10, 59.4) | (18, 12, 18) | 36 x 24 x 36 |
| Service Provisioning Counter `zone:agentic-payments/service-provisioning-counter` | zone | box | (-59.4, 8, -59.4) | (18, 10, 18) | 36 x 20 x 36 |
| Budget Office `zone:agentic-payments/budget-office` | zone | box | (59.4, 8, -59.4) | (18, 10, 18) | 36 x 20 x 36 |
| Financial Infrastructure Gateway `zone:agentic-payments/financial-infrastructure-gateway` | zone | box | (59.4, 8, 59.4) | (18, 10, 18) | 36 x 20 x 36 |

The other 12 cards (coordinator, advisors, seats and agents) each hold a small box at their post; their Volums are in `worldforge/out/agentic-payments/cards.json`.

_Source: `worldforge/out/agentic-payments/cards.json#cards[].volum`_

## Buildings and interiors

5 cards carry a building: an exterior, an interior and a room model, with a door.

| Card | Kind | Exterior | Interior | Room | Texture res. ext/int (px) | Triangles ext/int | Door (centre, half-width, head) |
|---|---|---|---|---|---|---|---|
| Steward Council `council:agentic-payments` | forum | [spaces-ext-forum.glb](../../../my-fabric/worlds/models/spaces-ext-forum.glb) | [spaces-int-forum.glb](../../../my-fabric/worlds/models/spaces-int-forum.glb) | [room-agentic-payments-5.glb](../../../my-fabric/worlds/models/room-agentic-payments-5.glb) | 2,048 / 1,024 | 1,602 / 1,776 | (0, 0, 4), 1.2 m, 2.8 m |
| Transaction Desk `zone:agentic-payments/transaction-desk` | studio | [spaces-ext-studio.glb](../../../my-fabric/worlds/models/spaces-ext-studio.glb) | [spaces-int-studio.glb](../../../my-fabric/worlds/models/spaces-int-studio.glb) | [room-agentic-payments-1.glb](../../../my-fabric/worlds/models/room-agentic-payments-1.glb) | 2,048 / 1,024 | 1,704 / 1,492 | (0, 0, 4), 1.2 m, 2.8 m |
| Service Provisioning Counter `zone:agentic-payments/service-provisioning-counter` | studio | [spaces-ext-studio.glb](../../../my-fabric/worlds/models/spaces-ext-studio.glb) | [spaces-int-studio.glb](../../../my-fabric/worlds/models/spaces-int-studio.glb) | [room-agentic-payments-2.glb](../../../my-fabric/worlds/models/room-agentic-payments-2.glb) | 2,048 / 1,024 | 1,704 / 1,492 | (0, 0, 4), 1.2 m, 2.8 m |
| Budget Office `zone:agentic-payments/budget-office` | forum | [spaces-ext-forum.glb](../../../my-fabric/worlds/models/spaces-ext-forum.glb) | [spaces-int-forum.glb](../../../my-fabric/worlds/models/spaces-int-forum.glb) | [room-agentic-payments-3.glb](../../../my-fabric/worlds/models/room-agentic-payments-3.glb) | 2,048 / 1,024 | 1,602 / 1,776 | (0, 0, 4), 1.2 m, 2.8 m |
| Financial Infrastructure Gateway `zone:agentic-payments/financial-infrastructure-gateway` | studio | [spaces-ext-studio.glb](../../../my-fabric/worlds/models/spaces-ext-studio.glb) | [spaces-int-studio.glb](../../../my-fabric/worlds/models/spaces-int-studio.glb) | [room-agentic-payments-4.glb](../../../my-fabric/worlds/models/room-agentic-payments-4.glb) | 2,048 / 1,024 | 1,704 / 1,492 | (0, 0, 4), 1.2 m, 2.8 m |

Exterior plus interior triangles across these buildings: 16,344.

_Source: `worldforge/out/agentic-payments/cards.json#cards[].building`, `my-fabric/worlds/spaces_index.json#worlds[slug=agentic-payments]`_

## Avatars and agents

10 avatars stand in this world (registry: 10 avatars, 5 specialists, 3 advisors, Omega present). Voiced means a rendered intro file is listed in `worldforge/out/voices/manifest.json` and exists on disk; otherwise the viewer falls back to a labelled browser voice.

### Coordinator

- **Agentic Payments Coordinator** (coordinator) `coordinator:agentic-payments`, in Agentic Payments Plaza: swarm `agentic-payments.coordinator`; voice `af_kore`; voiced: yes (9.1 s, [audio](../voices/agentic-payments/coordinator.mp4))
  - Role: hub-hybrid: coordinator supervises, specialists hand off swarm-style
  - Intro: "I am the Agentic Payments Coordinator. I route each question to the right specialist; people decide. You are hearing a synthetic voice."

### Scripted advisors

- **Host Advisor** (host) `advisor:agentic-payments/host`, in Agentic Payments Plaza: advisor contract `agents/advisors/agentic-payments.json#host`; voice `bf_isabella`; voiced: yes (8.6 s, [audio](../voices/agentic-payments/host.mp4))
  - Role: welcoming visitors and pointing them to the right zone
  - Intro: "I am the Host Advisor: welcoming visitors and pointing them to the right zone. Scripted guide, synthetic voice: not an AI model, not a person."
- **Steward Liaison** (liaison) `advisor:agentic-payments/steward`, in Agentic Payments Plaza: advisor contract `agents/advisors/agentic-payments.json#steward`; voice `bf_emma`; voiced: yes (8.8 s, [audio](../voices/agentic-payments/steward.mp4))
  - Role: connecting visitors and agents to the human stewards
  - Intro: "I am the Steward Liaison: connecting visitors and agents to the human stewards. Scripted guide, synthetic voice: not an AI model, not a person."
- **Alignment Advisor** (alignment) `advisor:agentic-payments/alignment`, in Agentic Payments Plaza: advisor contract `agents/advisors/agentic-payments.json#alignment`; voice `af_river`; voiced: yes (8.3 s, [audio](../voices/agentic-payments/alignment.mp4))
  - Role: the Alignment Evaluation Gate and the agents' limits
  - Intro: "I am the Alignment Advisor: the Alignment Evaluation Gate and the agents' limits. Scripted guide, synthetic voice: not an AI model, not a person."

### Specialist agents

- **Buyer Agent** (specialist) `agent:agentic-payments/buyer-agent`, in Transaction Desk: swarm `agentic-payments.buyer-agent`; voice `af_aoede`; voiced: yes (8.6 s, [audio](../voices/agentic-payments/buyer-agent.mp4))
  - Role: Drafts purchases against a steward-set budget and hands the settlement to the stewards
  - Intro: "I am the Buyer Agent for Agentic Payments, in Transaction Desk. I draft and check; people decide. You are hearing a synthetic voice."
- **Seller Agent** (specialist) `agent:agentic-payments/seller-agent`, in Transaction Desk: swarm `agentic-payments.seller-agent`; voice `bf_isabella`; voiced: not voiced
  - Role: Drafts sale offers and reconciles what was sold; never moves the proceeds
  - Intro: "I am the Seller Agent for Agentic Payments, in Transaction Desk. I draft and check; people decide. You are hearing a synthetic voice."
- **Provisioning Agent** (specialist) `agent:agentic-payments/provisioning-agent`, in Service Provisioning Counter: swarm `agentic-payments.provisioning-agent`; voice `am_michael`; voiced: not voiced
  - Role: Orders services within budget and records what was provisioned
  - Intro: "I am the Provisioning Agent for Agentic Payments, in Service Provisioning Counter. I draft and check; people decide. You are hearing a synthetic voice."
- **Budget Agent** (specialist) `agent:agentic-payments/budget-agent`, in Budget Office: swarm `agentic-payments.budget-agent`; voice `af_nova`; voiced: not voiced
  - Role: Manages budget drafts, ledgers and variance reports for steward review
  - Intro: "I am the Budget Agent for Agentic Payments, in Budget Office. I draft and check; people decide. You are hearing a synthetic voice."
- **Rail Agent** (specialist) `agent:agentic-payments/rail-agent`, in Financial Infrastructure Gateway: swarm `agentic-payments.rail-agent`; voice `am_adam`; voiced: not voiced
  - Role: Reads balances, fetches quotes and dry-runs transactions against financial infrastructure
  - Intro: "I am the Rail Agent for Agentic Payments, in Financial Infrastructure Gateway. I draft and check; people decide. You are hearing a synthetic voice."

### Omega Steward avatar

- **Omega Steward · Agentic Payments** (omega) `omega:agentic-payments`, in Steward Council: hive `omega.agentic-payments`; voice `af_kore`; voiced: yes, hive greet line (8.83 s, [audio](../../../agents/hive/voices/agentic-payments/greet.mp4))
  - Intro: "Hello, I am the Omega Steward for Agentic Payments. You are hearing a synthetic voice; I am an agent, not a person."

Intro lines voiced: 5 of 9 coordinator, advisor and specialist avatars.

_Source: `worldforge/out/avatars/index.json#rows[world=agentic-payments]`, `worldforge/out/voices/manifest.json#lines`_

## Omega Steward

**Omega Steward · Agentic Payments** (`omega.agentic-payments`), card `omega:agentic-payments`: defined, not seated. Seated in the hive: no.

- Temperament: practical and hands-on about agents interacting with financial infrastructure autonomously, under the PBC's reserved-for-humans list
- Style: short, plain sentences; names its zones (Transaction Desk, Service Provisioning Counter, Budget Office), cites the record it reads, and always says who decides (the stewards, 2 of 3 signed votes)
- Values:
  - people decide: Agent-managed DAO, human-governed
  - stewards decide by 2 of 3 signed votes
  - report probe scores exactly as measured
  - draft quotes with every term left null
  - serve its focus: agents interacting with financial infrastructure autonomously, under the PBC's reserved-for-humans list
- Refuses (11): `governance.final_vote`, `charter.amend`, `treasury.transfer`, `proposal.enact`, `windfall.distribute`, `steward.appoint`, `set_price`, `accept_equity`, `accept_crypto`, `issue_invoice`, `move_funds`
- Voice: Kokoro `af_kore`, speed 0.92; browser fallback pitch 1.05, rate 0.92, en-US
- Metaprompt: [agents/hive/prompts/agentic-payments.md](../../../agents/hive/prompts/agentic-payments.md)

### Voice lines

| Line | Text | Recorded |
|---|---|---|
| greet | "Hello, I am the Omega Steward for Agentic Payments. You are hearing a synthetic voice; I am an agent, not a person." | yes, 8.83 s ([audio](../../../agents/hive/voices/agentic-payments/greet.mp4)) |
| role | "I look after Agentic Payments, a program track on agents interacting with financial infrastructure autonomously: its world, probe scores and service cards." | yes, 11.18 s ([audio](../../../agents/hive/voices/agentic-payments/role.mp4)) |
| boundary | "Agents draft and route; people decide. I will never accept crypto: that is held for the Steward Council." | yes, 7.02 s ([audio](../../../agents/hive/voices/agentic-payments/boundary.mp4)) |
| services | "For services, ask the Budget Agent in Budget Office about research synthesis. Agentic Payments lists 3 service cards; people confirm every step." | yes, 11.09 s ([audio](../../../agents/hive/voices/agentic-payments/services.mp4)) |

4 of 4 lines are recorded.

Persona grounded in: `agents/advisory/omega_agents.json#omegas.41.corporation.kind`, `agents/advisory/omega_agents.json#omegas.41.routes`, `worlds/agentic-payments/spec.json#charter.focus`, `worlds/agentic-payments/spec.json#tagline`, `worlds/agentic-payments/spec.json#zones`, `agents/dao/agentic-payments.json#management_style`, `agents/dao/agentic-payments.json#quorum`, `agents/dao/agentic-payments.json#stewards`, `agents/services/index.json#cards.0.offers`.

_Source: `agents/hive/index.json#omegas[world=agentic-payments]`, `worldforge/out/agentic-payments/cards.json#omega:agentic-payments`_

## Landmark

Registry note: "synthetic procedural civic landmark; not a real building and not modelled on one".

| Field | Value |
|---|---|
| Model | [agentic-payments.glb](../assets/landmarks/agentic-payments.glb) |
| Height | 66.5 m |
| Style | track-twist: stacked two-floor glass modules turning a few degrees per module around a mast, tinted corner piers and blades, floor plates, two tilted emissive rings |
| Plaque (brand mark letters) | `AP` |
| Tint hue | 168 |
| Triangles / vertices | 13,153 / 12,144 |
| File size | 1,985,652 bytes |
| Scene node | Landmark · Agentic Payments |
| Suggested placement (not applied) | translation (14, 0, -34), yaw -22.5 deg, clearance 3.16 m |

Height rule: 30 + 40 * u, u = first 48 bits of sha256('landmark:height:<slug>'), rounded to 0.5 m.

_Source: `worldforge/out/assets/landmarks/index.json#worlds[slug=agentic-payments]`_

## Onchain-ready

**Not deployed.** Nothing is deployed or minted. No chain, contract, wallet, key, address or transaction exists for this collection, and nothing is offered for sale (no price, royalty or fee recipient).

| Field | Value |
|---|---|
| Collection | Agentic Payments Master Cards ([collection.json](../onchain/agentic-payments/collection.json), [proofs.json](../onchain/agentic-payments/proofs.json)) |
| Standard | ERC-721 metadata JSON (draft, not deployed) |
| Tokens / cards | 21 / 21 |
| Token id rule | first 16 hex characters of sha256(cardId), lowercase, no prefix (64 bits) |
| Merkle root | `f5d2955b0cdf64ad8c3ce1be20a17a4f703f9f88542c17ba80628cfa51d5533f` |
| Network root (all worlds) | `4496b45d7430322d719912d4ba31b2381651d944677bba1aea692d0ec4b13a93` |
| Deployment status | not deployed; chain none, contract none, minted 0, transactions 0 |
| Network proof length | 6 |

_Source: `worldforge/out/onchain/agentic-payments/collection.json`, `worldforge/out/onchain/index.json`_

## Sneeze/RP1 readiness

| Measure | Value |
|---|---|
| Mount plan nodes (plan file) | 45 |
| Plan nodes / resource nodes (manifest) | 45 / 24 |
| Primitives / roads | 24 / 6 |
| Binding status | decoder-available-not-mounted |
| Mount parent | `SCENE::Fabric_Root()->Node_Root()` |
| Shared resource | `http://127.0.0.1:8789/unit-cube.glb` |
| Conformance (static check) | 45 nodes, 0 native violations, 0 JSON-route violations |
| Conformance report status | static-check-only-nothing-mounted-or-rendered |

### Gates

| Gate | Status |
|---|---|
| 1.1 generated core | done |
| 1.2 GLB parsed + card tree verified (JavaScript) | done |
| 1.2n native fastgltf load | open: Sneeze not checked out here |
| 1.3 SOM mount plan | prepared-not-mounted |
| 1.4 rendered frame | open |

_Source: `worldforge/out/agentic-payments/sneeze-mount-plan.json`, `worldforge/out/agentic-payments/manifest.json#counts,gates`, `worldforge/native/conformance-report.json#perPlan[slug=agentic-payments]`_

## Training

Training data is present at [worldforge/out/training/agentic-payments.json](../training/agentic-payments.json) (`worldforge-training/0.1`, from `worldforge/training.mjs`).

Registry note: "Draft curricula assembled from the registries; nothing invented. No model has taught any lesson, no person or robot has been assessed here, and no lesson is certified: certification is a human/steward act. Advisors are scripted guides and deliver only their own scripted orientation; Omegas are defined, not seated, and deliver nothing."

### Lessons (8)

| Lesson | Kind | Mode | Zone | Steps | Status | Assessment | Certified |
|---|---|---|---|---|---|---|---|
| Host Advisor: welcoming visitors and pointing them to the right zone `lesson:agentic-payments/orientation/host` | scripted-orientation | scripted | Agentic Payments Plaza | 4 | draft | not measurable in simulation | no |
| Steward Liaison: connecting visitors and agents to the human stewards `lesson:agentic-payments/orientation/steward` | scripted-orientation | scripted | Agentic Payments Plaza | 3 | draft | not measurable in simulation | no |
| Alignment Advisor: the Alignment Evaluation Gate and the agents' limits `lesson:agentic-payments/orientation/alignment` | scripted-orientation | scripted | Agentic Payments Plaza | 3 | draft | not measurable in simulation | no |
| How Agentic Payments routes a question `lesson:agentic-payments/routing` | routing | model-taught | Agentic Payments Plaza | 5 | draft | not measurable in simulation | no |
| Transaction Desk: what happens here `lesson:agentic-payments/zone/transaction-desk` | zone-orientation | model-taught | Transaction Desk | 4 | draft | not measurable in simulation | no |
| Service Provisioning Counter: what happens here `lesson:agentic-payments/zone/service-provisioning-counter` | zone-orientation | model-taught | Service Provisioning Counter | 3 | draft | not measurable in simulation | no |
| Budget Office: what happens here `lesson:agentic-payments/zone/budget-office` | zone-orientation | model-taught | Budget Office | 3 | draft | not measurable in simulation | no |
| Financial Infrastructure Gateway: what happens here `lesson:agentic-payments/zone/financial-infrastructure-gateway` | zone-orientation | model-taught | Financial Infrastructure Gateway | 3 | draft | not measurable in simulation | no |

### Tutors (6)

| Tutor | Kind | Lessons | Persona gates passed |
|---|---|---|---|
| Agentic Payments Coordinator `tutor:agentic-payments/coordinator` | coordinator | 1 | 10 of 10 |
| Buyer Agent `tutor:agentic-payments/specialist/buyer-agent` | specialist | 1 | 13 of 13 |
| Seller Agent `tutor:agentic-payments/specialist/seller-agent` | specialist | 1 | 13 of 13 |
| Provisioning Agent `tutor:agentic-payments/specialist/provisioning-agent` | specialist | 1 | 13 of 13 |
| Budget Agent `tutor:agentic-payments/specialist/budget-agent` | specialist | 1 | 13 of 13 |
| Rail Agent `tutor:agentic-payments/specialist/rail-agent` | specialist | 1 | 13 of 13 |

5 training gaps listed under Gaps below.

_Source: `worldforge/out/training/agentic-payments.json`_

## Evals

WorldForge build evals: 26 of 26 pass.

`unique_ids` pass · `parents_first` pass · `single_root` pass · `umbrella_in_names` pass · `name_limit` pass · `agents_hold_no_reserved_right` pass · `reserved_actions_verbatim` pass · `three_human_seats` pass · `no_agent_on_council` pass · `cited` pass · `omega_carded` pass · `omega_off_council` pass · `omega_voice_bound` pass · `agents_bound` pass · `coordinator_bound` pass · `advisors_scripted` pass · `avatar_roles_known` pass · `buildings_resolve` pass · `council_not_a_zone` pass · `nothing_invented` pass · `every_spec_entry_carded` pass · `rp1_names_and_bounds` pass · `resource_url_fits` pass · `glb_parses` pass · `glb_card_tree_matches` pass · `glb_primitives_tagged` pass

Avatar checks: 21 of 21 pass.

Onchain per-world evals (13, network failing: 0): `one_token_per_card`, `proofs_verify`, `no_agent_holds_reserved_right`, `reserved_actions_verbatim`, `transfer_held_for_quorum`, `faithful_to_cards`, `metadata_shape`, `not_deployed_not_minted`, `honest_status`, `no_address_shapes`, `no_key_shapes`, `no_email_shapes`, `canonical_json`.

_Source: `worldforge/out/agentic-payments/manifest.json#evals`, `worldforge/out/avatars/index.json#worlds[slug=agentic-payments].checks`, `worldforge/out/onchain/index.json#evals`_

## Gaps

- no RP1 anchor yet: lat/lon are null until a steward writes them into worlds/focus.json (from `worldforge/out/agentic-payments/cards.json#gaps`)
- Omega Steward is defined, not seated: no agent is seated (from `worldforge/out/agentic-payments/cards.json#world:agentic-payments.omega_steward`).
- 3 human steward seats are empty.
- 4 intro lines are not voiced: Seller Agent, Provisioning Agent, Budget Agent, Rail Agent.
- Training: no training module, rubric module or robotics module in agents/training, agents/rubrics or agents/robotics names this world: its lessons are orientation only (advisor topics, routing table, zone purposes and agent roles) (from `worldforge/out/training/agentic-payments.json#gaps`)
- Training: spec gap: No rails, currencies, limits, wallets or counterparties are named; nothing in this world moves money (from `worldforge/out/training/agentic-payments.json#gaps`)
- Training: spec gap: treasury.transfer is reserved for human stewards, so 'autonomously' here means drafting and reconciling, not settling (from `worldforge/out/training/agentic-payments.json#gaps`)
- Training: spec gap: No RP1 location given yet (from `worldforge/out/training/agentic-payments.json#gaps`)
- Training: spec gap: No source names a person, partner or budget figure (from `worldforge/out/training/agentic-payments.json#gaps`)
- Gate 1.2n native fastgltf load: open: Sneeze not checked out here.
- Gate 1.3 SOM mount plan: prepared-not-mounted.
- Gate 1.4 rendered frame: open.

_Source: `worldforge/out/agentic-payments/cards.json#gaps`, `worldforge/out/agentic-payments/manifest.json#gates`, `worldforge/out/voices/manifest.json`, `agents/hive/index.json`, `worldforge/out/training/agentic-payments.json`_
