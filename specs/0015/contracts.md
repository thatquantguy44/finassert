# 0015 — Contracts

[spec.md](spec.md) is canonical. Preserve financial semantics and existing catalog,
policy and artifact contracts. SHA256SUMS excludes itself; the manifest excludes
its own hash. External approval/pinning establishes trust, not a checksum alone.
Builds must reconcile wheel/sdist code and metadata with the exact producer tree.
