"use client";

import { useQuery } from "@tanstack/react-query";
import { AlertTriangle } from "lucide-react";
import { useState } from "react";

import { ChampionStatsTable } from "@/components/summoner/champion-stats-table";
import { MatchList } from "@/components/summoner/match-list";
import { RankCard } from "@/components/summoner/rank-card";
import { SummonerHeader } from "@/components/summoner/summoner-header";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { ApiError, getSummonerProfile, getSummonerRecent } from "@/lib/api";

const QUEUE_FILTERS = [
  { id: 0, label: "全て" },
  { id: 420, label: "ランクソロ" },
  { id: 440, label: "フレックス" },
  { id: 450, label: "ARAM" },
];

function errorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    if (error.status === 404)
      return "サモナーが見つかりませんでした。Riot ID とリージョンを確認してください。";
    if (error.status === 401 || error.status === 403)
      return "Riot API キーが無効または失効しています。/opt/lol-coach/.env の RIOT_API_KEY を更新してください（開発キーは24時間で失効します）。";
    if (error.status === 429)
      return "レート制限に達しました。少し待ってから再試行してください。";
    if (error.status === 0) return error.message;
    return `エラーが発生しました（${error.status}）: ${error.message}`;
  }
  return "予期しないエラーが発生しました。";
}

export function SummonerView({
  platform,
  name,
  tag,
}: {
  platform: string;
  name: string;
  tag: string;
}) {
  const [queue, setQueue] = useState(0);

  const profileQ = useQuery({
    queryKey: ["profile", platform, name, tag],
    queryFn: () => getSummonerProfile(platform, name, tag),
  });
  const recentQ = useQuery({
    queryKey: ["recent", platform, name, tag, queue],
    queryFn: () => getSummonerRecent(platform, name, tag, { count: 20, queue }),
  });

  return (
    <div className="space-y-5">
      <SummonerHeader
        platform={platform}
        name={name}
        tag={tag}
        profile={profileQ.data}
        error={profileQ.isError ? errorMessage(profileQ.error) : null}
      />

      <div className="grid gap-5 md:grid-cols-[300px_1fr]">
        <div className="space-y-4">
          {profileQ.isLoading ? (
            <Skeleton className="h-32 w-full rounded-xl" />
          ) : profileQ.data && profileQ.data.ranks.length > 0 ? (
            profileQ.data.ranks
              .slice()
              .sort((a, b) => a.queue_type.localeCompare(b.queue_type))
              .map((r) => <RankCard key={r.queue_type} rank={r} />)
          ) : profileQ.data ? (
            <Card>
              <CardContent className="py-6 text-center text-sm text-muted-foreground">
                ランク情報なし（アンランク）
              </CardContent>
            </Card>
          ) : null}

          {recentQ.data && recentQ.data.by_champion.length > 0 && (
            <ChampionStatsTable champions={recentQ.data.by_champion} />
          )}
        </div>

        <div className="space-y-4">
          <div className="flex flex-wrap items-center gap-1.5">
            {QUEUE_FILTERS.map((f) => (
              <Button
                key={f.id}
                size="sm"
                variant={queue === f.id ? "secondary" : "ghost"}
                onClick={() => setQueue(f.id)}
              >
                {f.label}
              </Button>
            ))}
          </div>

          {recentQ.isLoading ? (
            <div className="space-y-2">
              {Array.from({ length: 6 }).map((_, i) => (
                <Skeleton key={i} className="h-[68px] w-full rounded-lg" />
              ))}
            </div>
          ) : recentQ.isError ? (
            <Card className="ring-destructive/30">
              <CardContent className="flex items-start gap-3 py-5 text-sm">
                <AlertTriangle className="mt-0.5 size-5 shrink-0 text-destructive" />
                <p>{errorMessage(recentQ.error)}</p>
              </CardContent>
            </Card>
          ) : recentQ.data && recentQ.data.matches.length > 0 ? (
            <MatchList stats={recentQ.data} />
          ) : (
            <Card>
              <CardContent className="py-10 text-center text-sm text-muted-foreground">
                この条件の試合が見つかりませんでした。
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}
