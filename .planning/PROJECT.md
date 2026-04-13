# APZmedia ComfyUI Audio Tools - PlayDiffusion Integration Analysis

## Project Goal

Research and design the optimal architecture for integrating PlayDiffusion into ComfyUI while:
1. Preserving ComfyUI's environment integrity (no dependency hell)
2. Handling PlayDiffusion's heavy dependencies (~10GB model, complex build requirements)
3. Providing a smooth user experience (auto-install without manual intervention)

## Problem Statement

PlayDiffusion is difficult to integrate because:
- Requires building from git repo (needs hatchling, build tools)
- Large model downloads (~10GB)
- Heavy Python dependencies that may conflict with ComfyUI's pinned versions
- Current auto-install fails on ComfyUI Portable (embedded Python lacks build tools)

## Potential Approaches to Analyze

### Option A: Direct pip install (current, failing)
Install PlayDiffusion directly into ComfyUI's Python environment.
- Pros: Simple, single environment
- Cons: Dependency conflicts, build failures on portable installs

### Option B: Isolated venv
Run PlayDiffusion in a separate virtual environment, communicate via IPC/API.
- Pros: Complete isolation, no dependency conflicts
- Cons: Complex setup, need to manage two Python processes

### Option C: Extract and rebuild
Strip down PlayDiffusion to just what we need, rebuild as pure ComfyUI nodes.
- Pros: Full control, lightweight
- Cons: High maintenance, may violate license, updates break integration

### Option D: Docker/container approach
Run PlayDiffusion in a container.
- Pros: Complete isolation
- Cons: Requires Docker, complex for Windows users

### Option E: Pre-built wheels
Host pre-built wheels to skip the build step.
- Pros: No build tools needed
- Cons: Platform-specific, maintenance burden

## Success Criteria

1. Installation works on ComfyUI Portable (Windows) without manual pip commands
2. No dependency conflicts with other ComfyUI nodes
3. Model downloads happen automatically and are cached properly
4. Error messages are clear when things go wrong
5. Updates to PlayDiffusion don't break the integration

## Research Questions

1. What are PlayDiffusion's exact dependencies and their versions?
2. Which dependencies conflict with ComfyUI's common dependency set?
3. Can we isolate PlayDiffusion's inference code without the full package?
4. What's the minimal viable subset of PlayDiffusion functionality?
5. How do other ComfyUI nodes handle heavy ML dependencies (e.g., talk-llama, video nodes)?

## References

- PlayDiffusion repo: https://github.com/playht/PlayDiffusion
- Current integration attempt: `play_diffusion_loader.py`
- ComfyUI custom node guidelines
- ComfyUI Manager install hooks
