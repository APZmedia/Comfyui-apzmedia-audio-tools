# Roadmap: PlayDiffusion ComfyUI Integration

## Phase 1: Dependency Analysis
**Goal:** Understand what PlayDiffusion needs and what conflicts it creates

### Tasks
- [ ] Extract PlayDiffusion's dependency tree (pyproject.toml, setup.py)
- [ ] Map against ComfyUI's dependencies
- [ ] Identify version conflicts
- [ ] Document system requirements (CUDA, etc.)

### Deliverable
- Dependency conflict matrix
- Go/no-go for direct integration

---

## Phase 2: Architecture Research
**Goal:** Evaluate isolation strategies and pick the best approach

### Tasks
- [ ] Research venv isolation patterns in ComfyUI nodes
- [ ] Analyze PlayDiffusion's code structure for extraction potential
- [ ] Survey other ComfyUI nodes with heavy ML deps (how do they solve this?)
- [ ] Document each approach's trade-offs

### Deliverable
- Architecture decision record (ADR) with chosen approach

---

## Phase 3: Proof of Concept
**Goal:** Build minimal working version of chosen approach

### Tasks
- [ ] Implement basic inference with isolation
- [ ] Test model download/caching
- [ ] Verify ComfyUI environment remains intact

### Deliverable
- Working PoC with one PlayDiffusion feature (e.g., TTS)

---

## Phase 4: Integration & Testing
**Goal:** Production-ready implementation

### Tasks
- [ ] Full feature parity (loader, inpaint, TTS, RVC)
- [ ] Error handling and user feedback
- [ ] Test on fresh ComfyUI Portable install
- [ ] Documentation

### Deliverable
- Merged code with working auto-install

---

## Decisions Log

| Date | Decision | Context |
|------|----------|---------|
| 2026-04-12 | Start research project | Auto-install fails on embedded Python due to missing build tools |
