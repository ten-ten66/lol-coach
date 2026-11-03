"use client";

import { useQuery } from "@tanstack/react-query";

import { fetchLatestVersion } from "@/lib/ddragon";

const ONE_DAY = 1000 * 60 * 60 * 24;

export function useDDragonVersion() {
  return useQuery({
    queryKey: ["ddragon-version"],
    queryFn: fetchLatestVersion,
    staleTime: ONE_DAY,
    gcTime: ONE_DAY,
  });
}
