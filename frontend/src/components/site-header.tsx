import Link from "next/link";

import { SearchBar } from "@/components/search-bar";

export function SiteHeader() {
  return (
    <header className="sticky top-0 z-40 border-b border-border bg-background/80 backdrop-blur">
      <div className="mx-auto flex h-14 max-w-5xl items-center gap-4 px-4">
        <Link href="/" className="font-heading text-lg font-bold tracking-tight">
          LoL<span className="text-sky-400">Stats</span>
        </Link>
        <nav className="hidden items-center gap-0.5 text-sm sm:flex">
          {[
            { href: "/champions", label: "チャンピオン" },
            { href: "/tier", label: "Tier表" },
            { href: "/draft", label: "ドラフト" },
            { href: "/leaderboard", label: "ランキング" },
          ].map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className="rounded-md px-2 py-1 text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
            >
              {item.label}
            </Link>
          ))}
        </nav>
        <div className="ml-auto w-full max-w-xs">
          <SearchBar />
        </div>
      </div>
    </header>
  );
}
