"""Mapping between platform routes and regional routes.

Riot splits its endpoints across two route families:
- Platform routes (jp1, kr, na1, ...): summoner-v4, league-v4, spectator-v5
- Regional routes (asia, americas, europe, sea): match-v5, account-v1
"""

from __future__ import annotations

PLATFORM_TO_REGIONAL: dict[str, str] = {
    # Asia
    "jp1": "asia",
    "kr": "asia",
    # Americas
    "na1": "americas",
    "br1": "americas",
    "la1": "americas",
    "la2": "americas",
    # Europe
    "euw1": "europe",
    "eun1": "europe",
    "tr1": "europe",
    "ru": "europe",
    "me1": "europe",
    # SEA
    "oc1": "sea",
    "ph2": "sea",
    "sg2": "sea",
    "th2": "sea",
    "tw2": "sea",
    "vn2": "sea",
}


def regional_for(platform: str) -> str:
    """Return the regional route for a platform; raises if unknown."""
    key = platform.lower()
    if key not in PLATFORM_TO_REGIONAL:
        raise ValueError(
            f"unknown platform '{platform}'. "
            f"Known: {sorted(PLATFORM_TO_REGIONAL)}"
        )
    return PLATFORM_TO_REGIONAL[key]
