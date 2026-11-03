"use client";

import Image from "next/image";
import { useState } from "react";

import { useDDragonVersion } from "@/hooks/use-ddragon-version";
import { championIconUrl } from "@/lib/ddragon";
import { cn } from "@/lib/utils";

export function ChampionIcon({
  name,
  size = 40,
  className,
}: {
  name: string;
  size?: number;
  className?: string;
}) {
  const { data: version } = useDDragonVersion();
  const [errored, setErrored] = useState(false);

  return (
    <div
      className={cn("relative shrink-0 overflow-hidden rounded-md bg-muted", className)}
      style={{ width: size, height: size }}
      title={name}
    >
      {version && !errored && (
        <Image
          src={championIconUrl(version, name)}
          alt={name}
          width={size}
          height={size}
          unoptimized
          onError={() => setErrored(true)}
          className="h-full w-full object-cover"
        />
      )}
    </div>
  );
}
