# Docker Layer Architecture Comparison

## Method 1: Direct Extension
```
┌─────────────────────────────┐
│  Your Circuit-Synth Code    │  ← Layer 6 (your additions)
├─────────────────────────────┤
│  Python Dependencies       │  ← Layer 5 (pip install)  
├─────────────────────────────┤
│  KiCad Runtime Files        │  ← Layer 4 (inherited)
├─────────────────────────────┤
│  KiCad Build Tools          │  ← Layer 3 (inherited - unused!)
├─────────────────────────────┤
│  System Dependencies       │  ← Layer 2 (inherited)
├─────────────────────────────┤
│  Debian Base                │  ← Layer 1 (inherited)
└─────────────────────────────┘
Final Size: ~2GB (includes unused build tools)
```

## Method 2: Multi-Stage Build (Our Implementation)
```
┌─────────────────────────────┐
│  Your Circuit-Synth Code    │  ← Layer 6 (your code)
├─────────────────────────────┤
│  Rust Modules               │  ← Layer 5 (maturin builds)
├─────────────────────────────┤
│  Python Dependencies       │  ← Layer 4 (pip install)
├─────────────────────────────┤
│  KiCad Runtime Files ONLY   │  ← Layer 3 (selective copy)
├─────────────────────────────┤
│  Runtime Dependencies      │  ← Layer 2 (lean deps)
├─────────────────────────────┤
│  Python 3.11 Slim          │  ← Layer 1 (clean base)
└─────────────────────────────┘
Final Size: ~800MB (no build cruft)

Source Image (not in final):
┌─────────────────────────────┐
│  KiCad Build Tools          │  ← Used for COPY --from= only
│  KiCad Source Code          │  ← Then discarded
│  Development Headers        │
│  Compilation Dependencies   │
└─────────────────────────────┘
```