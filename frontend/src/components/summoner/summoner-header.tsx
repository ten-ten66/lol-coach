"use client";

import { AlertTriangle } from "lucide-react";
import Image from "next/image";
import { useState } from "react";

import { Badge } from "@/components/ui/badge";
import { useDDragonVersion } from "@/hooks/use-ddragon-version";
import { profileIconUrl } from "@/lib/ddragon";
import { regionLabel } from "@/lib/regions";
import type { SummonerProfile } from "@/lib/types";

export function SummonerHeader({
  platform,
  name,
  tag,
  profile,
  error,
}: {
  platform: string;
  name: string;
  tag: string;
  profile?: SummonerProfile;
  error?: string | null;
}) {
  const { data: version } = useDDragonVersion();
  const [iconError, setIconError] = useState(false);
  const iconId = profile?.profile_icon_id;

  return (
    <div className="flex items-center gap-4 rounded-xl bg-card p-4 ring-1 ring-foreground/10">
      <div className="relative size-20 shrink-0 overflow-hidden rounded-xl bg-muted">
        {version && iconId != null && !iconError && (
          <Image
            src={profileIconUrl(version, iconId)}
            alt=""
            width={80}
            height={80}
            unoptimized
            onError={() => setIconError(true)}
            className="h-full w-full object-cover"
          />
        )}
        {profile && (
          <span className="absolute inset-x-0 bottom-0 bg-black/60 py-0.5 text-center text-xs font-medium text-white">
            {profile.summoner_level}
          </span>
        )}
      </div>

      <div className="min-w-0 flex-1 space-y-1.5">
        <div className="flex flex-wrap items-baseline gap-x-2">
          <h1 className="text-2xl font-bold tracking-tight">{name}</h1>
          <span className="text-lg text-muted-foreground">#{tag}</span>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <Badge variant="outline">{regionLabel(platform)}</Badge>
          {profile && (
            <span className="text-xs text-muted-foreground">Lv. {profile.summoner_level}</span>
          )}
        </div>
        {error && (
          <p className="flex items-start gap-1.5 text-xs text-destructive">
            <AlertTriangle className="mt-0.5 size-3.5 shrink-0" />
            <span>{error}</span>
          </p>
        )}
      </div>
    </div>
  );
}
