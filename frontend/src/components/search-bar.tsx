"use client";

import { Search } from "lucide-react";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { DEFAULT_REGION, REGIONS, defaultTagForRegion } from "@/lib/regions";
import { cn } from "@/lib/utils";

export function SearchBar({
  size = "default",
  initialRegion = DEFAULT_REGION,
  autoFocus = false,
}: {
  size?: "default" | "lg";
  initialRegion?: string;
  autoFocus?: boolean;
}) {
  const router = useRouter();
  const [region, setRegion] = useState(initialRegion);
  const [value, setValue] = useState("");
  const lg = size === "lg";

  function submit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const raw = value.trim();
    if (!raw) return;

    let name = raw;
    let tag = defaultTagForRegion(region);
    const hashIdx = raw.lastIndexOf("#");
    if (hashIdx >= 0) {
      name = raw.slice(0, hashIdx).trim();
      tag = raw.slice(hashIdx + 1).trim();
    }
    if (!name || !tag) return;

    router.push(
      `/summoner/${region}/${encodeURIComponent(name)}/${encodeURIComponent(tag)}`,
    );
  }

  return (
    <form onSubmit={submit} className="flex items-stretch gap-2">
      <select
        aria-label="リージョン"
        value={region}
        onChange={(e) => setRegion(e.target.value)}
        className={cn(
          "rounded-lg border border-input bg-background px-2 text-sm text-foreground outline-none focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50",
          lg ? "h-11" : "h-9",
        )}
      >
        {REGIONS.map((r) => (
          <option key={r.platform} value={r.platform}>
            {r.label}
          </option>
        ))}
      </select>
      <Input
        autoFocus={autoFocus}
        value={value}
        onChange={(e) => setValue(e.target.value)}
        placeholder="プレイヤー名#JP1"
        className={cn("flex-1", lg && "h-11 text-base")}
      />
      <Button
        type="submit"
        size={lg ? "lg" : "icon"}
        aria-label="検索"
        className={cn(lg && "h-11 px-4")}
      >
        <Search />
        {lg && <span>検索</span>}
      </Button>
    </form>
  );
}
