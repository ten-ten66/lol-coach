import type { Metadata } from "next";

import { Leaderboard } from "@/components/leaderboard/leaderboard";

export const metadata: Metadata = {
  title: "ランキング — LoL Stats",
};

export default function LeaderboardPage() {
  return <Leaderboard />;
}
