# PlayDiffusion Dependency Analysis

## Core Dependencies (pinned versions)

| Package | Version | ComfyUI Compatible? | Risk Level |
|---------|---------|---------------------|------------|
| torch | ==2.6.0 | ⚠️ ComfyUI uses 2.3.x or 2.4.x typically | HIGH |
| torchaudio | ==2.6.0 | Same as torch | HIGH |
| numpy | ==1.24.3 | ⚠️ Older than ComfyUI's 1.26+ | MEDIUM |
| fairseq2 | ==0.4.4 | Heavy C++ dependency | HIGH |
| syllables | git+... | Another git dependency | MEDIUM |
| pydantic | ==2.11.5 | v2 vs v1 potential issues | MEDIUM |
| huggingface-hub | ==0.31.4 | Usually compatible | LOW |
| tokenizers | ==0.21.1 | May conflict | MEDIUM |
| torchtune | ==0.6.1 | Heavy dep | HIGH |
| torchao | ==0.11.0 | Another torch dep | HIGH |

## Key Findings

### 1. PyTorch Version Pin
PlayDiffusion requires **exactly torch 2.6.0**. ComfyUI typically uses:
- 2.3.x for stability
- 2.4.x for newer features
- 2.6.x is very recent (Jan 2025)

This is a **hard blocker** for direct installation.

### 2. Multiple Git Dependencies
- `syllables @ git+https://github.com/playht/python-syllables.git`
- PlayDiffusion itself is git-only (no PyPI package)

These require build tools that embedded Python lacks.

### 3. Heavy ML Stack
- fairseq2: Facebook's sequence modeling (large C++ extension)
- torchtune: Meta's fine-tuning library
- torchao: PyTorch AO (optimization)

These all have compiled components.

## Conflict Matrix

```
PlayDiffusion torch==2.6.0  →  ComfyUI torch~=2.3.0  = CONFLICT
PlayDiffusion numpy==1.24.3 →  ComfyUI numpy~=1.26   = POSSIBLE CONFLICT
PlayDiffusion pydantic v2   →  ComfyUI pydantic v1   = CONFLICT in some nodes
```

## Conclusion

**Direct integration is NOT viable.** The PyTorch version pin alone makes this impossible for most ComfyUI users.

## Recommended Approaches

1. **Isolated venv** (Option B) - Only viable path for full compatibility
2. **Extract inference code** (Option C) - High effort but cleanest
3. **Patch requirements** - Contact PlayHT to loosen version pins

## References

- https://github.com/playht/PlayDiffusion/blob/main/pyproject.toml
