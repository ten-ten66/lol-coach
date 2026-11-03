import type { Metadata } from "next";

import { ChampionDetail } from "@/components/champions/champion-detail";

type Params = Promise<{ key: string }>;

export async function generateMetadata({
  params,
}: {
  params: Params;
}): Promise<Metadata> {
  const { key } = await params;
  return { title: `${decodeURIComponent(key)} — チャンピオン — LoL Stats` };
}

export default async function ChampionDetailPage({ params }: { params: Params }) {
  const { key } = await params;
  return <ChampionDetail championKey={decodeURIComponent(key)} />;
}
