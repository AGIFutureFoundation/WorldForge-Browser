# SmartCiti.X worlds: network overview

AGI Future Foundation PBC · Powered by AGI Corp. 41 agentic virtual worlds, each described card by card in its own overview. Every number below is read from a registry at build time by `worldforge/overview.mjs`; the source path sits next to it.

Open the [3-D viewer](../../viewer.html) or the [WorldForge console](../../../consoles/worldforge/index.html).

## Totals

| Measure | Value | Source |
|---|---|---|
| Worlds | 41 | worldforge/out/index.json#totals.worlds |
| Master Cards | 939 | worldforge/out/index.json#totals.cards |
| Zone cards | 205 | worldforge/out/<slug>/cards.json |
| Agent cards | 242 | worldforge/out/<slug>/cards.json |
| Cards with a building | 246 | worldforge/out/<slug>/cards.json#cards[].building |
| Blockout primitives | 1,103 | worldforge/out/index.json#totals.primitives |
| WorldForge build evals (failed) | 1,066 (0) | worldforge/out/index.json#totals |
| Worlds with an RP1 anchor | 4 | worldforge/out/index.json#totals.anchored |
| Avatars | 447: 242 specialists, 41 coordinators, 123 advisors, 41 Omegas | worldforge/out/avatars/index.json#totals |
| Voiced intro lines | 159 (1510.6 s) | worldforge/out/voices/manifest.json#totals |
| Omega voice lines for these worlds (recorded) | 164 (161) | agents/hive/index.json#omegas[].lines |
| Landmarks (triangles) | 41 (508,339) | worldforge/out/assets/landmarks/index.json#totals |
| Landmark height range | 30.5 to 69 m | worldforge/out/assets/landmarks/index.json#totals |
| Onchain-ready tokens (deployed) | 939 (not deployed, not minted) | worldforge/out/onchain/index.json#totals,status |
| Onchain network root | `4496b45d7430322d719912d4ba31b2381651d944677bba1aea692d0ec4b13a93` | worldforge/out/onchain/index.json#network_root |
| Mount plans / nodes | 41 / 2,042 | worldforge/native/conformance-report.json#totals |
| Native conformance violations | 0 | worldforge/native/conformance-report.json#totals.native |

## The SmartCiti.X Master Card model

**Master Cards.** Every object in a world is one card (`smartcitix-master-cards/0.1`), owned by AGI Future Foundation PBC and carrying the umbrella "Powered by AGI Corp". Cards form one tree per world through `parentCardId`: world, then plaza (a coordinator and scripted advisors), the Alignment Evaluation Gate, the Steward Council with its human seats, the Omega Steward, and zones holding agent avatars. Across the network the kinds are: advisor 123, agent 242, coordinator 41, council 41, gate 41, omega 41, plaza 41, seat 123, world 41, zone 205.

**Volum.** Each card covers a bounded 3-D region, stored as a box centre and half-extents in metres (shapes used: box).

**Permissions.** Each card has a matrix over 7 rights: `view`, `enter`, `build`, `operate`, `delegate`, `transfer`, `govern`. Holders are `agents:zone`, `public`, `steward-quorum`, `stewards`. 6 actions are reserved for people and held for the Steward Council by a 2-of-3 quorum of 3 seats: `governance.final_vote`, `charter.amend`, `treasury.transfer`, `proposal.enact`, `windfall.distribute`, `steward.appoint`.

**Agents operate; people govern.** That is the principle written on every cards file. Agents, coordinators, advisors and the Omega Steward list the reserved actions in `may_never`; council seats are human seats (all 123 empty today); every Omega Steward is defined, not seated.

_Source: `worldforge/out/<slug>/cards.json`, `worlds/PBC.json`, `worldforge/out/onchain/index.json#totals.by_kind`_

## Worlds

Kind is the landmark style, which `worldforge/out/assets/landmarks/index.json` assigns by a rule on each world's registry entry (see the key below). Voiced lines count rendered intro lines plus recorded Omega lines.

| World | Kind | Zone cards | Agents | Buildings | Landmark height | Voiced lines | Anchor |
|---|---|---|---|---|---|---|---|
| [Agentic Payments](agentic-payments.md) | track-twist | 4 | 5 | 5 | 66.5 m | 9 | no anchor yet |
| [Agents That Deploy Infrastructure](agents-deploy-infrastructure.md) | track-twist | 6 | 6 | 7 | 52 m | 9 | no anchor yet |
| [Autonomous Organizations](autonomous-organizations.md) | track-twist | 5 | 6 | 6 | 54 m | 9 | no anchor yet |
| [Biota.blockchain (BioDAO.X)](biota-blockchain.md) | platform-prism | 5 | 6 | 6 | 30.5 m | 9 | lat -38.713, lon -27.248 |
| [Cancer DAO](cancer-dao.md) | focus-rotunda | 5 | 6 | 6 | 51 m | 9 | no anchor yet |
| [Climate DAO](climate-dao.md) | focus-rotunda | 5 | 6 | 6 | 60 m | 9 | no anchor yet |
| [Diagnostic.X](diagnostic-x.md) | platform-prism | 4 | 4 | 5 | 39.5 m | 9 | lat 5.343, lon 101.566 |
| [Ecology DAO](ecology-dao.md) | focus-rotunda | 5 | 6 | 6 | 65.5 m | 9 | no anchor yet |
| [Education DAO](education-dao.md) | focus-rotunda | 5 | 6 | 6 | 52 m | 9 | no anchor yet |
| [Empathic.X](empathic-x.md) | platform-prism | 5 | 5 | 6 | 63.5 m | 9 | lat 47.440, lon -179.350 |
| [Locator.X](locator-x.md) | platform-prism | 6 | 6 | 7 | 48 m | 9 | lat 21.097, lon 142.693 |
| [Public Health DAO](public-health-dao.md) | focus-rotunda | 5 | 6 | 6 | 63 m | 9 | no anchor yet |
| [Robotics DAO](robotics-dao.md) | focus-rotunda | 5 | 6 | 6 | 58 m | 9 | no anchor yet |
| [Curable.X (Series 4)](s04-curable-x.md) | series-setback | 5 | 6 | 6 | 37 m | 9 | no anchor yet |
| [BioPharma.Go (Series 5)](s05-biopharma-go.md) | series-setback | 5 | 6 | 6 | 40.5 m | 9 | no anchor yet |
| [Blockchain (Series 6)](s06-blockchain.md) | series-setback | 5 | 6 | 6 | 43 m | 8 | no anchor yet |
| [Divine.DAO (Series 7)](s07-divine-dao.md) | series-setback | 5 | 6 | 6 | 65 m | 9 | no anchor yet |
| [Astrological.X (Series 9)](s09-astrological-x.md) | series-setback | 5 | 6 | 6 | 55.5 m | 9 | no anchor yet |
| [Molecular (Series 11)](s11-molecular.md) | series-setback | 5 | 6 | 6 | 54 m | 9 | no anchor yet |
| [Parking Smart.X (Series 12)](s12-parking-smart-x.md) | series-setback | 5 | 6 | 6 | 31.5 m | 9 | no anchor yet |
| [Gonstead.X (Series 13)](s13-gonstead-x.md) | series-setback | 5 | 6 | 6 | 51 m | 9 | no anchor yet |
| [AskDoc.X (Series 14)](s14-askdoc-x.md) | series-setback | 5 | 6 | 6 | 57 m | 9 | no anchor yet |
| [RomanBridge DAO (Series 15)](s15-romanbridge-dao.md) | series-setback | 5 | 6 | 6 | 54 m | 9 | no anchor yet |
| [EchoDawn DAO (Series 16)](s16-echodawn-dao.md) | series-setback | 5 | 6 | 6 | 35.5 m | 9 | no anchor yet |
| [Curable.Blockchain DAO (Series 17)](s17-curable-blockchain-dao.md) | series-setback | 5 | 6 | 6 | 48 m | 9 | no anchor yet |
| [Moscone.X (Series 19)](s19-moscone-x.md) | series-setback | 5 | 6 | 6 | 41 m | 8 | no anchor yet |
| [CMMC (Series 20)](s20-cmmc.md) | series-setback | 5 | 6 | 6 | 35.5 m | 6 | no anchor yet |
| [Incubator DAO (Series 21)](s21-incubator-dao.md) | series-setback | 5 | 6 | 6 | 47.5 m | 6 | no anchor yet |
| [Get.Delivery DAO (Series 22)](s22-get-delivery-dao.md) | series-setback | 5 | 6 | 6 | 37 m | 6 | no anchor yet |
| [Avatar.Chat (Series 23)](s23-avatar-chat.md) | series-setback | 5 | 6 | 6 | 57.5 m | 6 | no anchor yet |
| [Donatello DAO (Series 24)](s24-donatello-dao.md) | series-setback | 5 | 6 | 6 | 59 m | 6 | no anchor yet |
| [MyPet.AI (Series 25)](s25-mypet-ai.md) | series-setback | 5 | 6 | 6 | 48.5 m | 6 | no anchor yet |
| [Lyka DAO (Series 26)](s26-lyka-dao.md) | series-setback | 5 | 6 | 6 | 65.5 m | 6 | no anchor yet |
| [Genomic.DAO (Series 27)](s27-genomic-dao.md) | series-setback | 5 | 6 | 6 | 37 m | 6 | no anchor yet |
| [Genomic.Blockchain (Series 28)](s28-genomic-blockchain.md) | series-setback | 5 | 6 | 6 | 31 m | 6 | no anchor yet |
| [Metaverse DAO (Series 29)](s29-metaverse-dao.md) | series-setback | 5 | 6 | 6 | 53 m | 6 | no anchor yet |
| [Aerospace DAO (Series 31)](s31-aerospace-dao.md) | series-setback | 5 | 6 | 6 | 69 m | 6 | no anchor yet |
| [Solar DAO (Series 32)](s32-solar-dao.md) | series-setback | 5 | 6 | 6 | 59 m | 6 | no anchor yet |
| [InfoGurus (Series 33)](s33-infogurus.md) | series-setback | 5 | 6 | 6 | 62.5 m | 4 | no anchor yet |
| [ALS DAO (Series 34)](s34-als-dao.md) | series-setback | 5 | 6 | 6 | 54 m | 6 | no anchor yet |
| [Parkinsons DAO (Series 35)](s35-parkinsons-dao.md) | series-setback | 5 | 6 | 6 | 34 m | 6 | no anchor yet |

Zone cards exclude the Steward Council: every spec lists it as a zone, but it is merged into the council card, so `worldforge/out/index.json` reports one more zone per world than the table.

### Kind key

| Style | Worlds | Rule |
|---|---|---|
| series-setback | 28 | my-fabric/worlds/index.json worlds[].name ends in '(Series N)' |
| track-twist | 3 | worlds[].zones[].source cites worlds/sources/founder-tracks-2026-09-28.md |
| focus-rotunda | 6 | worlds[].name ends in ' DAO' and zones[].source cites the PBC mission statement ('How It Works') |
| platform-prism | 4 | none of the rules above (worlds whose zones cite their own source documents) |

_Source: `worldforge/out/index.json#worlds`, `worldforge/out/assets/landmarks/index.json#styles,worlds`, `worldforge/out/voices/manifest.json`, `agents/hive/index.json`_

## Roadmap and gates

The family roadmap and stack, read by atlas/build_deck.py and atlas/build_film.py. Phases carry no dates: each gate is a named person's decision, and nothing here is promised until that person makes it.

### Family roadmap

#### Built and checked (done)

- 35 walkable 4 km series worlds with districts, landmarks, a Steward Council and a Projects Pavilion
- SmartCiti.X Holodeck: 8 districts of union halls and an 11-simulator yard
- RP1 fabric files for every world; 506 glTF models pass the Khronos validator
- Agent swarms, metaprompts and management teams seated by each company's own agents
- Hash-chained agent ledger with 2-of-3 signed steward votes
- A heartbeat that runs every eval every five minutes and stops itself on a broken build

**Human gate:** none: this is the evidence the later phases build on

#### Shared state on Neon (now)

- Postgres schema and seed for worlds, teams, seats, proposals, projects and the ledger
- Consoles and worlds read one database instead of rebuilt JSON files
- Heartbeat beats written as rows, so a report is a query

**Human gate:** the founder authorizes the Neon connector; the connection string stays in the environment, never in the repository

#### Worlds on RP1's Earth (next)

- An RP1 Dev Center company for the family
- A public HTTPS map service hosting the fabrics
- Land claims at each world's anchor, then attach-to-Earth
- Publication kit ready: 6 worlds pass every check; 38 wait only on a founder-chosen anchor

**Human gate:** the founder, on the RP1 Dev Center account; publishing public content is the founder's call

#### Real stewards, real signatures (next)

- Seat three human stewards on each Steward Council
- Replace the throwaway test keys with the stewards' own Ed25519 public keys
- First signed votes on the open proposals
- Keyring ready: stewards and instructors make their own signing keys and register only the public half

**Human gate:** the board appoints stewards (steward.appoint is reserved for people)

#### Membership goes live (later)

- Apple Wallet and Google Wallet passes signed with the family's own certificates
- Prices for each membership level
- Checkout opened only after the levels and terms are approved

**Human gate:** the board sets every price; the founder supplies the signing certificates; counsel reviews the terms

#### Entities and shared benefit (later)

- AGI Corp and W3 LLC filings, and written agreements between the nonprofit, the management company and each cell
- Open Global Investment terms, kept separate from control
- The Windfall Clause threshold, share and recipients

**Human gate:** the board and counsel

_Source: `atlas/roadmap.json#phases`_

### WorldForge gates

| Gate | Status across worlds |
|---|---|
| 1.1 generated core | done (41) |
| 1.2 GLB parsed + card tree verified (JavaScript) | done (41) |
| 1.2n native fastgltf load | open: Sneeze not checked out here (41) |
| 1.3 SOM mount plan | prepared-not-mounted (41) |
| 1.4 rendered frame | open (41) |

Gates 1.2n and 1.4 need the Sneeze native host and a rendered frame (status strings above). Beside these engineering gates sit the human ones: 37 worlds have no RP1 anchor until a steward writes one (cards.json gaps), all 123 steward seats wait on `steward.appoint`, which is reserved for the Steward Council, and nothing onchain is deployed or minted.

_Source: `worldforge/out/<slug>/manifest.json#gates`, `worldforge/out/index.json#totals.anchored`_
