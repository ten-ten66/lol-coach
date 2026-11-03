"use client";

import { AlertTriangle, ChevronLeft } from "lucide-react";
import Image from "next/image";
import Link from "next/link";

import { ChampionIcon } from "@/components/champion-icon";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { useChampionDetail } from "@/hooks/use-champions";
import { useDDragonVersion } from "@/hooks/use-ddragon-version";
import { SPELL_KEYS, STAT_FIELDS, classLabel } from "@/lib/champion-meta";
import {
  type DDragonChampionFull,
  championSplashUrl,
  passiveIconUrl,
  spellIconUrl,
} from "@/lib/ddragon";
import { stripTags } from "@/lib/format";

function round(n: number): number {
  return Math.round(n * 100) / 100;
}

function Abilities({ champ, version }: { champ: DDragonChampionFull; version: string }) {
  const items = [
    {
      slot: "P",
      name: champ.passive.name,
      desc: champ.passive.description,
      icon: passiveIconUrl(version, champ.passive.image.full),
      cd: "",
    },
    ...champ.spells.map((s, i) => ({
      slot: SPELL_KEYS[i] ?? "",
      name: s.name,
      desc: s.description,
      icon: spellIconUrl(version, s.image.full),
      cd: s.cooldownBurn,
    })),
  ];

  return (
    <Card>
      <CardHeader>
        <CardTitle>スキル</CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        {items.map((it) => (
          <div key={it.slot} className="flex gap-3">
            <div className="relative size-12 shrink-0 overflow-hidden rounded-md bg-muted">
              <Image
                src={it.icon}
                alt={it.name}
                width={48}
                height={48}
                unoptimized
                className="h-full w-full object-cover"
              />
              <span className="absolute right-0 bottom-0 rounded-tl bg-black/70 px-1 text-[10px] font-bold text-white">
                {it.slot}
              </span>
            </div>
            <div className="min-w-0">
              <div className="flex items-baseline gap-2">
                <span className="font-medium">{it.name}</span>
                {it.cd && <span className="text-xs text-muted-foreground">CD {it.cd}s</span>}
              </div>
              <p className="text-sm text-muted-foreground">{stripTags(it.desc)}</p>
            </div>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}

export function ChampionDetail({ championKey }: { championKey: string }) {
  const { data: version } = useDDragonVersion();
  const { data: champ, isLoading, isError, error } = useChampionDetail(championKey);

  if (isError) {
    return (
      <Card className="ring-destructive/30">
        <CardContent className="flex items-center gap-2 py-6 text-sm">
          <AlertTriangle className="size-5 text-destructive" />
          {error instanceof Error
            ? error.message
            : `チャンピオン「${championKey}」が見つかりませんでした。`}
        </CardContent>
      </Card>
    );
  }

  if (isLoading || !champ || !version) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-44 w-full rounded-xl" />
        <div className="grid gap-4 md:grid-cols-[1fr_320px]">
          <Skeleton className="h-72 rounded-xl" />
          <Skeleton className="h-72 rounded-xl" />
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-5">
      <Link
        href="/champions"
        className="inline-flex items-center gap-1 text-sm text-muted-foreground transition-colors hover:text-foreground"
      >
        <ChevronLeft className="size-4" /> チャンピオン一覧
      </Link>

      <div className="relative overflow-hidden rounded-xl ring-1 ring-foreground/10">
        <div
          className="absolute inset-0 bg-cover bg-center opacity-30"
          style={{ backgroundImage: `url(${championSplashUrl(champ.id, 0)})` }}
        />
        <div className="absolute inset-0 bg-gradient-to-t from-background via-background/70 to-transparent" />
        <div className="relative flex items-end gap-4 p-5 pt-28">
          <ChampionIcon name={champ.id} size={88} className="ring-2 ring-background" />
          <div>
            <h1 className="text-3xl font-bold tracking-tight">{champ.name}</h1>
            <p className="text-muted-foreground">{champ.title}</p>
            <div className="mt-2 flex flex-wrap gap-1.5">
              {champ.tags.map((t) => (
                <Badge key={t} variant="secondary">
                  {classLabel(t)}
                </Badge>
              ))}
            </div>
          </div>
        </div>
      </div>

      <div className="grid gap-5 md:grid-cols-[1fr_320px]">
        <div className="space-y-5">
          <Abilities champ={champ} version={version} />

          <Card>
            <CardHeader>
              <CardTitle>ストーリー</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4 text-sm text-muted-foreground">
              <p className="leading-relaxed">{stripTags(champ.lore)}</p>
              {champ.allytips.length > 0 && (
                <div>
                  <div className="mb-1 font-medium text-foreground">使う側のヒント</div>
                  <ul className="list-disc space-y-1 pl-5">
                    {champ.allytips.map((t, i) => (
                      <li key={i}>{stripTags(t)}</li>
                    ))}
                  </ul>
                </div>
              )}
              {champ.enemytips.length > 0 && (
                <div>
                  <div className="mb-1 font-medium text-foreground">対面のヒント</div>
                  <ul className="list-disc space-y-1 pl-5">
                    {champ.enemytips.map((t, i) => (
                      <li key={i}>{stripTags(t)}</li>
                    ))}
                  </ul>
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        <div className="space-y-5">
          <Card size="sm">
            <CardHeader>
              <CardTitle>基本ステータス</CardTitle>
            </CardHeader>
            <CardContent>
              <dl className="space-y-1.5 text-sm">
                {STAT_FIELDS.map((f) => {
                  const base = champ.stats[f.key];
                  if (base == null) return null;
                  const per = f.perLevelKey ? champ.stats[f.perLevelKey] : undefined;
                  return (
                    <div key={f.key} className="flex items-center justify-between">
                      <dt className="text-muted-foreground">{f.label}</dt>
                      <dd className="font-medium">
                        {round(base)}
                        {per ? (
                          <span className="ml-1 text-xs text-muted-foreground">
                            +{round(per)}/Lv
                          </span>
                        ) : null}
                      </dd>
                    </div>
                  );
                })}
              </dl>
            </CardContent>
          </Card>

          <Card size="sm">
            <CardContent className="py-4 text-xs text-muted-foreground">
              勝率・ピック率・バン率などの統計は、試合データ蓄積後（Phase 3）に表示予定です。
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
