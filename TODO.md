# TODO

## Stage 1 — Data exploration (ACTIVE)
- [x] Create SPEC.md, SCHEMA.md, folder structure
- [ ] Run scripts/explore_data.py against all free StatsBomb competitions
- [ ] Confirm real shootout counts per competition
- [ ] Confirm keeper dive field coverage
- [ ] Confirm taker sample sizes

## Stage 2 — Aggregations (PENDING)
- [ ] Per-taker placement tendencies with Wilson CIs
- [ ] Population pressure stats (kick order, score state, sudden death)

## Stage 3 — FastAPI + MCP (PENDING)
- [ ] List shootouts endpoint
- [ ] Get kick endpoint
- [ ] Taker history with confidence endpoint
- [ ] Keeper record endpoint
- [ ] Pressure stats endpoint
- [ ] Context Forge MCP tool definitions

## Stage 4 — Granite explanation service (PENDING)
- [ ] Prompt template (no directional recommendations)
- [ ] Language toggle support
- [ ] Integration with watsonx.ai

## Stage 5 — Frontend Keeper POV (PENDING)
- [ ] Shootout picker
- [ ] Taker prior display with visible confidence band
- [ ] Dive choice UI
- [ ] Reveal + Granite explanation

## Stage 6 — Frontend Taker POV (PENDING)
- [ ] Pressure context display (kick order, score state, sudden death)
- [ ] Placement choice UI
- [ ] Reveal + Granite explanation
