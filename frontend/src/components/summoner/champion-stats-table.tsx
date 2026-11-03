import { ChampionIcon } from "@/components/champion-icon";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { pct, winRateColorClass } from "@/lib/format";
import type { ChampionAgg } from "@/lib/types";
import { cn } from "@/lib/utils";

export function ChampionStatsTable({ champions }: { champions: ChampionAgg[] }) {
  const top = champions.slice(0, 10);
  return (
    <Card size="sm">
      <CardHeader>
        <CardTitle>チャンピオン別成績</CardTitle>
      </CardHeader>
      <CardContent className="px-0">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead className="pl-4">チャンピオン</TableHead>
              <TableHead className="text-right">勝率</TableHead>
              <TableHead className="text-right">KDA</TableHead>
              <TableHead className="pr-4 text-right">CS</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {top.map((c) => (
              <TableRow key={c.champion}>
                <TableCell className="pl-4">
                  <div className="flex items-center gap-2">
                    <ChampionIcon name={c.champion} size={28} />
                    <div className="min-w-0">
                      <div className="truncate font-medium">{c.champion}</div>
                      <div className="text-xs text-muted-foreground">
                        {c.games}戦 {c.wins}勝{c.games - c.wins}敗
                      </div>
                    </div>
                  </div>
                </TableCell>
                <TableCell
                  className={cn("text-right font-medium", winRateColorClass(c.win_rate))}
                >
                  {pct(c.win_rate, 0)}
                </TableCell>
                <TableCell className="text-right">{c.kda.toFixed(2)}</TableCell>
                <TableCell className="pr-4 text-right text-muted-foreground">
                  {c.avg_cs.toFixed(1)}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  );
}
