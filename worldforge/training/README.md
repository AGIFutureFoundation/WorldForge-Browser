# Worldforge training: curricula, lessons and tutor prompts

*Powered by AGI Corp* · AGI Future Foundation PBC · agents operate; people govern.

```
node worldforge/training.mjs           # writes worldforge/out/training/
node worldforge/training.mjs --check   # rebuilds in memory; exit 1 if any output is stale or any eval fails
```

Outputs:

- `worldforge/out/training/index.json`: the delivery rules, a row per world, the gaps, every eval and every broken fixture, and the totals.
- `worldforge/out/training/<world>.json`: one curriculum per worldforge avatar world (the lessons, the tutor prompts with their gate results, the gaps).
- `worldforge/out/training/smartciti-holodeck.json`: draft module lessons for the one training world that has no worldforge avatar world (`seated: false`, `delivered_by: []`).
- `worldforge/out/training/tutors/<world>.md`: the tutor prompts, written out so a person can read them.

## Where lessons come from

Every lesson is built from content that already exists in the registries. Nothing is invented.

| kind | mode | content from | delivered by |
|---|---|---|---|
| `scripted-orientation` | scripted | the advisor's own topics, `agents/advisors/<slug>.json` | that scripted advisor only |
| `routing` | model-taught | the swarm's topology and agents, `agents/swarms/<slug>.json` | the world's coordinator |
| `zone-orientation` | model-taught | the zone purpose (`worlds/<slug>/spec.json`), the roles of the agents seated there, and the zone's building card (`worldforge/out/<slug>/cards.json`) | the specialists seated in that zone |
| `module` | model-taught | the training module with its human and robot tracks (`agents/training/index.json`), the robotics module's skills (`agents/robotics/index.json`), the paired Academy halls' focus lines (`my-fabric/holodeck/data.json`) and the wing bay (`my-fabric/holodeck/wing.json`) | the specialists that `agents/robotics/index.json#avatars.<world>` names for the world |

Assessment uses the axes of `agents/rubrics/index.json`, copied exactly, including the axes marked "not measurable in simulation". A lesson with no rubric module is marked "not measurable in simulation", with the reason "no measure in the source". Every lesson has `status: "draft"` and `certification: null`. Certification is done by a human steward. This script never certifies anything.

## Tutor prompts

Each specialist or coordinator that delivers a model-taught lesson gets one tutor prompt. The prompt binds the avatar's persona prompt (`worldforge/out/avatars/prompts/<world>.json`) by id and sha256, then lists the avatar's lessons. Each prompt is gated by `evalPrompt` from `agents/metaprompt.mjs`, which receives the world spec and, for a specialist, its swarm agent, just as `specialistPrompt` is checked. Every gate must pass.

Two kinds of avatar get no tutor prompt:

- Advisors are scripted guides.
- Omegas are defined, not seated.

## Evals

The build fails if any of these does not hold:

- Every source, objective and step pointer resolves.
- Every deliverer exists in that world and is allowed for the lesson kind.
- No advisor or Omega delivers a model-taught lesson.
- No lesson is certified.
- The rubric axes match `agents/rubrics`.
- Module lessons keep both tracks.
- Every tutor prompt passes every gate and binds its avatar's current persona prompt.
- The outputs contain no PII, no keys and no retired name.
- Two builds produce byte-identical output.

Each broken fixture must fail exactly its own check.

## Known gaps

- 40 of the 41 avatar worlds get orientation lessons only, because no training, rubric or robotics module names them. Robotics DAO is the exception: it has the `deployment-gate` module.
- The 18 holodeck modules belong to `smartciti-holodeck`, which has no worldforge avatar world. They are drafted but not seated.
- The Locator.X Academy's tracks and lessons are cited from a file that is not in this repository, so none of that content is reproduced here.
