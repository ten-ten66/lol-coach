import { BarChart3, Swords, Trophy, Users } from "lucide-react";
import Link from "next/link";

import { SearchBar } from "@/components/search-bar";

const NAV = [
  {
    href: "/champions",
    title: "チャンピオン",
    desc: "全チャンピオンの情報・スキル・ステータス",
    icon: Users,
  },
  { href: "/tier", title: "Tier 表", desc: "ロール別の勝率ランキング", icon: BarChart3 },
  {
    href: "/draft",
    title: "ドラフト相性",
    desc: "ピックに対するおすすめを統計から提示",
    icon: Swords,
  },
  {
    href: "/leaderboard",
    title: "ランキング",
    desc: "各リージョンの上位ラダー",
    icon: Trophy,
  },
];

export default function Home() {
  return (
    <div className="space-y-10 py-6">
      <div className="flex flex-col items-center gap-6 text-center">
        <div className="space-y-3">
          <h1 className="font-heading text-4xl font-bold tracking-tight sm:text-5xl">
            LoL<span className="text-sky-400">Stats</span>
          </h1>
          <p className="text-muted-foreground">
            Riot ID を入力して、サモナーの戦績・ランク・直近の試合を検索
          </p>
        </div>
        <div className="w-full max-w-xl">
          <SearchBar size="lg" autoFocus />
        </div>
        <p className="text-xs text-muted-foreground">
          例: <span className="font-mono">Hide on bush#KR1</span>
          （タグ省略時はリージョン既定タグ）
        </p>
      </div>

      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        {NAV.map((n) => {
          const Icon = n.icon;
          return (
            <Link
              key={n.href}
              href={n.href}
              className="group rounded-xl bg-card p-4 ring-1 ring-foreground/10 transition-colors hover:ring-sky-400/50"
            >
              <Icon className="size-6 text-sky-400" />
              <div className="mt-3 font-medium">{n.title}</div>
              <div className="mt-1 text-xs text-muted-foreground">{n.desc}</div>
            </Link>
          );
        })}
      </div>
    </div>
  );
}
