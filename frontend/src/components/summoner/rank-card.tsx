import { Card, CardContent } from "@/components/ui/card";
import { QUEUE_TYPE_LABELS, pct, tierColorClass, tierLabel } from "@/lib/format";
import type { RankEntry } from "@/lib/types";
import { cn } from "@/lib/utils";

export function RankCard({ rank }: { rank: RankEntry }) {
  const total = rank.wins + rank.losses;
  return (
    <Card size="sm">
      <CardContent className="space-y-2">
        <div className="text-xs font-medium text-muted-foreground">
          {QUEUE_TYPE_LABELS[rank.queue_type] ?? rank.queue_type}
        </div>
        <div className="flex items-baseline justify-between gap-2">
          <span className={cn("text-lg font-bold", tierColorClass(rank.tier))}>
            {tierLabel(rank.tier)} {rank.rank}
          </span>
          <span className="text-sm text-muted-foreground">{rank.league_points} LP</span>
        </div>
        <div className="flex items-center justify-between text-xs text-muted-foreground">
          <span>
            {rank.wins}勝 {rank.losses}敗
          </span>
          <span>勝率 {total ? pct(rank.win_rate, 0) : "—"}</span>
        </div>
      </CardContent>
    </Card>
  );
}
