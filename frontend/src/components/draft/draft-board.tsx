"use client";

import { useMutation, useQuery } from "@tanstack/react-query";
import { Plus, X } from "lucide-react";
import { useMemo, useState } from "react";

import { ChampionIcon } from "@/components/champion-icon";
import { ChampionPicker } from "@/components/champions/champion-picker";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useChampionList } from "@/hooks/use-champions";
import { getDraftMeta, recommendDraft } from "@/lib/api";
import { roleLabel } from "@/lib/format";
import type { DraftPick, DraftResponse } from "@/lib/types";
import { cn } from "@/lib/utils";

const ROLES = ["TOP", "JUNGLE", "MIDDLE", "BOTTOM", "UTILITY"] as const;
type Role = (typeof ROLES)[number];
type Side = "ally" | "enemy";
type Board = Record<Side, Record<Role, number | null>>;

type ChampInfo = { id: string; name: string };

function emptyBoard(): Board {
  const empty = { TOP: null, JUNGLE: null, MIDDLE: null, BOTTOM: null, UTILITY: null };
  return { ally: { ...empty }, enemy: { ...empty } };
}

function Recommendations({
  data,
  byId,
}: {
  data: DraftResponse;
  byId: Map<number, ChampInfo>;
}) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>
          {roleLabel(data.missing_role)} おすすめ Top {data.recommendations.length}
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-2">
        {data.recommendations.map((r, i) => {
          const c = byId.get(r.champion_id);
          return (
            <div
              key={r.champion_id}
              className="flex items-center gap-3 rounded-lg bg-muted/40 p-2"
            >
              <span className="w-5 text-center text-sm font-bold text-muted-foreground">
                {i + 1}
              </span>
              <ChampionIcon name={c?.id ?? r.champion_name} size={36} />
              <span className="flex-1 truncate text-sm font-medium">
                {c?.name ?? r.champion_name}
              </span>
              <div className="text-right text-xs text-muted-foreground">
                <div className="text-sm font-semibold text-foreground">
                  {(r.score * 100).toFixed(2)}
                </div>
                <div>
                  対面 {(r.vs_enemies_score * 100).toFixed(1)} / シナジー{" "}
                  {(r.synergy_score * 100).toFixed(1)}
                </div>
                <div>サンプル {r.matchup_samples + r.synergy_samples}</div>
              </div>
            </div>
          );
        })}
      </CardContent>
    </Card>
  );
}

export function DraftBoard() {
  const { data: champions } = useChampionList();
  const metaQ = useQuery({ queryKey: ["draft-meta"], queryFn: getDraftMeta });
  const [board, setBoard] = useState<Board>(emptyBoard);
  const [targetRole, setTargetRole] = useState<Role>("MIDDLE");
  const [patch, setPatch] = useState("");
  const [tierBand, setTierBand] = useState("");
  const [picker, setPicker] = useState<{ side: Side; role: Role } | null>(null);

  const patches = metaQ.data?.patches ?? [];
  const bands = metaQ.data?.tier_bands ?? ["ALL"];
  const effectivePatch = patch || patches[0] || "";
  const effectiveBand = tierBand || bands[0] || "ALL";

  const byId = useMemo(() => {
    const m = new Map<number, ChampInfo>();
    champions?.forEach((c) => m.set(Number(c.key), { id: c.id, name: c.name }));
    return m;
  }, [champions]);

  const recommendM = useMutation({
    mutationFn: () => {
      const allies: DraftPick[] = ROLES.flatMap((r) => {
        const id = board.ally[r];
        return r !== targetRole && id != null ? [{ champion_id: id, role: r }] : [];
      });
      const enemies: DraftPick[] = ROLES.flatMap((r) => {
        const id = board.enemy[r];
        return id != null ? [{ champion_id: id, role: r }] : [];
      });
      return recommendDraft({
        patch: effectivePatch,
        tier_band: effectiveBand,
        allies,
        enemies,
        missing_role: targetRole,
        top_n: 5,
      });
    },
  });

  function setSlot(side: Side, role: Role, id: number | null) {
    setBoard((b) => ({ ...b, [side]: { ...b[side], [role]: id } }));
  }

  function renderSlot(side: Side, role: Role) {
    const id = board[side][role];
    const champ = id != null ? byId.get(id) : undefined;
    const isTarget = side === "ally" && role === targetRole;
    return (
      <div key={role} className="flex items-center gap-2">
        <span className="w-9 shrink-0 text-xs font-medium text-muted-foreground">
          {roleLabel(role)}
        </span>
        <button
          onClick={() => setPicker({ side, role })}
          className={cn(
            "flex h-12 flex-1 items-center gap-2 rounded-lg border border-dashed border-border px-2 text-left transition-colors hover:border-foreground/40",
            isTarget && "border-solid border-sky-500 bg-sky-500/10",
          )}
        >
          {champ ? (
            <>
              <ChampionIcon name={champ.id} size={36} />
              <span className="truncate text-sm">{champ.name}</span>
            </>
          ) : (
            <span className="flex items-center gap-1 text-sm text-muted-foreground">
              <Plus className="size-4" /> {isTarget ? "推薦対象" : "選択"}
            </span>
          )}
        </button>
        {champ && (
          <button
            onClick={() => setSlot(side, role, null)}
            aria-label="クリア"
            className="rounded-md p-1 text-muted-foreground hover:bg-muted hover:text-foreground"
          >
            <X className="size-4" />
          </button>
        )}
      </div>
    );
  }

  const allZero =
    recommendM.data?.recommendations.every(
      (r) => r.matchup_samples + r.synergy_samples === 0,
    ) ?? false;

  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">ドラフト相性ツール</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          味方・敵のピックを入力し、空けたロールのおすすめチャンピオンを統計から提示します。
        </p>
      </div>

      <div className="flex flex-wrap items-end gap-3">
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
          ティア
          <select
            value={effectiveBand}
            onChange={(e) => setTierBand(e.target.value)}
            className="h-9 rounded-lg border border-input bg-background px-2 text-sm text-foreground"
          >
            {bands.map((b) => (
              <option key={b} value={b}>
                {b}
              </option>
            ))}
          </select>
        </label>
        <div className="flex flex-col gap-1 text-xs text-muted-foreground">
          推薦するロール
          <div className="flex gap-1">
            {ROLES.map((r) => (
              <Button
                key={r}
                size="sm"
                variant={targetRole === r ? "secondary" : "ghost"}
                onClick={() => setTargetRole(r)}
              >
                {roleLabel(r)}
              </Button>
            ))}
          </div>
        </div>
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="text-blue-400">味方</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            {ROLES.map((r) => renderSlot("ally", r))}
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle className="text-red-400">敵</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            {ROLES.map((r) => renderSlot("enemy", r))}
          </CardContent>
        </Card>
      </div>

      <Button
        onClick={() => recommendM.mutate()}
        disabled={!effectivePatch || recommendM.isPending}
        size="lg"
      >
        {recommendM.isPending
          ? "計算中…"
          : `${roleLabel(targetRole)} のおすすめを見る`}
      </Button>

      {recommendM.isError && (
        <Card className="ring-destructive/30">
          <CardContent className="py-4 text-sm text-destructive">
            推薦の取得に失敗しました。バックエンドが起動しているか確認してください。
          </CardContent>
        </Card>
      )}

      {recommendM.data && <Recommendations data={recommendM.data} byId={byId} />}

      {recommendM.data && allZero && (
        <p className="text-xs text-muted-foreground">
          ※ 現在のサンプルデータでは対面/シナジーの統計が乏しく、スコアが 0
          になる組み合わせが多くあります。<code>lol-coach ingest sample</code>{" "}
          で試合データを増やすと精度が上がります。
        </p>
      )}

      <ChampionPicker
        open={picker !== null}
        onClose={() => setPicker(null)}
        onSelect={(id) => {
          if (picker) setSlot(picker.side, picker.role, id);
        }}
      />
    </div>
  );
}
