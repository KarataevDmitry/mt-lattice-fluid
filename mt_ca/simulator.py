from __future__ import annotations

import torch

from mt_ca.config import MConfig
from mt_ca.fixed_point import decode_spinor
from mt_ca.metrics import field_amplitude, total_norm_squared
from mt_ca.reversible import canonical_fixed, leapfrog_forward_fixed, leapfrog_reverse_fixed
from mt_ca.seeds import SeedClass, make_seed
from mt_ca.spinor import micro_step


class LatticeFluidSimulator:
    def __init__(
        self,
        ny: int,
        nx: int,
        cfg: MConfig | None = None,
        *,
        device: str | torch.device | None = None,
        dtype: torch.dtype = torch.complex64,
    ) -> None:
        self.ny = ny
        self.nx = nx
        self.cfg = cfg or MConfig()
        if device is None:
            device = "cuda" if torch.cuda.is_available() else "cpu"
        self.device = torch.device(device)
        self.dtype = dtype
        self.z = torch.zeros(ny, nx, 2, device=self.device, dtype=dtype)
        self.z_past = torch.zeros_like(self.z)
        self._f_curr: torch.Tensor | None = None
        self._f_past: torch.Tensor | None = None
        self._kick_ledger: list[torch.Tensor] = []
        self._norm0: float | None = None

    def _sync_z_from_fixed(self) -> None:
        if self._f_curr is not None:
            self.z = decode_spinor(self._f_curr, frac_bits=self.cfg.frac_bits).to(
                device=self.device, dtype=self.dtype
            )

    def _init_leapfrog_state(self, z: torch.Tensor) -> None:
        f0 = canonical_fixed(z, self.cfg)
        self._f_curr = f0.clone()
        self._f_past = f0.clone()
        self._kick_ledger = []
        self._sync_z_from_fixed()
        self.z_past = self.z.clone()

    def reset(self, seed_class: SeedClass = SeedClass.VACUUM) -> None:
        kw: dict = {"device": self.device, "dtype": self.dtype}
        if seed_class is SeedClass.VACUUM:
            kw["amplitude"] = self.cfg.vacuum_amplitude
        self.z = make_seed(seed_class, self.ny, self.nx, **kw)
        self.z_past = self.z.clone()
        if self.cfg.is_leapfrog:
            self._init_leapfrog_state(self.z)
        else:
            self._f_curr = None
            self._f_past = None
            self._kick_ledger = []
        self._norm0 = total_norm_squared(self.z)

    def set_field(self, z: torch.Tensor) -> None:
        expected = (self.ny, self.nx, 2)
        if tuple(z.shape) != expected:
            raise ValueError(f"Expected {expected}, got {tuple(z.shape)}")
        self.z = z.to(device=self.device, dtype=self.dtype)
        self.z_past = self.z.clone()
        if self.cfg.is_leapfrog:
            self._init_leapfrog_state(self.z)
        else:
            self._f_curr = None
            self._f_past = None
            self._kick_ledger = []
        self._norm0 = total_norm_squared(self.z)

    def step(self, steps: int = 1) -> torch.Tensor:
        for _ in range(steps):
            if self.cfg.is_leapfrog:
                assert self._f_curr is not None and self._f_past is not None
                f_next, f_prev, f_kick = leapfrog_forward_fixed(
                    self._f_curr, self._f_past, self.cfg
                )
                self._kick_ledger.append(f_kick)
                self._f_curr = f_next
                self._f_past = f_prev
                self._sync_z_from_fixed()
                self.z_past = decode_spinor(self._f_past, frac_bits=self.cfg.frac_bits).to(
                    device=self.device, dtype=self.dtype
                )
            else:
                self.z = micro_step(self.z, self.cfg)
        return self.z

    def step_reverse(self, steps: int = 1) -> torch.Tensor:
        """T-reverse via leapfrog kick ledger (requires evolution=leapfrog)."""
        if not self.cfg.is_leapfrog:
            raise ValueError("step_reverse requires cfg.evolution='leapfrog'")
        assert self._f_curr is not None and self._f_past is not None
        for _ in range(steps):
            if not self._kick_ledger:
                raise ValueError("kick ledger empty — nothing to reverse")
            f_kick = self._kick_ledger.pop()
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
