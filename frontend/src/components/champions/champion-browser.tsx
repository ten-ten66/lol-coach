"use client";

import { AlertTriangle } from "lucide-react";
import Link from "next/link";
import { useMemo, useState } from "react";

import { ChampionIcon } from "@/components/champion-icon";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { useChampionList } from "@/hooks/use-champions";
import { CLASS_ORDER, classLabel } from "@/lib/champion-meta";

export function ChampionBrowser() {
  const { data, isLoading, isError } = useChampionList();
  const [query, setQuery] = useState("");
  const [tag, setTag] = useState<string | null>(null);

  const filtered = useMemo(() => {
    if (!data) return [];
    const needle = query.trim().toLowerCase();
    return data.filter((c) => {
      if (tag && !c.tags.includes(tag)) return false;
      if (!needle) return true;
      return (
        c.name.toLowerCase().includes(needle) || c.id.toLowerCase().includes(needle)
      );
    });
  }, [data, query, tag]);

  return (
    <div className="space-y-5">
      <div className="space-y-3">
        <h1 className="text-2xl font-bold tracking-tight">チャンピオン</h1>
        <Input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="チャンピオン名で検索…"
          className="max-w-sm"
        />
        <div className="flex flex-wrap gap-1.5">
          <Button
            size="sm"
            variant={tag === null ? "secondary" : "ghost"}
            onClick={() => setTag(null)}
          >
            全て
          </Button>
          {CLASS_ORDER.map((t) => (
            <Button
              key={t}
              size="sm"
              variant={tag === t ? "secondary" : "ghost"}
              onClick={() => setTag(t)}
            >
              {classLabel(t)}
            </Button>
          ))}
        </div>
      </div>

      {isLoading ? (
        <div className="grid grid-cols-3 gap-3 sm:grid-cols-4 md:grid-cols-6 lg:grid-cols-8">
          {Array.from({ length: 24 }).map((_, i) => (
            <Skeleton key={i} className="aspect-square w-full rounded-md" />
          ))}
        </div>
      ) : isError ? (
        <Card className="ring-destructive/30">
          <CardContent className="flex items-center gap-2 py-5 text-sm">
            <AlertTriangle className="size-5 text-destructive" />
            チャンピオンデータの取得に失敗しました。
          </CardContent>
        </Card>
      ) : (
        <>
          <p className="text-sm text-muted-foreground">{filtered.length} 体</p>
          <div className="grid grid-cols-3 gap-3 sm:grid-cols-4 md:grid-cols-6 lg:grid-cols-8">
            {filtered.map((c) => (
              <Link
                key={c.id}
                href={`/champions/${c.id}`}
                className="group flex flex-col items-center gap-1.5"
              >
                <ChampionIcon
                  name={c.id}
                  size={64}
                  className="transition-transform group-hover:scale-105 group-hover:ring-2 group-hover:ring-sky-400"
                />
                <span className="w-full truncate text-center text-xs font-medium">
                  {c.name}
                </span>
              </Link>
            ))}
          </div>
        </>
      )}
    </div>
  );
}
