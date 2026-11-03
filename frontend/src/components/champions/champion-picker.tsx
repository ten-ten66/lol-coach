"use client";

import { X } from "lucide-react";
import { useMemo, useState } from "react";

import { ChampionIcon } from "@/components/champion-icon";
import { Input } from "@/components/ui/input";
import { useChampionList } from "@/hooks/use-champions";

export function ChampionPicker({
  open,
  onClose,
  onSelect,
}: {
  open: boolean;
  onClose: () => void;
  onSelect: (championId: number, ddragonId: string) => void;
}) {
  const { data } = useChampionList();
  const [query, setQuery] = useState("");

  const filtered = useMemo(() => {
    if (!data) return [];
    const needle = query.trim().toLowerCase();
    if (!needle) return data;
    return data.filter(
      (c) =>
        c.name.toLowerCase().includes(needle) || c.id.toLowerCase().includes(needle),
    );
  }, [data, query]);

  if (!open) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-start justify-center bg-black/60 p-4 pt-16"
      onClick={onClose}
    >
      <div
        className="flex max-h-[70vh] w-full max-w-2xl flex-col overflow-hidden rounded-xl bg-card ring-1 ring-foreground/10"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center gap-2 border-b border-border p-3">
          {/* eslint-disable-next-line jsx-a11y/no-autofocus */}
          <Input
            autoFocus
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="チャンピオン名で検索…"
            className="flex-1"
          />
          <button
            onClick={onClose}
            aria-label="閉じる"
            className="rounded-md p-2 text-muted-foreground hover:bg-muted hover:text-foreground"
          >
            <X className="size-4" />
          </button>
        </div>
        <div className="grid grid-cols-4 gap-2 overflow-y-auto p-3 sm:grid-cols-6">
          {filtered.map((c) => (
            <button
              key={c.id}
              onClick={() => {
                onSelect(Number(c.key), c.id);
                onClose();
              }}
              className="flex flex-col items-center gap-1 rounded-md p-1 hover:bg-muted"
            >
              <ChampionIcon name={c.id} size={48} />
              <span className="w-full truncate text-center text-[11px]">{c.name}</span>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
