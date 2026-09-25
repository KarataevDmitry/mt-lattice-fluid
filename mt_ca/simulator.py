from __future__ import annotations

import torch

from mt_ca.config import MConfig
from mt_ca.fixed_point import decode_spinor
from mt_ca.holomorphy import clamp_density
from mt_ca.metrics import field_amplitude, total_norm_squared
from mt_ca.reversible import canonical_fixed, leapfrog_forward_fixed, leapfrog_reverse_fixed
from mt_ca.seeds import SeedClass, make_seed


class LatticeFluidSimulator:
    def __init__(
        self,
        ny: int,
        nx: int,
        cfg: MConfig | None = None,
        *,
        nz: int | None = None,
        device: str | torch.device | None = None,
        dtype: torch.dtype = torch.complex64,
    ) -> None:
        self.cfg = cfg or MConfig()
        self.ny = ny
        self.nx = nx
        if self.cfg.stencil == "fcc":
            self.nz = ny if nz is None else nz
        else:
            self.nz = None if nz is None else nz
        if device is None:
            device = "cuda" if torch.cuda.is_available() else "cpu"
        self.device = torch.device(device)
        self.dtype = dtype
        self.z = torch.zeros(*self.spatial_shape, 2, device=self.device, dtype=dtype)
        self.z_past = torch.zeros_like(self.z)
        self._f_curr: torch.Tensor | None = None
        self._f_past: torch.Tensor | None = None
        self._momentum_ledger: list[torch.Tensor] = []
        self._norm0: float | None = None

    @property
    def spatial_shape(self) -> tuple[int, ...]:
        if self.cfg.stencil == "fcc":
            assert self.nz is not None
            return (self.nz, self.ny, self.nx)
        return (self.ny, self.nx)

    def _sync_z_from_fixed(self) -> None:
        if self._f_curr is not None:
            self.z = decode_spinor(self._f_curr, frac_bits=self.cfg.frac_bits).to(
                device=self.device, dtype=self.dtype
            )
            self.z = clamp_density(self.z, self.cfg)

    def _init_leapfrog_state(self, z: torch.Tensor) -> None:
        f0 = canonical_fixed(z, self.cfg)
        self._f_curr = f0.clone()
        self._f_past = f0.clone()
        self._momentum_ledger = []
        self._sync_z_from_fixed()
        self.z_past = self.z.clone()

    def reset(self, seed_class: SeedClass = SeedClass.VACUUM) -> None:
        kw: dict = {
            "device": self.device,
            "dtype": self.dtype,
            "mod_bits": self.cfg.mod_bits,
            "frac_bits": self.cfg.frac_bits,
            "phase_bits": self.cfg.phase_bits,
        }
        if self.cfg.stencil == "fcc":
            kw["nz"] = self.nz
        self.z = make_seed(seed_class, self.ny, self.nx, **kw)
        self.z_past = self.z.clone()
        self._init_leapfrog_state(self.z)
        self._norm0 = total_norm_squared(self.z)

    def set_field(
        self,
        z: torch.Tensor,
        *,
        z_past: torch.Tensor | None = None,
        momentum_k: tuple[float, ...] | None = None,
    ) -> None:
        expected = (*self.spatial_shape, 2)
        if tuple(z.shape) != expected:
            raise ValueError(f"Expected {expected}, got {tuple(z.shape)}")
        self.z = z.to(device=self.device, dtype=self.dtype)
        if z_past is not None:
            self.z_past = z_past.to(device=self.device, dtype=self.dtype)
        elif momentum_k is not None:
            if self.cfg.stencil == "fcc":
                kz, ky, kx = (momentum_k + (0.0, 0.0, 0.0))[:3]
                rolled = torch.roll(self.z, shifts=(1, 1, 1), dims=(0, 1, 2))
                phase = torch.exp(
                    torch.tensor(-1j * (kz + ky + kx), device=self.device, dtype=self.dtype)
                )
            else:
                ky, kx = momentum_k[:2]
                rolled = torch.roll(self.z, shifts=(1, 1), dims=(0, 1))
                phase = torch.exp(
                    torch.tensor(-1j * (ky + kx), device=self.device, dtype=self.dtype)
                )
            self.z_past = rolled * phase
            n0 = total_norm_squared(self.z)
            n_p = total_norm_squared(self.z_past)
            if n_p > 1e-12:
                self.z_past = self.z_past * (n0 / n_p) ** 0.5
        else:
            self.z_past = self.z.clone()
        self._f_curr = canonical_fixed(self.z, self.cfg)
        self._f_past = canonical_fixed(self.z_past, self.cfg)
        self._momentum_ledger = []
        self._sync_z_from_fixed()
        self._norm0 = total_norm_squared(self.z)

    def step(self, steps: int = 1) -> torch.Tensor:
        assert self._f_curr is not None and self._f_past is not None
        for _ in range(steps):
            f_next, f_prev, f_kick = leapfrog_forward_fixed(self._f_curr, self._f_past, self.cfg)
            self._momentum_ledger.append(f_kick)
            self._f_curr = f_next
            self._f_past = f_prev
            self._sync_z_from_fixed()
            self.z_past = decode_spinor(self._f_past, frac_bits=self.cfg.frac_bits).to(
                device=self.device, dtype=self.dtype
            )
        return self.z

    def step_reverse(self, steps: int = 1) -> torch.Tensor:
        """T-reverse via leapfrog momentum ledger (§3.12)."""
        assert self._f_curr is not None and self._f_past is not None
        for _ in range(steps):
            if not self._momentum_ledger:
                raise ValueError("momentum ledger empty — nothing to reverse")
            f_kick = self._momentum_ledger.pop()
            f_past, f_curr = leapfrog_reverse_fixed(self._f_past, self._f_curr, f_kick, self.cfg)
            self._f_past = f_past
            self._f_curr = f_curr
            self._sync_z_from_fixed()
            self.z_past = decode_spinor(self._f_past, frac_bits=self.cfg.frac_bits).to(
                device=self.device, dtype=self.dtype
            )
        return self.z

    @property
    def norm0(self) -> float:
        if self._norm0 is None:
            return 0.0
        return self._norm0

    def norm(self) -> float:
        return total_norm_squared(self.z)

    def snapshot_amplitude(self) -> torch.Tensor:
        return field_amplitude(self.z).detach().cpu()
