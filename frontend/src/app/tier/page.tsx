import type { Metadata } from "next";

import { TierList } from "@/components/tier/tier-list";

export const metadata: Metadata = {
  title: "Tier 表 — LoL Stats",
};

export default function TierPage() {
  return <TierList />;
}
