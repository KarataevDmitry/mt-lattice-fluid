"""Second-order reversible leapfrog CA — projected collision on Planck ℤ (§3.12)."""

from __future__ import annotations

import torch

from mt_ca.config import MConfig
from mt_ca.fixed_point import decode_spinor, encode_spinor, leapfrog_invert
from mt_ca.projected_collision import projected_step_fixed


def canonicalize(z: torch.Tensor, cfg: MConfig) -> torch.Tensor:
    return decode_spinor(
        encode_spinor(z, frac_bits=cfg.frac_bits, mod_bits=cfg.mod_bits),
        frac_bits=cfg.frac_bits,
        mod_bits=cfg.mod_bits,
    )


def canonical_fixed(z: torch.Tensor, cfg: MConfig) -> torch.Tensor:
    return encode_spinor(z, frac_bits=cfg.frac_bits, mod_bits=cfg.mod_bits)


def leapfrog_forward_fixed(
    f_curr: torch.Tensor,
    f_past: torch.Tensor,
    cfg: MConfig,
) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
    """M-canonical tick: projected collision on Z_N[i] only (§3.12.5)."""
    return projected_step_fixed(f_curr, f_past, cfg)


def evolve_canonical(
    z: torch.Tensor,
    cfg: MConfig,
    steps: int = 1,
    *,
    z_past: torch.Tensor | None = None,
) -> torch.Tensor:
    """Apply g^steps on Z_N[i]; decode to ℂ² for readout only."""
    f_curr = canonical_fixed(z, cfg)
    f_past = canonical_fixed(z_past if z_past is not None else z, cfg)
    for _ in range(steps):
        f_curr, f_past, _ = leapfrog_forward_fixed(f_curr, f_past, cfg)
    return decode_spinor(f_curr, frac_bits=cfg.frac_bits)


def leapfrog_reverse_fixed(
    f_curr: torch.Tensor,
    f_next: torch.Tensor,
    f_kick: torch.Tensor,
    cfg: MConfig,
) -> tuple[torch.Tensor, torch.Tensor]:
    f_prev = leapfrog_invert(f_curr, f_next, f_kick, mod_bits=cfg.mod_bits)
    return f_prev, f_curr


def leapfrog_forward(
    z_curr: torch.Tensor,
    z_past: torch.Tensor,
    cfg: MConfig,
) -> tuple[torch.Tensor, torch.Tensor]:
    f_curr = canonical_fixed(z_curr, cfg)
    f_past = canonical_fixed(z_past, cfg)
    f_next, f_prev, _ = leapfrog_forward_fixed(f_curr, f_past, cfg)
    return (
        decode_spinor(f_next, frac_bits=cfg.frac_bits),
        decode_spinor(f_prev, frac_bits=cfg.frac_bits),
    )


def micro_step_reversible(
    z_curr: torch.Tensor,
    z_past: torch.Tensor,
    cfg: MConfig,
) -> tuple[torch.Tensor, torch.Tensor]:
    return leapfrog_forward(z_curr, z_past, cfg)


def unwind_with_kicks(
    f_past: torch.Tensor,
    f_curr: torch.Tensor,
    kicks: list[torch.Tensor],
    cfg: MConfig,
) -> torch.Tensor:
    f_p, f_c = f_past, f_curr
    for f_kick in reversed(kicks):
        f_p, f_c = leapfrog_reverse_fixed(f_p, f_c, f_kick, cfg)
    return f_c


def bit_exact_roundtrip_report(
    size: int = 64,
    steps: int = 32,
    device: str = "cpu",
    *,
    seed_class=None,
) -> dict:
    from mt_ca.seeds import SeedClass, make_seed
    from mt_ca.topology import winding_nearest_int, winding_robust

    if seed_class is None:
        seed_class = SeedClass.IMPULSE

    dev = torch.device(device)
    cfg = MConfig.for_stencil("hex", evolution="leapfrog", use_projected_collision=True)
    z0 = make_seed(seed_class, size, size, device=dev)
    f0 = canonical_fixed(z0, cfg)
    f_past = f0.clone()
    f_curr = f0.clone()
    kicks: list[torch.Tensor] = []
    w0 = winding_robust(decode_spinor(f0, frac_bits=cfg.frac_bits))
    n0 = winding_nearest_int(w0) if w0 == w0 and seed_class != SeedClass.IMPULSE else 0

    for _ in range(steps):
        f_next, f_prev, f_kick = leapfrog_forward_fixed(f_curr, f_past, cfg)
        kicks.append(f_kick)
        f_past = f_prev
        f_curr = f_next

    f_back = unwind_with_kicks(f_past, f_curr, kicks, cfg)
    exact = bool(torch.equal(f0, f_back))
    z_back = decode_spinor(f_back, frac_bits=cfg.frac_bits)
    z_ref = decode_spinor(f0, frac_bits=cfg.frac_bits)
    rel = float((z_back - z_ref).abs().max().item() / (z_ref.abs().max().item() + 1e-12))
    w_back = winding_robust(z_back)
    n_back = winding_nearest_int(w_back) if w_back == w_back and seed_class != SeedClass.IMPULSE else 0

    ok = exact or rel < 1e-6
    return {
        "id": "Leapfrog_bit_exact",
        "seed": seed_class.value if hasattr(seed_class, "value") else str(seed_class),
        "steps": steps,
        "bit_exact": exact,
        "max_rel_err": rel,
        "n0": n0,
        "n_back": n_back,
        "n_stable": n0 == n_back or seed_class == SeedClass.IMPULSE,
        "ok": ok,
        "note": "Z_N[i] projected collision + kick ledger (§3.12.5)",
    }
