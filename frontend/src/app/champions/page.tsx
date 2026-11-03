import type { Metadata } from "next";

import { ChampionBrowser } from "@/components/champions/champion-browser";

export const metadata: Metadata = {
  title: "チャンピオン一覧 — LoL Stats",
};

export default function ChampionsPage() {
  return <ChampionBrowser />;
}
