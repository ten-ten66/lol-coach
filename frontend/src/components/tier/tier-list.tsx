"use client";

import { useQuery } from "@tanstack/react-query";
import { AlertTriangle } from "lucide-react";
import { useMemo, useState } from "react";

import { ChampionIcon } from "@/components/champion-icon";
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
import { useChampionList } from "@/hooks/use-champions";
import { getChampionStats, getDraftMeta } from "@/lib/api";
import { pct, winRateColorClass } from "@/lib/format";
import { cn } from "@/lib/utils";

const ROLE_TABS = [
  { value: "", label: "全ロール" },
  { value: "TOP", label: "TOP" },
  { value: "JUNGLE", label: "JG" },
  { value: "MIDDLE", label: "MID" },
  { value: "BOTTOM", label: "BOT" },
  { value: "UTILITY", label: "SUP" },
];

const MIN_GAMES_OPTIONS = [1, 2, 3, 5];

function tierOf(wr: number): { label: string; cls: string } {
  if (wr >= 0.55) return { label: "S", cls: "bg-amber-400/20 text-amber-300" };
  if (wr >= 0.52) return { label: "A", cls: "bg-fuchsia-400/20 text-fuchsia-300" };
  if (wr >= 0.5) return { label: "B", cls: "bg-sky-400/20 text-sky-300" };
  if (wr >= 0.47) return { label: "C", cls: "bg-emerald-400/20 text-emerald-300" };
  return { label: "D", cls: "bg-muted text-muted-foreground" };
}

export function TierList() {
  const [role, setRole] = useState("");
  const [patch, setPatch] = useState("");
  const [minGames, setMinGames] = useState(3);

  const metaQ = useQuery({ queryKey: ["draft-meta"], queryFn: getDraftMeta });
  const patches = metaQ.data?.patches ?? [];
  const effectivePatch = patch || patches[0] || "";

  const { data: champions } = useChampionList();
  const byId = useMemo(() => {
    const m = new Map<number, { id: string; name: string }>();
    champions?.forEach((c) => m.set(Number(c.key), { id: c.id, name: c.name }));
    return m;
  }, [champions]);

  const statsQ = useQuery({
    queryKey: ["champion-stats", role, effectivePatch, minGames],
    queryFn: () =>
      getChampionStats({
        role: role || undefined,
        patch: effectivePatch || undefined,
        minGames,
      }),
    enabled: Boolean(effectivePatch),
  });

  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Tier 表</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          ローカルに蓄積した試合データから算出したチャンピオン勝率ランキングです。
        </p>
      </div>

      <div className="flex flex-wrap items-end gap-3">
        <div className="flex flex-col gap-1 text-xs text-muted-foreground">
          ロール
          <div className="flex flex-wrap gap-1">
            {ROLE_TABS.map((t) => (
              <Button
                key={t.value}
                size="sm"
                variant={role === t.value ? "secondary" : "ghost"}
                onClick={() => setRole(t.value)}
              >
                {t.label}
              </Button>
            ))}
          </div>
        </div>
        <label className="flex flex-col gap-1 text-xs text-muted-foreground">
          パッチ
          <select
            value={effectivePatch}
            onChange={(e) => setPatch(e.target.value)}
            className="h-9 rounded-lg border border-input bg-background px-2 text-sm text-foreground"
          >
            {patches.map((p) => (
              <option key={p} value={p}>
                {p}
              </option>
            ))}
          </select>
        </label>
        <label className="flex flex-col gap-1 text-xs text-muted-foreground">
          最小試合数
          <select
            value={minGames}
            onChange={(e) => setMinGames(Number(e.target.value))}
            className="h-9 rounded-lg border border-input bg-background px-2 text-sm text-foreground"
          >
            {MIN_GAMES_OPTIONS.map((n) => (
              <option key={n} value={n}>
                {n}
              </option>
            ))}
          </select>
        </label>
      </div>

      <p className="flex items-start gap-1.5 rounded-lg bg-muted/40 p-3 text-xs text-muted-foreground">
        <AlertTriangle className="mt-0.5 size-3.5 shrink-0" />
        <span>
          現在の試合データはサンプル数が少なく、勝率は統計的に不安定です（少数試合で勝率100%等が出ます）。
          <code>lol-coach ingest sample</code> でデータを増やすと精度が向上します。
        </span>
      </p>

      {statsQ.isLoading ? (
        <div className="space-y-2">
          {Array.from({ length: 10 }).map((_, i) => (
            <Skeleton key={i} className="h-12 w-full rounded-lg" />
          ))}
        </div>
      ) : statsQ.isError ? (
        <Card className="ring-destructive/30">
          <CardContent className="py-4 text-sm text-destructive">
            統計の取得に失敗しました。
          </CardContent>
        </Card>
      ) : statsQ.data && statsQ.data.length > 0 ? (
        <Card size="sm">
          <CardContent className="px-0">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-10 pl-4">#</TableHead>
                  <TableHead className="w-12">Tier</TableHead>
                  <TableHead>チャンピオン</TableHead>
                  <TableHead className="text-right">勝率</TableHead>
                  <TableHead className="text-right">試合</TableHead>
                  <TableHead className="pr-4 text-right">ピック率</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {statsQ.data.map((s, i) => {
                  const tier = tierOf(s.win_rate);
                  const info = byId.get(s.champion_id);
                  return (
                    <TableRow key={s.champion_id}>
                      <TableCell className="pl-4 text-muted-foreground">{i + 1}</TableCell>
                      <TableCell>
                        <span
                          className={cn(
                            "inline-flex h-6 w-6 items-center justify-center rounded text-xs font-bold",
                            tier.cls,
                          )}
                        >
                          {tier.label}
                        </span>
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center gap-2">
                          <ChampionIcon name={info?.id ?? s.champion_name} size={28} />
                          <span className="truncate font-medium">
                            {info?.name ?? s.champion_name}
                          </span>
                        </div>
                      </TableCell>
                      <TableCell
                        className={cn("text-right font-medium", winRateColorClass(s.win_rate))}
                      >
                        {pct(s.win_rate, 0)}
                      </TableCell>
                      <TableCell className="text-right text-muted-foreground">
                        {s.games}
                      </TableCell>
                      <TableCell className="pr-4 text-right text-muted-foreground">
                        {pct(s.pick_rate, 1)}
                      </TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      ) : (
        <Card>
          <CardContent className="py-10 text-center text-sm text-muted-foreground">
            条件に合うデータがありません（最小試合数を下げてみてください）。
          </CardContent>
        </Card>
      )}
    </div>
  );
}
