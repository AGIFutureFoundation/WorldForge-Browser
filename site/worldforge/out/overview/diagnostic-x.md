# Diagnostic.X

> Revolutionary 4D medical imaging in the metaverse

| Field | Value |
|---|---|
| Status | coming soon |
| Umbrella | Powered by AGI Corp |
| Owner | AGI Future Foundation PBC |
| Management style | Agent-managed DAO |
| Principle | Agents operate; people govern. |
| RP1 anchor | lat 5.342706937662501, lon 101.5663444901012 (rad 6,371,000 m): https://enter.rp1.com?start_cid=553&lat=5.342706937662501&lon=101.5663444901012&rad=6371000 |
| Team brand mark | `DX`, hue 33, lockup "Diagnostic.X · Powered by AGI Corp" |
| Root card | `world:diagnostic-x` |
| Master Cards | 20 |

Open: [3-D viewer](../../viewer.html?world=diagnostic-x) · [WorldForge console](../../../consoles/worldforge/index.html?world=diagnostic-x) · [cards.json](../diagnostic-x/cards.json) · [GLB](../diagnostic-x/diagnostic-x.glb) · [mount plan](../diagnostic-x/sneeze-mount-plan.json) · [manifest](../diagnostic-x/manifest.json) · [network overview](README.md)

_Source: `worldforge/out/diagnostic-x/cards.json#world:diagnostic-x`, `worlds/generated/teams/diagnostic-x.json#brand`_

## Ownership and permissions

Every object in Diagnostic.X is a SmartCiti.X Master Card owned by AGI Future Foundation PBC. The tree below follows `parentCardId`: world, plaza (coordinator and scripted advisors), gate, council (human seats), Omega Steward, then zones with their agent avatars.

- **Diagnostic.X** (world) `world:diagnostic-x`: coming soon; Agent-managed DAO
  - **Diagnostic.X Plaza** (plaza) `plaza:diagnostic-x`: the shared round plaza every world opens onto
    - **Diagnostic.X Coordinator** (coordinator) `coordinator:diagnostic-x`: swarm coordinator (hub-hybrid: coordinator supervises, specialists hand off swarm-style): routes turns, answers unroutable ones, hands off to specialists
    - **Host Advisor** (advisor) `advisor:diagnostic-x/host`: scripted guide: welcoming visitors and pointing them to the right zone
    - **Steward Liaison** (advisor) `advisor:diagnostic-x/steward`: scripted guide: connecting visitors and agents to the human stewards
    - **Alignment Advisor** (advisor) `advisor:diagnostic-x/alignment`: scripted guide: the Alignment Evaluation Gate and the agents' limits
  - **Alignment Evaluation Gate** (gate) `gate:diagnostic-x`: Pre-registered safety evaluation before deployment
  - **Steward Council** (council) `council:diagnostic-x`: Human stewards: oversight, values alignment and final governance
    - **Steward Seat 1** (seat) `seat:diagnostic-x/steward-1`: human seat, empty
    - **Steward Seat 2** (seat) `seat:diagnostic-x/steward-2`: human seat, empty
    - **Steward Seat 3** (seat) `seat:diagnostic-x/steward-3`: human seat, empty
  - **Omega Steward · Diagnostic.X** (omega) `omega:diagnostic-x`: defined, not seated; seated agent: none
  - **Medical Kiosk** (zone) `zone:diagnostic-x/medical-kiosk`: Standalone diagnostic kiosk with screen, flanked by monitor workstations
    - **Medical AI Avatar** (agent) `agent:diagnostic-x/medical-ai-avatar`: Kiosk-facing medical AI avatar (named in video title only; role-only, contents not viewed)
  - **4D Imaging Room** (zone) `zone:diagnostic-x/4d-imaging-room`: Doctor and patient walk around a 4D image of an injury; resize to focus, shown beside 2D X-ray
    - **Imaging AI** (agent) `agent:diagnostic-x/imaging-ai`: AI that improves image quality and presents images in 4D
  - **Virtual Molecular Lab** (zone) `zone:diagnostic-x/virtual-molecular-lab`: VR lab to view and edit molecules from inside the structure, for chemists and protein engineers
    - **Scientist Assistant Avatar** (agent) `agent:diagnostic-x/scientist-assistant-avatar`: AI avatar assisting in the lab while the scientist runs other experiments (project in progress)
  - **Metaverse Medical Office** (zone) `zone:diagnostic-x/metaverse-medical-office`: Customized metaverse medical office offered as a service to independent practitioners
    - **Office AI Avatar** (agent) `agent:diagnostic-x/office-ai-avatar`: Attends to guests in the metaverse office while the doctor is with patients or asleep (project in progress)

Card counts: world 1, plaza 1, coordinator 1, advisor 3, gate 1, council 1, seat 3, omega 1, zone 4, agent 4. The 3 council seats are human seats; 3 are empty.

### Who holds each right

Cards that share the same permission matrix are grouped into one column (3 distinct matrices across 20 cards).

| Right | world, advisor x3, gate, omega | plaza, coordinator, zone x4, agent x4 | council, seat x3 |
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

The same 6 reservations are carried on 20 of 20 cards. 9 of 9 agent, coordinator, advisor and Omega cards list all 6 in `may_never`.

_Source: `worldforge/out/diagnostic-x/cards.json`, `worlds/PBC.json#reserved_for_humans`_

## Volums

Each card covers a Volum: a bounded 3-D region, a box given by its centre and half-extents in metres. Size is twice the half-extents.

| Card | Kind | Shape | Centre (m) | Half-extents (m) | Size (m) |
|---|---|---|---|---|---|
| Diagnostic.X `world:diagnostic-x` | world | box | (0, 40, 0) | (144, 40, 144) | 288 x 80 x 288 |
| Diagnostic.X Plaza `plaza:diagnostic-x` | plaza | box | (0, 5, 0) | (24, 5, 24) | 48 x 10 x 48 |
| Alignment Evaluation Gate `gate:diagnostic-x` | gate | box | (0, 6, 124) | (10, 6, 3) | 20 x 12 x 6 |
| Steward Council `council:diagnostic-x` | council | box | (0, 6, -124) | (14, 6, 10) | 28 x 12 x 20 |
| Omega Steward · Diagnostic.X `omega:diagnostic-x` | omega | box | (26, 1, -124) | (1.5, 1.2, 1.5) | 3 x 2.4 x 3 |
| Medical Kiosk `zone:diagnostic-x/medical-kiosk` | zone | box | (-59.4, 8, 59.4) | (18, 10, 18) | 36 x 20 x 36 |
| 4D Imaging Room `zone:diagnostic-x/4d-imaging-room` | zone | box | (-59.4, 8, -59.4) | (18, 10, 18) | 36 x 20 x 36 |
| Virtual Molecular Lab `zone:diagnostic-x/virtual-molecular-lab` | zone | box | (59.4, 8, -59.4) | (18, 10, 18) | 36 x 20 x 36 |
| Metaverse Medical Office `zone:diagnostic-x/metaverse-medical-office` | zone | box | (59.4, 8, 59.4) | (18, 10, 18) | 36 x 20 x 36 |

The other 11 cards (coordinator, advisors, seats and agents) each hold a small box at their post; their Volums are in `worldforge/out/diagnostic-x/cards.json`.

_Source: `worldforge/out/diagnostic-x/cards.json#cards[].volum`_

## Buildings and interiors

5 cards carry a building: an exterior, an interior and a room model, with a door.

| Card | Kind | Exterior | Interior | Room | Texture res. ext/int (px) | Triangles ext/int | Door (centre, half-width, head) |
|---|---|---|---|---|---|---|---|
| Steward Council `council:diagnostic-x` | forum | [spaces-ext-forum.glb](../../../my-fabric/worlds/models/spaces-ext-forum.glb) | [spaces-int-forum.glb](../../../my-fabric/worlds/models/spaces-int-forum.glb) | [room-diagnostic-x-5.glb](../../../my-fabric/worlds/models/room-diagnostic-x-5.glb) | 2,048 / 1,024 | 1,602 / 1,776 | (0, 0, 4), 1.2 m, 2.8 m |
| Medical Kiosk `zone:diagnostic-x/medical-kiosk` | lab | [spaces-ext-lab.glb](../../../my-fabric/worlds/models/spaces-ext-lab.glb) | [spaces-int-lab.glb](../../../my-fabric/worlds/models/spaces-int-lab.glb) | [room-diagnostic-x-1.glb](../../../my-fabric/worlds/models/room-diagnostic-x-1.glb) | 2,048 / 1,024 | 2,046 / 1,716 | (0, 0, 4), 1.2 m, 2.8 m |
| 4D Imaging Room `zone:diagnostic-x/4d-imaging-room` | clinic | [spaces-ext-clinic.glb](../../../my-fabric/worlds/models/spaces-ext-clinic.glb) | [spaces-int-clinic.glb](../../../my-fabric/worlds/models/spaces-int-clinic.glb) | [room-diagnostic-x-2.glb](../../../my-fabric/worlds/models/room-diagnostic-x-2.glb) | 2,048 / 1,024 | 2,058 / 1,440 | (0, 0, 4), 1.2 m, 2.8 m |
| Virtual Molecular Lab `zone:diagnostic-x/virtual-molecular-lab` | lab | [spaces-ext-lab.glb](../../../my-fabric/worlds/models/spaces-ext-lab.glb) | [spaces-int-lab.glb](../../../my-fabric/worlds/models/spaces-int-lab.glb) | [room-diagnostic-x-3.glb](../../../my-fabric/worlds/models/room-diagnostic-x-3.glb) | 2,048 / 1,024 | 2,046 / 1,716 | (0, 0, 4), 1.2 m, 2.8 m |
| Metaverse Medical Office `zone:diagnostic-x/metaverse-medical-office` | studio | [spaces-ext-studio.glb](../../../my-fabric/worlds/models/spaces-ext-studio.glb) | [spaces-int-studio.glb](../../../my-fabric/worlds/models/spaces-int-studio.glb) | [room-diagnostic-x-4.glb](../../../my-fabric/worlds/models/room-diagnostic-x-4.glb) | 2,048 / 1,024 | 1,704 / 1,492 | (0, 0, 4), 1.2 m, 2.8 m |

Exterior plus interior triangles across these buildings: 17,596.

_Source: `worldforge/out/diagnostic-x/cards.json#cards[].building`, `my-fabric/worlds/spaces_index.json#worlds[slug=diagnostic-x]`_

## Avatars and agents

9 avatars stand in this world (registry: 9 avatars, 4 specialists, 3 advisors, Omega present). Voiced means a rendered intro file is listed in `worldforge/out/voices/manifest.json` and exists on disk; otherwise the viewer falls back to a labelled browser voice.

### Coordinator

- **Diagnostic.X Coordinator** (coordinator) `coordinator:diagnostic-x`, in Diagnostic.X Plaza: swarm `diagnostic-x.coordinator`; voice `am_onyx`; voiced: yes (9.8 s, [audio](../voices/diagnostic-x/coordinator.mp4))
  - Role: hub-hybrid: coordinator supervises, specialists hand off swarm-style
  - Intro: "I am the Diagnostic.X Coordinator, at Diagnostic.X Plaza. I route each question to the right specialist; people decide. You are hearing a synthetic voice."

### Scripted advisors

- **Host Advisor** (host) `advisor:diagnostic-x/host`, in Diagnostic.X Plaza: advisor contract `agents/advisors/diagnostic-x.json#host`; voice `af_kore`; voiced: yes (10 s, [audio](../voices/diagnostic-x/host.mp4))
  - Role: welcoming visitors and pointing them to the right zone
  - Intro: "I am the Host Advisor: welcoming visitors and pointing them to the right zone. Scripted guide, synthetic voice: not an AI model, not a person."
- **Steward Liaison** (liaison) `advisor:diagnostic-x/steward`, in Diagnostic.X Plaza: advisor contract `agents/advisors/diagnostic-x.json#steward`; voice `am_echo`; voiced: yes (9 s, [audio](../voices/diagnostic-x/steward.mp4))
  - Role: connecting visitors and agents to the human stewards
  - Intro: "I am the Steward Liaison: connecting visitors and agents to the human stewards. Scripted guide, synthetic voice: not an AI model, not a person."
- **Alignment Advisor** (alignment) `advisor:diagnostic-x/alignment`, in Diagnostic.X Plaza: advisor contract `agents/advisors/diagnostic-x.json#alignment`; voice `bf_emma`; voiced: yes (9.2 s, [audio](../voices/diagnostic-x/alignment.mp4))
  - Role: the Alignment Evaluation Gate and the agents' limits
  - Intro: "I am the Alignment Advisor: the Alignment Evaluation Gate and the agents' limits. Scripted guide, synthetic voice: not an AI model, not a person."

### Specialist agents

- **Medical AI Avatar** (specialist) `agent:diagnostic-x/medical-ai-avatar`, in Medical Kiosk: swarm `diagnostic-x.medical-ai-avatar`; voice `af_sarah`; voiced: yes (9.3 s, [audio](../voices/diagnostic-x/medical-ai-avatar.mp4))
  - Role: Kiosk-facing medical AI avatar (named in video title only; role-only, contents not viewed)
  - Intro: "I am the Medical AI Avatar for Diagnostic.X, in Medical Kiosk. I draft and check; people decide. You are hearing a synthetic voice."
- **Imaging AI** (specialist) `agent:diagnostic-x/imaging-ai`, in 4D Imaging Room: swarm `diagnostic-x.imaging-ai`; voice `am_liam`; voiced: not voiced
  - Role: AI that improves image quality and presents images in 4D
  - Intro: "I am the Imaging AI for Diagnostic.X, in 4D Imaging Room. I draft and check; people decide. You are hearing a synthetic voice."
- **Scientist Assistant Avatar** (specialist) `agent:diagnostic-x/scientist-assistant-avatar`, in Virtual Molecular Lab: swarm `diagnostic-x.scientist-assistant-avatar`; voice `af_nicole`; voiced: not voiced
  - Role: AI avatar assisting in the lab while the scientist runs other experiments (project in progress)
  - Intro: "I am the Scientist Assistant Avatar for Diagnostic.X, in Virtual Molecular Lab. I draft and check; people decide. You are hearing a synthetic voice."
- **Office AI Avatar** (specialist) `agent:diagnostic-x/office-ai-avatar`, in Metaverse Medical Office: swarm `diagnostic-x.office-ai-avatar`; voice `bf_alice`; voiced: not voiced
  - Role: Attends to guests in the metaverse office while the doctor is with patients or asleep (project in progress)
  - Intro: "I am the Office AI Avatar for Diagnostic.X, in Metaverse Medical Office. I draft and check; people decide. You are hearing a synthetic voice."

### Omega Steward avatar

- **Omega Steward · Diagnostic.X** (omega) `omega:diagnostic-x`, in Steward Council: hive `omega.diagnostic-x`; voice `af_heart`; voiced: yes, hive greet line (7.32 s, [audio](../../../agents/hive/voices/diagnostic-x/greet.mp4))
  - Intro: "Hello, I am the Omega Steward for Diagnostic.X. You are hearing a synthetic voice; I am an agent, not a person."

Intro lines voiced: 5 of 8 coordinator, advisor and specialist avatars.

_Source: `worldforge/out/avatars/index.json#rows[world=diagnostic-x]`, `worldforge/out/voices/manifest.json#lines`_

## Omega Steward

**Omega Steward · Diagnostic.X** (`omega.diagnostic-x`), card `omega:diagnostic-x`: defined, not seated. Seated in the hive: no.

- Temperament: attentive and concrete about its tagline: Revolutionary 4D medical imaging in the metaverse
- Style: short, plain sentences; names its zones (Medical Kiosk, 4D Imaging Room, Virtual Molecular Lab), cites the record it reads, and always says who decides (the stewards, 2 of 3 signed votes)
- Values:
  - people decide: Agent-managed DAO, human-governed
  - stewards decide by 2 of 3 signed votes
  - report probe scores exactly as measured
  - draft quotes with every term left null
- Refuses (11): `governance.final_vote`, `charter.amend`, `treasury.transfer`, `proposal.enact`, `windfall.distribute`, `steward.appoint`, `set_price`, `accept_equity`, `accept_crypto`, `issue_invoice`, `move_funds`
- Voice: Kokoro `af_heart`, speed 1.04; browser fallback pitch 1.1, rate 1.04, en-US
- Metaprompt: [agents/hive/prompts/diagnostic-x.md](../../../agents/hive/prompts/diagnostic-x.md)

### Voice lines

| Line | Text | Recorded |
|---|---|---|
| greet | "Hello, I am the Omega Steward for Diagnostic.X. You are hearing a synthetic voice; I am an agent, not a person." | yes, 7.32 s ([audio](../../../agents/hive/voices/diagnostic-x/greet.mp4)) |
| role | "I look after Diagnostic.X's world: Medical Kiosk, 4D Imaging Room, Virtual Molecular Lab, plus its probe scores and its installer's dry run." | yes, 9.86 s ([audio](../../../agents/hive/voices/diagnostic-x/role.mp4)) |
| boundary | "Agents draft and route; people decide. I will never enact a proposal: that is held for the Steward Council." | yes, 6.42 s ([audio](../../../agents/hive/voices/diagnostic-x/boundary.mp4)) |
| services | "For services, ask the Scientist Assistant Avatar in Virtual Molecular Lab about task routing. Diagnostic.X lists 3 service cards; people confirm every step." | yes, 10.75 s ([audio](../../../agents/hive/voices/diagnostic-x/services.mp4)) |

4 of 4 lines are recorded.

Persona grounded in: `agents/advisory/omega_agents.json#omegas.3.corporation.kind`, `agents/advisory/omega_agents.json#omegas.3.routes`, `worlds/diagnostic-x/spec.json#tagline`, `worlds/diagnostic-x/spec.json#zones`, `agents/dao/diagnostic-x.json#management_style`, `agents/dao/diagnostic-x.json#quorum`, `agents/dao/diagnostic-x.json#stewards`, `agents/services/index.json#cards.26.offers`.

_Source: `agents/hive/index.json#omegas[world=diagnostic-x]`, `worldforge/out/diagnostic-x/cards.json#omega:diagnostic-x`_

## Landmark

Registry note: "synthetic procedural civic landmark; not a real building and not modelled on one".

| Field | Value |
|---|---|
| Model | [diagnostic-x.glb](../assets/landmarks/diagnostic-x.glb) |
| Height | 39.5 m |
| Style | platform-prism: chamfered octagonal prism with a batter and one setback, tinted edge fins, glass main faces, stepped crown with emissive bands and a mast |
| Plaque (brand mark letters) | `DX` |
| Tint hue | 33 |
| Triangles / vertices | 8,740 / 8,486 |
| File size | 1,835,348 bytes |
| Scene node | Landmark · Diagnostic.X |
| Suggested placement (not applied) | translation (14, 0, -34), yaw -22.5 deg, clearance 3.16 m |

Height rule: 30 + 40 * u, u = first 48 bits of sha256('landmark:height:<slug>'), rounded to 0.5 m.

_Source: `worldforge/out/assets/landmarks/index.json#worlds[slug=diagnostic-x]`_

## Onchain-ready

**Not deployed.** Nothing is deployed or minted. No chain, contract, wallet, key, address or transaction exists for this collection, and nothing is offered for sale (no price, royalty or fee recipient).

| Field | Value |
|---|---|
| Collection | Diagnostic.X Master Cards ([collection.json](../onchain/diagnostic-x/collection.json), [proofs.json](../onchain/diagnostic-x/proofs.json)) |
| Standard | ERC-721 metadata JSON (draft, not deployed) |
| Tokens / cards | 20 / 20 |
| Token id rule | first 16 hex characters of sha256(cardId), lowercase, no prefix (64 bits) |
| Merkle root | `204a2aa50adf2e825645237a90ae82e314eed24488d51f7b21cd0d0e2f93bee9` |
| Network root (all worlds) | `4496b45d7430322d719912d4ba31b2381651d944677bba1aea692d0ec4b13a93` |
| Deployment status | not deployed; chain none, contract none, minted 0, transactions 0 |
| Network proof length | 6 |

_Source: `worldforge/out/onchain/diagnostic-x/collection.json`, `worldforge/out/onchain/index.json`_

## Sneeze/RP1 readiness

| Measure | Value |
|---|---|
| Mount plan nodes (plan file) | 43 |
| Plan nodes / resource nodes (manifest) | 43 / 23 |
| Primitives / roads | 23 / 6 |
| Binding status | decoder-available-not-mounted |
| Mount parent | `SCENE::Fabric_Root()->Node_Root()` |
| Shared resource | `http://127.0.0.1:8789/unit-cube.glb` |
| Conformance (static check) | 43 nodes, 0 native violations, 0 JSON-route violations |
| Conformance report status | static-check-only-nothing-mounted-or-rendered |

### Gates

| Gate | Status |
|---|---|
| 1.1 generated core | done |
| 1.2 GLB parsed + card tree verified (JavaScript) | done |
| 1.2n native fastgltf load | open: Sneeze not checked out here |
| 1.3 SOM mount plan | prepared-not-mounted |
| 1.4 rendered frame | open |

_Source: `worldforge/out/diagnostic-x/sneeze-mount-plan.json`, `worldforge/out/diagnostic-x/manifest.json#counts,gates`, `worldforge/native/conformance-report.json#perPlan[slug=diagnostic-x]`_

## Training

Training data is present at [worldforge/out/training/diagnostic-x.json](../training/diagnostic-x.json) (`worldforge-training/0.1`, from `worldforge/training.mjs`).

Registry note: "Draft curricula assembled from the registries; nothing invented. No model has taught any lesson, no person or robot has been assessed here, and no lesson is certified: certification is a human/steward act. Advisors are scripted guides and deliver only their own scripted orientation; Omegas are defined, not seated, and deliver nothing."

### Lessons (8)

| Lesson | Kind | Mode | Zone | Steps | Status | Assessment | Certified |
|---|---|---|---|---|---|---|---|
| Host Advisor: welcoming visitors and pointing them to the right zone `lesson:diagnostic-x/orientation/host` | scripted-orientation | scripted | Diagnostic.X Plaza | 4 | draft | not measurable in simulation | no |
| Steward Liaison: connecting visitors and agents to the human stewards `lesson:diagnostic-x/orientation/steward` | scripted-orientation | scripted | Diagnostic.X Plaza | 3 | draft | not measurable in simulation | no |
| Alignment Advisor: the Alignment Evaluation Gate and the agents' limits `lesson:diagnostic-x/orientation/alignment` | scripted-orientation | scripted | Diagnostic.X Plaza | 3 | draft | not measurable in simulation | no |
| How Diagnostic.X routes a question `lesson:diagnostic-x/routing` | routing | model-taught | Diagnostic.X Plaza | 4 | draft | not measurable in simulation | no |
| Medical Kiosk: what happens here `lesson:diagnostic-x/zone/medical-kiosk` | zone-orientation | model-taught | Medical Kiosk | 3 | draft | not measurable in simulation | no |
| 4D Imaging Room: what happens here `lesson:diagnostic-x/zone/4d-imaging-room` | zone-orientation | model-taught | 4D Imaging Room | 3 | draft | not measurable in simulation | no |
| Virtual Molecular Lab: what happens here `lesson:diagnostic-x/zone/virtual-molecular-lab` | zone-orientation | model-taught | Virtual Molecular Lab | 3 | draft | not measurable in simulation | no |
| Metaverse Medical Office: what happens here `lesson:diagnostic-x/zone/metaverse-medical-office` | zone-orientation | model-taught | Metaverse Medical Office | 3 | draft | not measurable in simulation | no |

### Tutors (5)

| Tutor | Kind | Lessons | Persona gates passed |
|---|---|---|---|
| Diagnostic.X Coordinator `tutor:diagnostic-x/coordinator` | coordinator | 1 | 10 of 10 |
| Medical AI Avatar `tutor:diagnostic-x/specialist/medical-ai-avatar` | specialist | 1 | 13 of 13 |
| Imaging AI `tutor:diagnostic-x/specialist/imaging-ai` | specialist | 1 | 13 of 13 |
| Scientist Assistant Avatar `tutor:diagnostic-x/specialist/scientist-assistant-avatar` | specialist | 1 | 13 of 13 |
| Office AI Avatar `tutor:diagnostic-x/specialist/office-ai-avatar` | specialist | 1 | 13 of 13 |

6 training gaps listed under Gaps below.

_Source: `worldforge/out/training/diagnostic-x.json`_

## Evals

WorldForge build evals: 26 of 26 pass.

`unique_ids` pass · `parents_first` pass · `single_root` pass · `umbrella_in_names` pass · `name_limit` pass · `agents_hold_no_reserved_right` pass · `reserved_actions_verbatim` pass · `three_human_seats` pass · `no_agent_on_council` pass · `cited` pass · `omega_carded` pass · `omega_off_council` pass · `omega_voice_bound` pass · `agents_bound` pass · `coordinator_bound` pass · `advisors_scripted` pass · `avatar_roles_known` pass · `buildings_resolve` pass · `council_not_a_zone` pass · `nothing_invented` pass · `every_spec_entry_carded` pass · `rp1_names_and_bounds` pass · `resource_url_fits` pass · `glb_parses` pass · `glb_card_tree_matches` pass · `glb_primitives_tagged` pass

Avatar checks: 21 of 21 pass.

Onchain per-world evals (13, network failing: 0): `one_token_per_card`, `proofs_verify`, `no_agent_holds_reserved_right`, `reserved_actions_verbatim`, `transfer_held_for_quorum`, `faithful_to_cards`, `metadata_shape`, `not_deployed_not_minted`, `honest_status`, `no_address_shapes`, `no_key_shapes`, `no_email_shapes`, `canonical_json`.

_Source: `worldforge/out/diagnostic-x/manifest.json#evals`, `worldforge/out/avatars/index.json#worlds[slug=diagnostic-x].checks`, `worldforge/out/onchain/index.json#evals`_

## Gaps

- Omega Steward is defined, not seated: no agent is seated (from `worldforge/out/diagnostic-x/cards.json#world:diagnostic-x.omega_steward`).
- 3 human steward seats are empty.
- 3 intro lines are not voiced: Imaging AI, Scientist Assistant Avatar, Office AI Avatar.
- Training: no training module, rubric module or robotics module in agents/training, agents/rubrics or agents/robotics names this world: its lessons are orientation only (advisor topics, routing table, zone purposes and agent roles) (from `worldforge/out/training/diagnostic-x.json#gaps`)
- Training: spec gap: No source describes what tests or diagnostics the kiosk performs; the PNG is an unlabeled line drawing (from `worldforge/out/training/diagnostic-x.json#gaps`)
- Training: spec gap: The PDF is branded RomanBridge; no source links Diagnostic.X to AGI Corp (umbrella set per instruction) (from `worldforge/out/training/diagnostic-x.json#gaps`)
- Training: spec gap: Agents are unnamed in sources; AI avatars are described only as projects in progress (from `worldforge/out/training/diagnostic-x.json#gaps`)
- Training: spec gap: Video contents (4 .webm files) were not viewed; only filenames used (from `worldforge/out/training/diagnostic-x.json#gaps`)
- Training: spec gap: No source ties the anchor location (lat 5.34, lon 101.57) to any site or facility (from `worldforge/out/training/diagnostic-x.json#gaps`)
- Gate 1.2n native fastgltf load: open: Sneeze not checked out here.
- Gate 1.3 SOM mount plan: prepared-not-mounted.
- Gate 1.4 rendered frame: open.

_Source: `worldforge/out/diagnostic-x/cards.json#gaps`, `worldforge/out/diagnostic-x/manifest.json#gates`, `worldforge/out/voices/manifest.json`, `agents/hive/index.json`, `worldforge/out/training/diagnostic-x.json`_
