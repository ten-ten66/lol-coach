import type { Metadata } from "next";

import { DraftBoard } from "@/components/draft/draft-board";

export const metadata: Metadata = {
  title: "ドラフト相性ツール — LoL Stats",
};

export default function DraftPage() {
  return <DraftBoard />;
}
