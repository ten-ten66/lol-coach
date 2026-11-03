from __future__ import annotations

import asyncio
import json

import click
from rich.console import Console
from rich.table import Table

from lol_coach.config import get_settings
from lol_coach.db.session import session_scope
from lol_coach.riot.client import AsyncRiotClient
from lol_coach.riot.errors import NotFoundError, RiotAPIError
from lol_coach.riot.regions import regional_for
from lol_coach.services.aggregation import recompute_all
from lol_coach.services.recommendation import PickedChampion, Recommendation, recommend
from lol_coach.services.summoner_stats import SummonerStats, SummonerStatsService
from lol_coach.workers.sampler import SamplingResult, sample_high_rank


@click.group()
def main() -> None:
    """lol-coach command-line interface."""


# ---------- serve --------------------------------------------------------


@main.command()
@click.option("--host", default="127.0.0.1", show_default=True)
@click.option("--port", default=8000, show_default=True, type=int)
@click.option("--reload/--no-reload", default=True, show_default=True)
def serve(host: str, port: int, reload: bool) -> None:
    """Start the FastAPI server (dev)."""
    import uvicorn

    uvicorn.run("lol_coach.main:app", host=host, port=port, reload=reload)


# ---------- stats --------------------------------------------------------

QUEUE_LABELS = {
    420: "Ranked Solo",
    440: "Ranked Flex",
    400: "Normal Draft",
    430: "Normal Blind",
    450: "ARAM",
    700: "Clash",
}


@main.command()
@click.argument("riot_id")
@click.option("--platform", default=None, help="Platform route (e.g. 'jp1'). Defaults to config.")
@click.option("--count", default=20, show_default=True, type=int)
@click.option(
    "--queue", default=420, show_default=True, type=int, help="Queue ID (0 = all queues)."
)
@click.option("--json", "as_json", is_flag=True, help="Output raw JSON instead of tables.")
def stats(riot_id: str, platform: str | None, count: int, queue: int, as_json: bool) -> None:
    """Show recent match stats for RIOT_ID (format: 'Name#TAG')."""
    if "#" not in riot_id:
        raise click.BadParameter("expected 'Name#TAG' format (e.g. 'Faker#KR1')")
    game_name, tag_line = riot_id.split("#", 1)
    settings = get_settings()
    plat = (platform or settings.default_region).lower()
    regional = regional_for(plat)
    queue_filter: int | None = queue if queue != 0 else None

    console = Console()
    try:
        result = asyncio.run(
            _run_stats(
                api_key=settings.riot_api_key.get_secret_value(),
                regional=regional,
                game_name=game_name,
                tag_line=tag_line,
                count=count,
                queue=queue_filter,
            )
        )
    except NotFoundError as e:
        console.print(f"[red]Riot ID not found:[/red] {game_name}#{tag_line} ({e})")
        raise SystemExit(2) from e
    except RiotAPIError as e:
        console.print(f"[red]Riot API error:[/red] {e}")
        raise SystemExit(1) from e

    if as_json:
        click.echo(json.dumps(_stats_to_dict(result), indent=2, ensure_ascii=False, default=str))
    else:
        _render_stats(console, result, plat, queue_filter)


async def _run_stats(
    api_key: str,
    regional: str,
    game_name: str,
    tag_line: str,
    count: int,
    queue: int | None,
) -> SummonerStats:
    async with AsyncRiotClient(api_key) as client, session_scope() as session:
        service = SummonerStatsService(client, session)
        return await service.fetch(regional, game_name, tag_line, count=count, queue=queue)


def _stats_to_dict(s: SummonerStats) -> dict[str, object]:
    return {
        "game_name": s.game_name,
        "tag_line": s.tag_line,
        "puuid": s.puuid,
        "total_games": s.total_games,
        "total_wins": s.total_wins,
        "win_rate": s.win_rate,
        "by_champion": [
            {
                "champion": c.champion,
                "games": c.games,
                "wins": c.wins,
                "win_rate": c.win_rate,
                "kda": c.kda,
                "avg_cs": c.avg_cs,
            }
            for c in s.by_champion
        ],
        "matches": [m.__dict__ for m in s.matches],
    }


def _render_stats(console: Console, s: SummonerStats, platform: str, queue: int | None) -> None:
    queue_label = QUEUE_LABELS.get(queue, str(queue)) if queue else "all queues"
    console.print()
    console.print(f"[bold cyan]{s.game_name}#{s.tag_line}[/bold cyan] [dim]({platform})[/dim]")
    if s.total_games == 0:
        console.print(f"[yellow]No matches found for queue {queue_label}.[/yellow]")
        return

    console.print(
        f"  recent {s.total_games} games on [magenta]{queue_label}[/magenta]: "
        f"[bold]{s.total_wins}W-{s.total_games - s.total_wins}L[/bold] "
        f"({s.win_rate * 100:.1f}% win rate)"
    )

    table = Table(title="By champion", show_lines=False)
    table.add_column("Champion", style="cyan")
    table.add_column("Games", justify="right")
    table.add_column("W-L", justify="right")
    table.add_column("WR %", justify="right")
    table.add_column("KDA", justify="right")
    table.add_column("Avg CS", justify="right")
    for c in s.by_champion:
        wr_color = "green" if c.win_rate >= 0.55 else "red" if c.win_rate < 0.45 else "white"
        table.add_row(
            c.champion,
            str(c.games),
            f"{c.wins}-{c.games - c.wins}",
            f"[{wr_color}]{c.win_rate * 100:.1f}[/{wr_color}]",
            f"{c.kda:.2f}",
            f"{c.avg_cs:.1f}",
        )
    console.print(table)

    detail = Table(title="Recent matches", show_lines=False)
    detail.add_column("Result", justify="center")
    detail.add_column("Champion", style="cyan")
    detail.add_column("Role", style="dim")
    detail.add_column("K/D/A", justify="right")
    detail.add_column("CS", justify="right")
    detail.add_column("Duration", justify="right")
    for m in s.matches:
        result = "[green]W[/green]" if m.win else "[red]L[/red]"
        mins, secs = divmod(m.game_duration_sec, 60)
        detail.add_row(
            result,
            m.champion,
            m.role or "-",
            f"{m.kills}/{m.deaths}/{m.assists}",
            str(m.cs),
            f"{mins}:{secs:02d}",
        )
    console.print(detail)


# ---------- ingest --------------------------------------------------------


@main.group()
def ingest() -> None:
    """Data ingestion commands."""


@ingest.command("sample")
@click.option("--platform", default=None, help="Platform route. Defaults to config DEFAULT_REGION.")
@click.option("--players", default=20, show_default=True, type=int)
@click.option("--matches-per-player", default=20, show_default=True, type=int)
@click.option("--concurrency", default=5, show_default=True, type=int)
def ingest_sample(
    platform: str | None, players: int, matches_per_player: int, concurrency: int
) -> None:
    """One-shot: sample top-rank players and ingest their recent ranked solo matches."""
    settings = get_settings()
    plat = platform or settings.default_region
    console = Console()
    console.print(f"[bold]Sampling[/bold] {plat}: {players} players x {matches_per_player} matches")
    result = asyncio.run(
        _run_sample(
            settings.riot_api_key.get_secret_value(), plat, players, matches_per_player, concurrency
        )
    )
    console.print(
        f"[green]Done.[/green] players={result.players_sampled} seen={result.matches_seen} "
        f"ingested={result.matches_ingested}"
    )


async def _run_sample(
    api_key: str, platform: str, players: int, mpp: int, concurrency: int
) -> SamplingResult:
    async with AsyncRiotClient(api_key) as client, session_scope() as session:
        result = await sample_high_rank(
            client,
            session,
            platform,
            n_players=players,
            matches_per_player=mpp,
            concurrency=concurrency,
        )
        return result


# ---------- aggregate -----------------------------------------------------


@main.command()
def aggregate() -> None:
    """Recompute matchup and synergy aggregate tables."""
    console = Console()
    matchups, synergies = asyncio.run(_run_aggregate())
    console.print(f"[green]Done.[/green] matchup rows={matchups} synergy rows={synergies}")


async def _run_aggregate() -> tuple[int, int]:
    async with session_scope() as session:
        return await recompute_all(session)


# ---------- draft ---------------------------------------------------------


@main.command()
@click.option("--patch", required=True, help="Patch version, e.g. '14.10'")
@click.option(
    "--ally",
    "allies",
    multiple=True,
    help="Repeatable: champion_id:role (e.g. 64:JUNGLE)",
)
@click.option(
    "--enemy",
    "enemies",
    multiple=True,
    help="Repeatable: champion_id:role (e.g. 86:TOP)",
)
@click.option(
    "--missing-role",
    type=click.Choice(["TOP", "JUNGLE", "MIDDLE", "BOTTOM", "UTILITY"]),
    required=True,
)
@click.option("--top-n", default=5, show_default=True, type=int)
@click.option("--tier-band", default="ALL", show_default=True)
def draft(
    patch: str,
    allies: tuple[str, ...],
    enemies: tuple[str, ...],
    missing_role: str,
    top_n: int,
    tier_band: str,
) -> None:
    """Recommend champions for an open role in a draft."""

    def parse(s: str) -> PickedChampion:
        cid, _, role = s.partition(":")
        return PickedChampion(int(cid), role.upper())

    a_picks = [parse(s) for s in allies]
    e_picks = [parse(s) for s in enemies]

    recs = asyncio.run(_run_draft(patch, tier_band, a_picks, e_picks, missing_role, top_n))
    console = Console()
    if not recs:
        console.print(
            "[yellow]No recommendations — aggregates may be empty for this patch.[/yellow]"
        )
        return
    table = Table(title=f"Draft picks for {missing_role} (patch {patch}, {tier_band})")
    table.add_column("Champion", style="cyan")
    table.add_column("Score", justify="right")
    table.add_column("vs Enemies", justify="right")
    table.add_column("Synergy", justify="right")
    table.add_column("Match Samples", justify="right")
    table.add_column("Syn Samples", justify="right")
    for r in recs:
        table.add_row(
            r.champion_name,
            f"{r.score * 100:+.2f}",
            f"{r.breakdown.vs_enemies_score * 100:+.2f}",
            f"{r.breakdown.synergy_score * 100:+.2f}",
            str(r.breakdown.matchup_samples),
            str(r.breakdown.synergy_samples),
        )
    console.print(table)


async def _run_draft(
    patch: str,
    tier_band: str,
    allies: list[PickedChampion],
    enemies: list[PickedChampion],
    missing_role: str,
    top_n: int,
) -> list[Recommendation]:
    async with session_scope() as session:
        return await recommend(
            session,
            patch=patch,
            tier_band=tier_band,
            allies=allies,
            enemies=enemies,
            missing_role=missing_role,
            top_n=top_n,
        )
