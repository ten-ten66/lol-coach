"use client";

import { useQuery } from "@tanstack/react-query";
import { AlertTriangle } from "lucide-react";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { getLeaderboard } from "@/lib/api";
import { apiErrorMessage } from "@/lib/errors";
import { pct, tierColorClass } from "@/lib/format";
import { DEFAULT_REGION, REGIONS } from "@/lib/regions";
import { cn } from "@/lib/utils";

const TIERS = [
  { value: "challenger", label: "チャレンジャー" },
  { value: "grandmaster", label: "グランドマスター" },
  { value: "master", label: "マスター" },
];

export function Leaderboard() {
  const [tier, setTier] = useState("challenger");
  const [platform, setPlatform] = useState(DEFAULT_REGION);

  const q = useQuery({
    queryKey: ["leaderboard", platform, tier],
    queryFn: () => getLeaderboard(platform, { tier, limit: 50 }),
  });

  const lpColor = tierColorClass(tier.toUpperCase());

  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">ランキング</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          各リージョンの上位ランク（ソロ/デュオ）ラダー。
        </p>
      </div>

      <div className="flex flex-wrap items-end gap-3">
        <div className="flex flex-col gap-1 text-xs text-muted-foreground">
          ティア
          <div className="flex gap-1">
            {TIERS.map((t) => (
              <Button
                key={t.value}
                size="sm"
                variant={tier === t.value ? "secondary" : "ghost"}
                onClick={() => setTier(t.value)}
              >
                {t.label}
              </Button>
            ))}
          </div>
        </div>
        <label className="flex flex-col gap-1 text-xs text-muted-foreground">
          リージョン
          <select
            value={platform}
            onChange={(e) => setPlatform(e.target.value)}
            className="h-9 rounded-lg border border-input bg-background px-2 text-sm text-foreground"
          >
            {REGIONS.map((r) => (
              <option key={r.platform} value={r.platform}>
                {r.label}
              </option>
            ))}
          </select>
        </label>
      </div>

      {q.isLoading ? (
        <div className="space-y-2">
          {Array.from({ length: 12 }).map((_, i) => (
            <Skeleton key={i} className="h-11 w-full rounded-lg" />
          ))}
        </div>
      ) : q.isError ? (
        <Card className="ring-destructive/30">
          <CardContent className="flex items-start gap-3 py-5 text-sm">
            <AlertTriangle className="mt-0.5 size-5 shrink-0 text-destructive" />
            <p>{apiErrorMessage(q.error)}</p>
          </CardContent>
        </Card>
      ) : q.data && q.data.entries.length > 0 ? (
        <Card size="sm">
          <CardContent className="px-0">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-12 pl-4">#</TableHead>
                  <TableHead>サモナー</TableHead>
                  <TableHead className="text-right">LP</TableHead>
                  <TableHead className="text-right">勝/敗</TableHead>
                  <TableHead className="pr-4 text-right">勝率</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {q.data.entries.map((e) => (
                  <TableRow key={e.rank_position}>
                    <TableCell className="pl-4 font-medium text-muted-foreground">
                      {e.rank_position}
                    </TableCell>
                    <TableCell className="font-medium">
                      {e.game_name ? (
                        <>
                          {e.game_name}
                          <span className="text-muted-foreground">#{e.tag_line}</span>
                        </>
                      ) : (
                        <span className="text-muted-foreground">（名前未取得）</span>
                      )}
                    </TableCell>
                    <TableCell className="text-right">
                      <span className={cn("font-semibold", lpColor)}>
                        {e.league_points}
                      </span>{" "}
                      LP
                    </TableCell>
                    <TableCell className="text-right text-muted-foreground">
                      {e.wins}/{e.losses}
                    </TableCell>
                    <TableCell className="pr-4 text-right">{pct(e.win_rate, 0)}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      ) : (
        <Card>
          <CardContent className="py-10 text-center text-sm text-muted-foreground">
            データがありません。
          </CardContent>
        </Card>
      )}
    </div>
  );
}
