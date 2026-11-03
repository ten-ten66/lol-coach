import { ChampionIcon } from "@/components/champion-icon";
import { formatDuration, formatKda, queueLabel, roleLabel, timeAgo } from "@/lib/format";
import type { MatchSummary, SummonerStats } from "@/lib/types";
import { cn } from "@/lib/utils";

function MatchRow({ m }: { m: MatchSummary }) {
  return (
    <div
      className={cn(
        "flex items-center gap-3 rounded-lg border-l-4 bg-card p-3 ring-1 ring-foreground/10",
        m.win ? "border-l-blue-500" : "border-l-red-500",
      )}
    >
      <div className="w-14 shrink-0">
        <div className={cn("text-sm font-semibold", m.win ? "text-blue-400" : "text-red-400")}>
          {m.win ? "勝利" : "敗北"}
        </div>
        <div className="text-xs text-muted-foreground">{queueLabel(m.queue_id)}</div>
      </div>

      <ChampionIcon name={m.champion} size={44} />

      <div className="min-w-0 flex-1">
        <div className="flex items-center gap-2">
          <span className="truncate font-medium">{m.champion}</span>
          {roleLabel(m.role) && (
            <span className="text-xs text-muted-foreground">{roleLabel(m.role)}</span>
          )}
        </div>
        <div className="text-sm">
          <span className="font-medium">
            {m.kills} / <span className="text-red-400">{m.deaths}</span> / {m.assists}
          </span>
          <span className="ml-2 text-xs text-muted-foreground">
            KDA {formatKda(m.kills, m.deaths, m.assists)}
          </span>
        </div>
      </div>

      <div className="shrink-0 space-y-0.5 text-right text-xs text-muted-foreground">
        <div>CS {m.cs}</div>
        <div>{formatDuration(m.game_duration_sec)}</div>
        <div>{timeAgo(m.game_start_at)}</div>
      </div>
    </div>
  );
}

export function MatchList({ stats }: { stats: SummonerStats }) {
  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between px-1 text-sm text-muted-foreground">
        <span>直近 {stats.total_games} 試合</span>
        <span>
          {stats.total_wins}勝 {stats.total_games - stats.total_wins}敗 ・ 勝率{" "}
          {(stats.win_rate * 100).toFixed(0)}%
        </span>
      </div>
      {stats.matches.map((m) => (
        <MatchRow key={m.match_id} m={m} />
      ))}
    </div>
  );
}
