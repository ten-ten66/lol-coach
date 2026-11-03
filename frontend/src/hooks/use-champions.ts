"use client";

import { useQuery } from "@tanstack/react-query";

import { useDDragonVersion } from "@/hooks/use-ddragon-version";
import { fetchChampionDetail, fetchChampionList } from "@/lib/ddragon";

const ONE_DAY = 1000 * 60 * 60 * 24;

export function useChampionList() {
  const { data: version } = useDDragonVersion();
  return useQuery({
    queryKey: ["champion-list", version],
    queryFn: () => fetchChampionList(version as string),
    enabled: Boolean(version),
    staleTime: ONE_DAY,
    gcTime: ONE_DAY,
  });
}

export function useChampionDetail(id: string) {
  const { data: version } = useDDragonVersion();
  return useQuery({
    queryKey: ["champion-detail", version, id],
    queryFn: () => fetchChampionDetail(version as string, id),
    enabled: Boolean(version) && Boolean(id),
    staleTime: ONE_DAY,
    gcTime: ONE_DAY,
  });
}
