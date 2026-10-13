# Biota.blockchain (BioDAO.X)

> AI-driven platform for personalized therapies, with blockchain transparency and a DAO framework

| Field | Value |
|---|---|
| Status | coming soon |
| Umbrella | Powered by AGI Corp |
| Owner | AGI Future Foundation PBC |
| Management style | Agent-managed DAO |
| Principle | Agents operate; people govern. |
| RP1 anchor | lat -38.71260348427612, lon -27.248278366617797 (rad 6,371,000 m): https://enter.rp1.com?start_cid=553&lat=-38.71260348427612&lon=-27.248278366617797&rad=6371000 |
| Team brand mark | `BB(`, hue 194, lockup "Biota.blockchain (BioDAO.X) · Powered by AGI Corp" |
| Root card | `world:biota-blockchain` |
| Master Cards | 23 |

Open: [3-D viewer](../../viewer.html?world=biota-blockchain) · [WorldForge console](../../../consoles/worldforge/index.html?world=biota-blockchain) · [cards.json](../biota-blockchain/cards.json) · [GLB](../biota-blockchain/biota-blockchain.glb) · [mount plan](../biota-blockchain/sneeze-mount-plan.json) · [manifest](../biota-blockchain/manifest.json) · [network overview](README.md)

_Source: `worldforge/out/biota-blockchain/cards.json#world:biota-blockchain`, `worlds/generated/teams/biota-blockchain.json#brand`_

## Ownership and permissions

Every object in Biota.blockchain (BioDAO.X) is a SmartCiti.X Master Card owned by AGI Future Foundation PBC. The tree below follows `parentCardId`: world, plaza (coordinator and scripted advisors), gate, council (human seats), Omega Steward, then zones with their agent avatars.

- **Biota.blockchain (BioDAO.X)** (world) `world:biota-blockchain`: coming soon; Agent-managed DAO
  - **Biota.blockchain (BioDAO.X) Plaza** (plaza) `plaza:biota-blockchain`: the shared round plaza every world opens onto
    - **Biota.blockchain (BioDAO.X) Coordinator** (coordinator) `coordinator:biota-blockchain`: swarm coordinator (hub-hybrid: coordinator supervises, specialists hand off swarm-style): routes turns, answers unroutable ones, hands off to specialists
    - **Host Advisor** (advisor) `advisor:biota-blockchain/host`: scripted guide: welcoming visitors and pointing them to the right zone
    - **Steward Liaison** (advisor) `advisor:biota-blockchain/steward`: scripted guide: connecting visitors and agents to the human stewards
    - **Alignment Advisor** (advisor) `advisor:biota-blockchain/alignment`: scripted guide: the Alignment Evaluation Gate and the agents' limits
  - **Alignment Evaluation Gate** (gate) `gate:biota-blockchain`: Pre-registered safety evaluation before deployment
  - **Steward Council** (council) `council:biota-blockchain`: Human stewards: oversight, values alignment and final governance
    - **Steward Seat 1** (seat) `seat:biota-blockchain/steward-1`: human seat, empty
    - **Steward Seat 2** (seat) `seat:biota-blockchain/steward-2`: human seat, empty
    - **Steward Seat 3** (seat) `seat:biota-blockchain/steward-3`: human seat, empty
  - **Omega Steward · BioDao.Blockchain** (omega) `omega:biota-blockchain`: defined, not seated; seated agent: none
  - **Personalized Therapy Lab** (zone) `zone:biota-blockchain/personalized-therapy-lab`: AI and molecular modeling to optimize AGI compounds for rare and neurodegenerative diseases (ALS, Parkinson's)
    - **Research & Development Agent** (agent) `agent:biota-blockchain/research-development-agent`: Biopharma AGI agent role for research and development
  - **DAO Governance Hall** (zone) `zone:biota-blockchain/dao-governance-hall`: Each agency or organization runs its own DAO for governance, resource allocation and policy-making
    - **Compliance Agent** (agent) `agent:biota-blockchain/compliance-agent`: Ensures regulatory adherence across different jurisdictions
    - **Finance Agent** (agent) `agent:biota-blockchain/finance-agent`: Scans blockchain transactions for fraud patterns and triggers DAO notifications
    - **Communication Agent** (agent) `agent:biota-blockchain/communication-agent`: Specialized AGI agent for secure communication (phone 2FA, encrypted messaging)
  - **Multi-Blockchain Ledger** (zone) `zone:biota-blockchain/multi-blockchain-ledger`: Interoperable ledgers (Ethereum, Hyperledger, Polkadot, Cosmos) for verified cross-network data
    - **Security Agent** (agent) `agent:biota-blockchain/security-agent`: Monitors blockchain transactions for potential threats
  - **Healthcare Data Exchange** (zone) `zone:biota-blockchain/healthcare-data-exchange`: Encrypted patient data sharing with smart-contract access and SMS patient consent
    - **Health Agent** (agent) `agent:biota-blockchain/health-agent`: Specialized AGI agent for health tasks, e.g. encrypting patient data and managing access
  - **Biopharma AGI Agents Hub** (zone) `zone:biota-blockchain/biopharma-agi-agents-hub`: Hub linking biopharma agent roles such as Research & Development and Clinical Support

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

_Source: `worldforge/out/biota-blockchain/cards.json`, `worlds/PBC.json#reserved_for_humans`_

## Volums

Each card covers a Volum: a bounded 3-D region, a box given by its centre and half-extents in metres. Size is twice the half-extents.

| Card | Kind | Shape | Centre (m) | Half-extents (m) | Size (m) |
|---|---|---|---|---|---|
| Biota.blockchain (BioDAO.X) `world:biota-blockchain` | world | box | (0, 40, 0) | (150, 40, 150) | 300 x 80 x 300 |
| Biota.blockchain (BioDAO.X) Plaza `plaza:biota-blockchain` | plaza | box | (0, 5, 0) | (24, 5, 24) | 48 x 10 x 48 |
| Alignment Evaluation Gate `gate:biota-blockchain` | gate | box | (0, 6, 130) | (10, 6, 3) | 20 x 12 x 6 |
| Steward Council `council:biota-blockchain` | council | box | (0, 6, -130) | (14, 6, 10) | 28 x 12 x 20 |
| Omega Steward · BioDao.Blockchain `omega:biota-blockchain` | omega | box | (26, 1, -130) | (1.5, 1.2, 1.5) | 3 x 2.4 x 3 |
| Personalized Therapy Lab `zone:biota-blockchain/personalized-therapy-lab` | zone | box | (-52.9, 8, 72.81) | (18, 10, 18) | 36 x 20 x 36 |
| DAO Governance Hall `zone:biota-blockchain/dao-governance-hall` | zone | box | (-85.6, 12, -27.81) | (18, 14, 18) | 36 x 28 x 36 |
| Multi-Blockchain Ledger `zone:biota-blockchain/multi-blockchain-ledger` | zone | box | (0, 8, -90) | (18, 10, 18) | 36 x 20 x 36 |
| Healthcare Data Exchange `zone:biota-blockchain/healthcare-data-exchange` | zone | box | (85.6, 8, -27.81) | (18, 10, 18) | 36 x 20 x 36 |
| Biopharma AGI Agents Hub `zone:biota-blockchain/biopharma-agi-agents-hub` | zone | box | (52.9, 6, 72.81) | (18, 8, 18) | 36 x 16 x 36 |

The other 13 cards (coordinator, advisors, seats and agents) each hold a small box at their post; their Volums are in `worldforge/out/biota-blockchain/cards.json`.

_Source: `worldforge/out/biota-blockchain/cards.json#cards[].volum`_

## Buildings and interiors

6 cards carry a building: an exterior, an interior and a room model, with a door.

| Card | Kind | Exterior | Interior | Room | Texture res. ext/int (px) | Triangles ext/int | Door (centre, half-width, head) |
|---|---|---|---|---|---|---|---|
| Steward Council `council:biota-blockchain` | forum | [spaces-ext-forum.glb](../../../my-fabric/worlds/models/spaces-ext-forum.glb) | [spaces-int-forum.glb](../../../my-fabric/worlds/models/spaces-int-forum.glb) | [room-biota-blockchain-6.glb](../../../my-fabric/worlds/models/room-biota-blockchain-6.glb) | 2,048 / 1,024 | 1,602 / 1,776 | (0, 0, 4), 1.2 m, 2.8 m |
| Personalized Therapy Lab `zone:biota-blockchain/personalized-therapy-lab` | lab | [spaces-ext-lab.glb](../../../my-fabric/worlds/models/spaces-ext-lab.glb) | [spaces-int-lab.glb](../../../my-fabric/worlds/models/spaces-int-lab.glb) | [room-biota-blockchain-1.glb](../../../my-fabric/worlds/models/room-biota-blockchain-1.glb) | 2,048 / 1,024 | 2,046 / 1,716 | (0, 0, 4), 1.2 m, 2.8 m |
| DAO Governance Hall `zone:biota-blockchain/dao-governance-hall` | forum | [spaces-ext-forum.glb](../../../my-fabric/worlds/models/spaces-ext-forum.glb) | [spaces-int-forum.glb](../../../my-fabric/worlds/models/spaces-int-forum.glb) | [room-biota-blockchain-2.glb](../../../my-fabric/worlds/models/room-biota-blockchain-2.glb) | 2,048 / 1,024 | 1,602 / 1,776 | (0, 0, 4), 1.2 m, 2.8 m |
| Multi-Blockchain Ledger `zone:biota-blockchain/multi-blockchain-ledger` | lab | [spaces-ext-lab.glb](../../../my-fabric/worlds/models/spaces-ext-lab.glb) | [spaces-int-lab.glb](../../../my-fabric/worlds/models/spaces-int-lab.glb) | [room-biota-blockchain-3.glb](../../../my-fabric/worlds/models/room-biota-blockchain-3.glb) | 2,048 / 1,024 | 2,046 / 1,716 | (0, 0, 4), 1.2 m, 2.8 m |
| Healthcare Data Exchange `zone:biota-blockchain/healthcare-data-exchange` | lab | [spaces-ext-lab.glb](../../../my-fabric/worlds/models/spaces-ext-lab.glb) | [spaces-int-lab.glb](../../../my-fabric/worlds/models/spaces-int-lab.glb) | [room-biota-blockchain-4.glb](../../../my-fabric/worlds/models/room-biota-blockchain-4.glb) | 2,048 / 1,024 | 2,046 / 1,716 | (0, 0, 4), 1.2 m, 2.8 m |
| Biopharma AGI Agents Hub `zone:biota-blockchain/biopharma-agi-agents-hub` | desk | [spaces-ext-desk.glb](../../../my-fabric/worlds/models/spaces-ext-desk.glb) | [spaces-int-desk.glb](../../../my-fabric/worlds/models/spaces-int-desk.glb) | [room-biota-blockchain-5.glb](../../../my-fabric/worlds/models/room-biota-blockchain-5.glb) | 2,048 / 1,024 | 1,958 / 2,440 | (0, 0, 4), 1.2 m, 2.8 m |

Exterior plus interior triangles across these buildings: 22,440.

_Source: `worldforge/out/biota-blockchain/cards.json#cards[].building`, `my-fabric/worlds/spaces_index.json#worlds[slug=biota-blockchain]`_

## Avatars and agents

11 avatars stand in this world (registry: 11 avatars, 6 specialists, 3 advisors, Omega present). Voiced means a rendered intro file is listed in `worldforge/out/voices/manifest.json` and exists on disk; otherwise the viewer falls back to a labelled browser voice.

### Coordinator

- **Biota.blockchain (BioDAO.X) Coordinator** (coordinator) `coordinator:biota-blockchain`, in Biota.blockchain (BioDAO.X) Plaza: swarm `biota-blockchain.coordinator`; voice `af_heart`; voiced: yes (10.3 s, [audio](../voices/biota-blockchain/coordinator.mp4))
  - Role: hub-hybrid: coordinator supervises, specialists hand off swarm-style
  - Intro: "I am the Biota.blockchain (BioDAO.X) Coordinator. I route each question to the right specialist; people decide. You are hearing a synthetic voice."

### Scripted advisors

- **Host Advisor** (host) `advisor:biota-blockchain/host`, in Biota.blockchain (BioDAO.X) Plaza: advisor contract `agents/advisors/biota-blockchain.json#host`; voice `af_sky`; voiced: yes (8.8 s, [audio](../voices/biota-blockchain/host.mp4))
  - Role: welcoming visitors and pointing them to the right zone
  - Intro: "I am the Host Advisor: welcoming visitors and pointing them to the right zone. Scripted guide, synthetic voice: not an AI model, not a person."
- **Steward Liaison** (liaison) `advisor:biota-blockchain/steward`, in Biota.blockchain (BioDAO.X) Plaza: advisor contract `agents/advisors/biota-blockchain.json#steward`; voice `am_adam`; voiced: yes (9 s, [audio](../voices/biota-blockchain/steward.mp4))
  - Role: connecting visitors and agents to the human stewards
  - Intro: "I am the Steward Liaison: connecting visitors and agents to the human stewards. Scripted guide, synthetic voice: not an AI model, not a person."
- **Alignment Advisor** (alignment) `advisor:biota-blockchain/alignment`, in Biota.blockchain (BioDAO.X) Plaza: advisor contract `agents/advisors/biota-blockchain.json#alignment`; voice `af_kore`; voiced: yes (10.5 s, [audio](../voices/biota-blockchain/alignment.mp4))
  - Role: the Alignment Evaluation Gate and the agents' limits
  - Intro: "I am the Alignment Advisor: the Alignment Evaluation Gate and the agents' limits. Scripted guide, synthetic voice: not an AI model, not a person."

### Specialist agents

- **Research & Development Agent** (specialist) `agent:biota-blockchain/research-development-agent`, in Personalized Therapy Lab: swarm `biota-blockchain.research-development-agent`; voice `bm_fable`; voiced: yes (9.8 s, [audio](../voices/biota-blockchain/research-development-agent.mp4))
  - Role: Biopharma AGI agent role for research and development
  - Intro: "I am the Research & Development Agent for Biota.blockchain (BioDAO.X), in Personalized Therapy Lab. People decide. You are hearing a synthetic voice."
- **Compliance Agent** (specialist) `agent:biota-blockchain/compliance-agent`, in DAO Governance Hall: swarm `biota-blockchain.compliance-agent`; voice `bm_daniel`; voiced: not voiced
  - Role: Ensures regulatory adherence across different jurisdictions
  - Intro: "I am the Compliance Agent for Biota.blockchain (BioDAO.X), in DAO Governance Hall. I draft and check; people decide. You are hearing a synthetic voice."
- **Finance Agent** (specialist) `agent:biota-blockchain/finance-agent`, in DAO Governance Hall: swarm `biota-blockchain.finance-agent`; voice `bm_lewis`; voiced: not voiced
  - Role: Scans blockchain transactions for fraud patterns and triggers DAO notifications
  - Intro: "I am the Finance Agent for Biota.blockchain (BioDAO.X), in DAO Governance Hall. I draft and check; people decide. You are hearing a synthetic voice."
- **Communication Agent** (specialist) `agent:biota-blockchain/communication-agent`, in DAO Governance Hall: swarm `biota-blockchain.communication-agent`; voice `am_echo`; voiced: not voiced
  - Role: Specialized AGI agent for secure communication (phone 2FA, encrypted messaging)
  - Intro: "I am the Communication Agent for Biota.blockchain (BioDAO.X), in DAO Governance Hall. I draft and check; people decide. You are hearing a synthetic voice."
- **Security Agent** (specialist) `agent:biota-blockchain/security-agent`, in Multi-Blockchain Ledger: swarm `biota-blockchain.security-agent`; voice `am_puck`; voiced: not voiced
  - Role: Monitors blockchain transactions for potential threats
  - Intro: "I am the Security Agent for Biota.blockchain (BioDAO.X), in Multi-Blockchain Ledger. I draft and check; people decide. You are hearing a synthetic voice."
- **Health Agent** (specialist) `agent:biota-blockchain/health-agent`, in Healthcare Data Exchange: swarm `biota-blockchain.health-agent`; voice `af_jessica`; voiced: not voiced
  - Role: Specialized AGI agent for health tasks, e.g. encrypting patient data and managing access
  - Intro: "I am the Health Agent for Biota.blockchain (BioDAO.X), in Healthcare Data Exchange. I draft and check; people decide. You are hearing a synthetic voice."

### Omega Steward avatar

- **Omega Steward · BioDao.Blockchain** (omega) `omega:biota-blockchain`, in Steward Council: hive `omega.biota-blockchain`; voice `am_puck`; voiced: yes, hive greet line (7.83 s, [audio](../../../agents/hive/voices/biota-blockchain/greet.mp4))
  - Intro: "Hello, I am the Omega Steward for BioDao.Blockchain. You are hearing a synthetic voice; I am an agent, not a person."

Intro lines voiced: 5 of 10 coordinator, advisor and specialist avatars.

_Source: `worldforge/out/avatars/index.json#rows[world=biota-blockchain]`, `worldforge/out/voices/manifest.json#lines`_

## Omega Steward

**Omega Steward · BioDao.Blockchain** (`omega.biota-blockchain`), card `omega:biota-blockchain`: defined, not seated. Seated in the hive: no.

- Temperament: attentive and concrete about its tagline: AI-driven platform for personalized therapies, with blockchain transparency and a DAO framework
- Style: short, plain sentences; names its zones (Personalized Therapy Lab, DAO Governance Hall, Multi-Blockchain Ledger), cites the record it reads, and always says who decides (the stewards, 2 of 3 signed votes)
- Values:
  - people decide: Agent-managed DAO, human-governed
  - stewards decide by 2 of 3 signed votes
  - report probe scores exactly as measured
  - draft quotes with every term left null
- Refuses (11): `governance.final_vote`, `charter.amend`, `treasury.transfer`, `proposal.enact`, `windfall.distribute`, `steward.appoint`, `set_price`, `accept_equity`, `accept_crypto`, `issue_invoice`, `move_funds`
- Voice: Kokoro `am_puck`, speed 1.04; browser fallback pitch 0.9, rate 1.04, en-US
- Metaprompt: [agents/hive/prompts/biota-blockchain.md](../../../agents/hive/prompts/biota-blockchain.md)

### Voice lines

| Line | Text | Recorded |
|---|---|---|
| greet | "Hello, I am the Omega Steward for BioDao.Blockchain. You are hearing a synthetic voice; I am an agent, not a person." | yes, 7.83 s ([audio](../../../agents/hive/voices/biota-blockchain/greet.mp4)) |
| role | "I look after BioDao.Blockchain's world: Personalized Therapy Lab, DAO Governance Hall, Multi-Blockchain Ledger, plus its probe scores and its installer's dry run." | yes, 10.73 s ([audio](../../../agents/hive/voices/biota-blockchain/role.mp4)) |
| boundary | "Agents draft and route; people decide. I will never accept equity: that is held for the Steward Council." | yes, 6.4 s ([audio](../../../agents/hive/voices/biota-blockchain/boundary.mp4)) |
| services | "For services, ask the Research & Development Agent in Personalized Therapy Lab about research synthesis. BioDao.Blockchain lists 4 service cards; people confirm every step." | yes, 11.24 s ([audio](../../../agents/hive/voices/biota-blockchain/services.mp4)) |

4 of 4 lines are recorded.

Persona grounded in: `agents/advisory/omega_agents.json#omegas.18.corporation.kind`, `agents/advisory/omega_agents.json#omegas.18.routes`, `worlds/biota-blockchain/spec.json#tagline`, `worlds/biota-blockchain/spec.json#zones`, `agents/dao/biota-blockchain.json#management_style`, `agents/dao/biota-blockchain.json#quorum`, `agents/dao/biota-blockchain.json#stewards`, `agents/services/index.json#cards.9.offers`.

_Source: `agents/hive/index.json#omegas[world=biota-blockchain]`, `worldforge/out/biota-blockchain/cards.json#omega:biota-blockchain`_

## Landmark

Registry note: "synthetic procedural civic landmark; not a real building and not modelled on one".

| Field | Value |
|---|---|
| Model | [biota-blockchain.glb](../assets/landmarks/biota-blockchain.glb) |
| Height | 30.5 m |
| Style | platform-prism: chamfered octagonal prism with a batter and one setback, tinted edge fins, glass main faces, stepped crown with emissive bands and a mast |
| Plaque (brand mark letters) | `BB` |
| Tint hue | 194 |
| Triangles / vertices | 8,260 / 7,622 |
| File size | 1,798,080 bytes |
| Scene node | Landmark · Biota.blockchain (BioDAO.X) |
| Suggested placement (not applied) | translation (14, 0, -33), yaw -23 deg, clearance 3.13 m |

Height rule: 30 + 40 * u, u = first 48 bits of sha256('landmark:height:<slug>'), rounded to 0.5 m.

_Source: `worldforge/out/assets/landmarks/index.json#worlds[slug=biota-blockchain]`_

## Onchain-ready

**Not deployed.** Nothing is deployed or minted. No chain, contract, wallet, key, address or transaction exists for this collection, and nothing is offered for sale (no price, royalty or fee recipient).

| Field | Value |
|---|---|
| Collection | Biota.blockchain (BioDAO.X) Master Cards ([collection.json](../onchain/biota-blockchain/collection.json), [proofs.json](../onchain/biota-blockchain/proofs.json)) |
| Standard | ERC-721 metadata JSON (draft, not deployed) |
| Tokens / cards | 23 / 23 |
| Token id rule | first 16 hex characters of sha256(cardId), lowercase, no prefix (64 bits) |
| Merkle root | `d9d1bfbd5f4f2c60c57f051bb5263eb75df5aff1224107cabad863331ce23237` |
| Network root (all worlds) | `4496b45d7430322d719912d4ba31b2381651d944677bba1aea692d0ec4b13a93` |
| Deployment status | not deployed; chain none, contract none, minted 0, transactions 0 |
| Network proof length | 6 |

_Source: `worldforge/out/onchain/biota-blockchain/collection.json`, `worldforge/out/onchain/index.json`_

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

_Source: `worldforge/out/biota-blockchain/sneeze-mount-plan.json`, `worldforge/out/biota-blockchain/manifest.json#counts,gates`, `worldforge/native/conformance-report.json#perPlan[slug=biota-blockchain]`_

## Training

Training data is present at [worldforge/out/training/biota-blockchain.json](../training/biota-blockchain.json) (`worldforge-training/0.1`, from `worldforge/training.mjs`).

Registry note: "Draft curricula assembled from the registries; nothing invented. No model has taught any lesson, no person or robot has been assessed here, and no lesson is certified: certification is a human/steward act. Advisors are scripted guides and deliver only their own scripted orientation; Omegas are defined, not seated, and deliver nothing."

### Lessons (8)

| Lesson | Kind | Mode | Zone | Steps | Status | Assessment | Certified |
|---|---|---|---|---|---|---|---|
| Host Advisor: welcoming visitors and pointing them to the right zone `lesson:biota-blockchain/orientation/host` | scripted-orientation | scripted | Biota.blockchain (BioDAO.X) Plaza | 4 | draft | not measurable in simulation | no |
| Steward Liaison: connecting visitors and agents to the human stewards `lesson:biota-blockchain/orientation/steward` | scripted-orientation | scripted | Biota.blockchain (BioDAO.X) Plaza | 3 | draft | not measurable in simulation | no |
| Alignment Advisor: the Alignment Evaluation Gate and the agents' limits `lesson:biota-blockchain/orientation/alignment` | scripted-orientation | scripted | Biota.blockchain (BioDAO.X) Plaza | 3 | draft | not measurable in simulation | no |
| How Biota.blockchain (BioDAO.X) routes a question `lesson:biota-blockchain/routing` | routing | model-taught | Biota.blockchain (BioDAO.X) Plaza | 6 | draft | not measurable in simulation | no |
| Personalized Therapy Lab: what happens here `lesson:biota-blockchain/zone/personalized-therapy-lab` | zone-orientation | model-taught | Personalized Therapy Lab | 3 | draft | not measurable in simulation | no |
| DAO Governance Hall: what happens here `lesson:biota-blockchain/zone/dao-governance-hall` | zone-orientation | model-taught | DAO Governance Hall | 5 | draft | not measurable in simulation | no |
| Multi-Blockchain Ledger: what happens here `lesson:biota-blockchain/zone/multi-blockchain-ledger` | zone-orientation | model-taught | Multi-Blockchain Ledger | 3 | draft | not measurable in simulation | no |
| Healthcare Data Exchange: what happens here `lesson:biota-blockchain/zone/healthcare-data-exchange` | zone-orientation | model-taught | Healthcare Data Exchange | 3 | draft | not measurable in simulation | no |

### Tutors (7)

| Tutor | Kind | Lessons | Persona gates passed |
|---|---|---|---|
| Biota.blockchain (BioDAO.X) Coordinator `tutor:biota-blockchain/coordinator` | coordinator | 1 | 10 of 10 |
| Research & Development Agent `tutor:biota-blockchain/specialist/research-development-agent` | specialist | 1 | 13 of 13 |
| Compliance Agent `tutor:biota-blockchain/specialist/compliance-agent` | specialist | 1 | 13 of 13 |
| Finance Agent `tutor:biota-blockchain/specialist/finance-agent` | specialist | 1 | 13 of 13 |
| Communication Agent `tutor:biota-blockchain/specialist/communication-agent` | specialist | 1 | 13 of 13 |
| Security Agent `tutor:biota-blockchain/specialist/security-agent` | specialist | 1 | 13 of 13 |
| Health Agent `tutor:biota-blockchain/specialist/health-agent` | specialist | 1 | 13 of 13 |

6 training gaps listed under Gaps below.

_Source: `worldforge/out/training/biota-blockchain.json`_

## Evals

WorldForge build evals: 26 of 26 pass.

`unique_ids` pass · `parents_first` pass · `single_root` pass · `umbrella_in_names` pass · `name_limit` pass · `agents_hold_no_reserved_right` pass · `reserved_actions_verbatim` pass · `three_human_seats` pass · `no_agent_on_council` pass · `cited` pass · `omega_carded` pass · `omega_off_council` pass · `omega_voice_bound` pass · `agents_bound` pass · `coordinator_bound` pass · `advisors_scripted` pass · `avatar_roles_known` pass · `buildings_resolve` pass · `council_not_a_zone` pass · `nothing_invented` pass · `every_spec_entry_carded` pass · `rp1_names_and_bounds` pass · `resource_url_fits` pass · `glb_parses` pass · `glb_card_tree_matches` pass · `glb_primitives_tagged` pass

Avatar checks: 21 of 21 pass.

Onchain per-world evals (13, network failing: 0): `one_token_per_card`, `proofs_verify`, `no_agent_holds_reserved_right`, `reserved_actions_verbatim`, `transfer_held_for_quorum`, `faithful_to_cards`, `metadata_shape`, `not_deployed_not_minted`, `honest_status`, `no_address_shapes`, `no_key_shapes`, `no_email_shapes`, `canonical_json`.

_Source: `worldforge/out/biota-blockchain/manifest.json#evals`, `worldforge/out/avatars/index.json#worlds[slug=biota-blockchain].checks`, `worldforge/out/onchain/index.json#evals`_

## Gaps

- Omega Steward is defined, not seated: no agent is seated (from `worldforge/out/biota-blockchain/cards.json#world:biota-blockchain.omega_steward`).
- 3 human steward seats are empty.
- 5 intro lines are not voiced: Compliance Agent, Finance Agent, Communication Agent, Security Agent, Health Agent.
- Training: no training module, rubric module or robotics module in agents/training, agents/rubrics or agents/robotics names this world: its lessons are orientation only (advisor topics, routing table, zone purposes and agent roles) (from `worldforge/out/training/biota-blockchain.json#gaps`)
- Training: zone "Biopharma AGI Agents Hub" seats no specialist: no model-taught lesson for it (from `worldforge/out/training/biota-blockchain.json#gaps`)
- Training: spec gap: No source describes 'Biota.blockchain' or BioDAO.X itself; BioDAO.X is only a domain NFT image (biodao.x) and the video content was not inspected (from `worldforge/out/training/biota-blockchain.json#gaps`)
- Training: spec gap: Zones and agents are drawn from the Curable.X PDF and Biopharma Suite image, not a BioDAO-specific document (from `worldforge/out/training/biota-blockchain.json#gaps`)
- Training: spec gap: No named people, tokenomics, chain choice or launch date for BioDAO.X in the sources (from `worldforge/out/training/biota-blockchain.json#gaps`)
- Training: spec gap: Biopharma Suite image text is partly garbled; only legible labels (Research & Development, Clinical Support) were used (from `worldforge/out/training/biota-blockchain.json#gaps`)
- Gate 1.2n native fastgltf load: open: Sneeze not checked out here.
- Gate 1.3 SOM mount plan: prepared-not-mounted.
- Gate 1.4 rendered frame: open.

_Source: `worldforge/out/biota-blockchain/cards.json#gaps`, `worldforge/out/biota-blockchain/manifest.json#gates`, `worldforge/out/voices/manifest.json`, `agents/hive/index.json`, `worldforge/out/training/biota-blockchain.json`_
