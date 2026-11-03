import type { Metadata } from "next";

import { SummonerView } from "@/components/summoner/summoner-view";

type Params = Promise<{ region: string; name: string; tag: string }>;

export async function generateMetadata({
  params,
}: {
  params: Params;
}): Promise<Metadata> {
  const { name, tag } = await params;
  return {
    title: `${decodeURIComponent(name)}#${decodeURIComponent(tag)} — LoL Stats`,
  };
}

export default async function SummonerPage({ params }: { params: Params }) {
  const { region, name, tag } = await params;
  return (
    <SummonerView
      platform={region}
      name={decodeURIComponent(name)}
      tag={decodeURIComponent(tag)}
    />
  );
}
