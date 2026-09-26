#!/usr/bin/env python3
"""Minimal forward envelope: M seed → T coarse ℬ → CMB-scale δT/T (META §3.0.1).

Back-of-envelope only — not a full C_ℓ solver.

Pipeline:
  1. boil → settle → half-space phase wall (§3.2 dogfood)
  2. coarse binomial macro on Δρ = |Φ|_wall − |Φ|_base (slice at iz)
  3. extra ν_viscosity passes (§4.1.2 proxy for long bubble evolution)
  4. extrapolate to N_CMB via nu_coarse_passes(N_CMB, block)
  5. invert: which δφ lands at δT/T ~ 10⁻⁵ after smoothing?
"""

from __future__ import annotations

import argparse
import json
import math
import sys
import time
from pathlib import Path
from typing import Any

_SCRIPTS = Path(__file__).resolve().parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

import torch

from mt_ca.config import MConfig
from mt_ca.macro import binomial121_smooth, macro_amplitude
from mt_ca.seeds import boil_ocean_spinor_3d
from mt_ca.simulator import LatticeFluidSimulator
from mt_ca.si_constants import SI, T_CMB_K_REF
from mt_ca.t_validation import coarse_grain, nu_coarse_passes

from run_boil_wall_sweep import apply_half_space_wall

CMB_DELTA_T_OVER_T = 1.0e-5


def coarse_slice(z: torch.Tensor, iz: int, block: int) -> torch.Tensor:
    """2D macro |Φ| at lattice slice iz (3D spinor → 2D macro slice)."""
    if z.ndim == 4:
        return coarse_grain(z[iz], block)
    return coarse_grain(z, block)


def perturbation_metrics(
    base: torch.Tensor,
    wall: torch.Tensor,
    *,
    iz: int,
    block: int,
) -> dict[str, float]:
    """Δρ relative to settled boil baseline — CMB proxy on T layer."""
    c0 = coarse_slice(base, iz, block)
    c1 = coarse_slice(wall, iz, block)
    d = c1 - c0
    mean = float(c0.mean().item())
    if mean <= 0.0:
        return {"mean": mean, "max_rel": 0.0, "rms_rel": 0.0}
    return {
        "mean": mean,
        "max_rel": float(d.abs().max().item()) / mean,
        "rms_rel": float(d.std().item()) / mean,
    }


def smooth_decay_curve(
    base: torch.Tensor,
    wall: torch.Tensor,
    *,
    iz: int,
    block: int,
    nu_passes: list[int],
) -> list[dict[str, float]]:
    """How Δρ rms/mean decays under extra binomial ν passes."""
    c0 = coarse_slice(base, iz, block)
    c1 = coarse_slice(wall, iz, block)
    d = c1 - c0
    mean = float(c0.mean().item())
    rows: list[dict[str, float]] = []
    for p in nu_passes:
        ds = binomial121_smooth(d, passes=p) if p > 0 else d
        rows.append(
            {
                "nu_passes": float(p),
                "max_rel": float(ds.abs().max().item()) / mean,
                "rms_rel": float(ds.std().item()) / mean,
            }
        )
    return rows


def fit_power_law_alpha(
    nu_passes: list[int],
    rms_rel: list[float],
    *,
    nu_max: int = 64,
    floor: float = 1e-12,
) -> float | None:
    """rms ~ rms0 · ν^{-α} on early ν only (tail is super-exponential)."""
    pts = [
        (math.log(float(p)), math.log(r))
        for p, r in zip(nu_passes, rms_rel, strict=True)
        if 0 < p <= nu_max and r > floor
    ]
    if len(pts) < 2:
        return None
    xs = [x for x, _ in pts]
    ys = [y for _, y in pts]
    x_mean = sum(xs) / len(xs)
    y_mean = sum(ys) / len(ys)
    num = sum((x - x_mean) * (y - y_mean) for x, y in pts)
    den = sum((x - x_mean) ** 2 for x in xs)
    if den <= 0.0:
        return None
    return -num / den


def nu_for_rms_target(
    nu_passes: list[int],
    rms_rel: list[float],
    target: float,
) -> tuple[float, float]:
    """Interpolate (log ν, log rms) to find ν where rms=target (rms falls with ν)."""
    pts = sorted(
        [(float(p), r) for p, r in zip(nu_passes, rms_rel, strict=True) if p > 0 and r > 0.0],
        key=lambda t: t[0],
    )
    if not pts:
        return 1.0, 0.0
    if target >= pts[0][1]:
        return pts[0][0], pts[0][1]
    if target <= pts[-1][1]:
        return pts[-1][0], pts[-1][1]
    for (p0, r0), (p1, r1) in zip(pts, pts[1:], strict=False):
        if r0 >= target >= r1:
            log_t = math.log(target)
            t = (log_t - math.log(r0)) / (math.log(r1) - math.log(r0))
            nu = math.exp(math.log(p0) + t * (math.log(p1) - math.log(p0)))
            return nu, target
    closest = min(pts, key=lambda pr: abs(math.log(pr[1] / target)))
    return closest[0], closest[1]


def loglog_extrapolate(
    nu_passes: list[int],
    rms_rel: list[float],
    nu_query: float,
) -> float:
    """Piecewise log-log linear extrapolation from measured decay curve."""
    pts = sorted(
        [(float(p), r) for p, r in zip(nu_passes, rms_rel, strict=True) if p > 0 and r > 0.0],
        key=lambda t: t[0],
    )
    if not pts:
        return 0.0
    if nu_query <= pts[0][0]:
        return pts[0][1]
    for (p0, r0), (p1, r1) in zip(pts, pts[1:], strict=False):
        if p0 <= nu_query <= p1:
            t = (math.log(nu_query) - math.log(p0)) / (math.log(p1) - math.log(p0))
            return math.exp(math.log(r0) + t * (math.log(r1) - math.log(r0)))
    p0, r0 = pts[-2]
    p1, r1 = pts[-1]
    t = (math.log(nu_query) - math.log(p0)) / (math.log(p1) - math.log(p0))
    return math.exp(math.log(r0) + t * (math.log(r1) - math.log(r0)))


def invert_delta_for_target(
    *,
    delta_angle: float,
    rms_rel: float,
    rms_at_nu: float,
    target: float = CMB_DELTA_T_OVER_T,
) -> dict[str, float]:
    """Linear in δφ: scale so measured rms_at_nu maps to target."""
    if rms_at_nu <= 0.0 or rms_rel <= 0.0:
        return {
            "delta_for_target_local": float("nan"),
            "linear_scale": float("nan"),
        }
    linear_scale = target / rms_at_nu
    return {
        "delta_for_target_local": delta_angle * linear_scale,
        "linear_scale": linear_scale,
    }


def calibrate_wall_row(
    sim: LatticeFluidSimulator,
    cfg: MConfig,
    *,
    nz: int,
    settle: int,
    delta_angle: float,
    axis: str,
    block: int,
    iz: int,
    nu_passes: list[int],
) -> dict[str, Any]:
    kw = {
        "device": sim.device,
        "dtype": sim.dtype,
        "mod_bits": cfg.mod_bits,
        "frac_bits": cfg.frac_bits,
        "phase_bits": cfg.phase_bits,
    }
    sim.set_field(boil_ocean_spinor_3d(nz, nz, nz, **kw))
    if settle > 0:
        sim.step(settle)
    base = sim.z.clone()
    wall = apply_half_space_wall(
        base,
        axis=axis,
        frac_bits=cfg.frac_bits,
        mod_bits=cfg.mod_bits,
        dtype=sim.dtype,
        delta_angle=delta_angle,
    )
    m0 = perturbation_metrics(base, base, iz=iz, block=block)
    m1 = perturbation_metrics(base, wall, iz=iz, block=block)
    decay = smooth_decay_curve(base, wall, iz=iz, block=block, nu_passes=nu_passes)
    return {
        "settle": settle,
        "delta_angle": delta_angle,
        "axis": axis,
        "zero_control_max_rel": m0["max_rel"],
        "max_rel": m1["max_rel"],
        "rms_rel": m1["rms_rel"],
        "smooth_decay": decay,
    }


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--size", type=int, default=48)
    p.add_argument("--block", type=int, default=4)
    p.add_argument("--iz", type=int, default=-1, help="slice index (-1 = nz//2)")
    p.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    p.add_argument("--settles", default="0,128,256")
    p.add_argument("--angles", default="0.01,0.05,0.125,0.25")
    p.add_argument("--axis", default="x")
    p.add_argument(
        "--nu-passes",
        default="1,4,16,64,256,1024",
        help="extra binomial passes for decay curve",
    )
    p.add_argument("--target", type=float, default=CMB_DELTA_T_OVER_T)
    p.add_argument("--json", action="store_true")
    args = p.parse_args()
    if args.device == "cuda" and not torch.cuda.is_available():
        args.device = "cpu"

    nz = args.size
    iz = args.iz if args.iz >= 0 else nz // 2
    settles = [int(x) for x in args.settles.split(",") if x.strip()]
    angles = [float(x) for x in args.angles.split(",") if x.strip()]
    nu_list = [int(x) for x in args.nu_passes.split(",") if x.strip()]

    bubble = SI.bubble_tick_row()
    bath = SI.vacuum_bath_row()
    n_cmb = int(bubble["N_CMB"])
    nu_at_ncmb = nu_coarse_passes(n_cmb, args.block)

    cfg = MConfig.for_stencil("fcc")
    sim = LatticeFluidSimulator(nz, nz, cfg, nz=nz, device=args.device)

    t0 = time.perf_counter()
    cal_rows: list[dict[str, Any]] = []
    for settle in settles:
        for angle in angles:
            row = calibrate_wall_row(
                sim,
                cfg,
                nz=nz,
                settle=settle,
                delta_angle=angle,
                axis=args.axis,
                block=args.block,
                iz=iz,
                nu_passes=nu_list,
            )
            cal_rows.append(row)
            print(
                f"settle={settle:3d} δ={angle:.4f} "
                f"max/mean={row['max_rel']:.4e} rms/mean={row['rms_rel']:.4e}",
                flush=True,
            )

    # Best calibration row: largest settle with measurable signal
    signal_rows = [r for r in cal_rows if r["rms_rel"] > 0.0]
    ref = max(signal_rows, key=lambda r: (r["settle"], r["rms_rel"])) if signal_rows else cal_rows[0]
    decay_nu = [int(r["nu_passes"]) for r in ref["smooth_decay"]]
    decay_rms = [r["rms_rel"] for r in ref["smooth_decay"]]
    alpha = fit_power_law_alpha(decay_nu, decay_rms) or 0.5

    nu_for_target_f, rms_at_target_nu = nu_for_rms_target(decay_nu, decay_rms, args.target)
    nu_for_target = int(round(nu_for_target_f))

    rms_blind_ncmb = loglog_extrapolate(decay_nu, decay_rms, float(nu_at_ncmb))
    inv = invert_delta_for_target(
        delta_angle=float(ref["delta_angle"]),
        rms_rel=float(ref["rms_rel"]),
        rms_at_nu=float(rms_at_target_nu or ref["rms_rel"]),
        target=args.target,
    )
    effective_alpha_ncmb: float | None = None
    if ref["rms_rel"] > 0.0 and rms_blind_ncmb > 0.0 and nu_at_ncmb > 0:
        effective_alpha_ncmb = math.log(ref["rms_rel"] / rms_blind_ncmb) / math.log(float(nu_at_ncmb))
    elif ref["rms_rel"] > 0.0 and nu_at_ncmb > 0:
        effective_alpha_ncmb = float("inf")

    elapsed = time.perf_counter() - t0
    out: dict[str, Any] = {
        "id": "cmb_forward_envelope",
        "dims": f"{nz}^3",
        "block": args.block,
        "iz": iz,
        "axis": args.axis,
        "seconds": round(elapsed, 2),
        "cmb_target_delta_T_over_T": args.target,
        "T_CMB_K": T_CMB_K_REF,
        "T_M_bath_K": bath["T_M_bath_K"],
        "log10_T_M_over_CMB": bath["log10_T_M_bath_over_CMB"],
        "N_CMB": n_cmb,
        "N_CMB_sci": bubble["N_CMB_sci"],
        "N_today": bubble["N_today"],
        "nu_coarse_at_N_CMB": nu_at_ncmb,
        "log10_nu_at_N_CMB": math.log10(nu_at_ncmb) if nu_at_ncmb > 0 else None,
        "calibration": cal_rows,
        "reference_row": {
            "settle": ref["settle"],
            "delta_angle": ref["delta_angle"],
            "max_rel": ref["max_rel"],
            "rms_rel": ref["rms_rel"],
        },
        "smooth_decay_fit": {
            "alpha_power_law_early_nu": alpha,
            "nu_passes_for_target_local": nu_for_target,
            "nu_passes_for_target_interp": nu_for_target_f,
            "rms_at_target_nu": rms_at_target_nu,
            "rms_blind_extrapolation_at_N_CMB": rms_blind_ncmb,
            "effective_alpha_blind_N_CMB": effective_alpha_ncmb,
            "decay_curve": ref["smooth_decay"],
        },
        "extrapolation_local": inv,
        "interpretation": [
            "Pure phase wall on unsettled boil → zero Δ|Φ| (CMB-blind at t=0).",
            "After settle, boil texture breaks symmetry; wall Δ|Φ|/mean ~ few % for δ~0.1–0.25.",
            f"Local ℬ: ~{nu_for_target_f:.0f} binomial passes → rms/mean≈{args.target:.0e} (CMB-scale).",
            f"Blind log-log extrapolation to N_CMB ν≈10^{math.log10(nu_at_ncmb):.1f} → rms~{rms_blind_ncmb:.0e} (signal erased).",
            f"⇒ CMB δT/T is not 'frozen wall smoothed once' — needs acoustic growth / sub-horizon modes between BB and N_CMB.",
            f"Local match: δφ≈{inv['delta_for_target_local']:.4f} rad (~{math.degrees(inv['delta_for_target_local']):.3f}°) at ν≈{nu_for_target_f:.0f}.",
            "M bath (~10³¹ K) ≠ CMB (2.73 K): last scattering is T-layer at N_CMB only.",
        ],
    }

    print("\n=== CMB forward envelope ===", flush=True)
    print(f"N_CMB = {bubble['N_CMB_sci']}  nu_coarse ≈ 10^{math.log10(nu_at_ncmb):.2f}", flush=True)
    print(f"T_M,bath = {bath['T_M_bath_K']:.3e} K  T_CMB = {T_CMB_K_REF} K", flush=True)
    print(
        f"ref settle={ref['settle']} δ={ref['delta_angle']:.4f} "
        f"rms/mean={ref['rms_rel']:.4e}",
        flush=True,
    )
    print(
        f"early-ν α ≈ {alpha:.3f}  local ν for δT/T≈{args.target:.0e}: {nu_for_target_f:.1f}",
        flush=True,
    )
    print(
        f"→ δφ local match: {inv['delta_for_target_local']:.4f} rad "
        f"({math.degrees(inv['delta_for_target_local']):.3f}°)",
        flush=True,
    )
    if effective_alpha_ncmb == float("inf"):
        alpha_txt = "∞ (signal erased)"
    elif effective_alpha_ncmb is None:
        alpha_txt = "n/a"
    else:
        alpha_txt = f"{effective_alpha_ncmb:.2f}"
    print(
        f"blind extrapolation rms@N_CMB ≈ {rms_blind_ncmb:.0e} (effective α≈{alpha_txt})",
        flush=True,
    )
    for line in out["interpretation"]:
        print(f"  · {line}", flush=True)

    if args.json:
        print(json.dumps(out, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
