export function pct(n: number, digits = 1): string {
  return `${(n * 100).toFixed(digits)}%`;
}

// Strip HTML tags from Data Dragon descriptions/lore for safe plain-text rendering.
export function stripTags(html: string): string {
  if (!html) return "";
  return html
    .replace(/<br\s*\/?>/gi, " ")
    .replace(/<[^>]*>/g, "")
    .replace(/\s+/g, " ")
    .trim();
}

export function kdaRatio(kills: number, deaths: number, assists: number): number {
  return deaths === 0 ? kills + assists : (kills + assists) / deaths;
}

export function formatKda(kills: number, deaths: number, assists: number): string {
  return kdaRatio(kills, deaths, assists).toFixed(2);
}

export function formatDuration(sec: number): string {
  const m = Math.floor(sec / 60);
  const s = Math.abs(sec % 60);
  return `${m}:${String(s).padStart(2, "0")}`;
}

export function timeAgo(iso: string): string {
  const then = new Date(iso).getTime();
  if (Number.isNaN(then)) return "";
  const min = Math.floor((Date.now() - then) / 60000);
  if (min < 1) return "たった今";
  if (min < 60) return `${min}分前`;
  const hour = Math.floor(min / 60);
  if (hour < 24) return `${hour}時間前`;
  const day = Math.floor(hour / 24);
  if (day < 30) return `${day}日前`;
  const month = Math.floor(day / 30);
  if (month < 12) return `${month}ヶ月前`;
  return `${Math.floor(month / 12)}年前`;
}

const QUEUE_LABELS: Record<number, string> = {
  400: "ノーマル",
  420: "ランクソロ",
  430: "ノーマル",
  440: "ランクフレックス",
  450: "ARAM",
  490: "ノーマル",
  700: "Clash",
  720: "ARAM Clash",
  900: "URF",
  1700: "アリーナ",
  1900: "URF",
};

export function queueLabel(queueId: number): string {
  return QUEUE_LABELS[queueId] ?? "その他";
}

export const QUEUE_TYPE_LABELS: Record<string, string> = {
  RANKED_SOLO_5x5: "ソロ/デュオ",
  RANKED_FLEX_SR: "フレックス",
};

const ROLE_LABELS: Record<string, string> = {
  TOP: "TOP",
  JUNGLE: "JG",
  MIDDLE: "MID",
  BOTTOM: "BOT",
  UTILITY: "SUP",
};

export function roleLabel(role: string): string {
  return ROLE_LABELS[role] ?? "";
}

export const TIER_LABELS: Record<string, string> = {
  IRON: "アイアン",
  BRONZE: "ブロンズ",
  SILVER: "シルバー",
  GOLD: "ゴールド",
  PLATINUM: "プラチナ",
  EMERALD: "エメラルド",
  DIAMOND: "ダイヤモンド",
  MASTER: "マスター",
  GRANDMASTER: "グランドマスター",
  CHALLENGER: "チャレンジャー",
};

export function tierLabel(tier: string): string {
  return TIER_LABELS[tier?.toUpperCase?.()] ?? tier;
}

const TIER_COLORS: Record<string, string> = {
  IRON: "text-zinc-400",
  BRONZE: "text-amber-700",
  SILVER: "text-slate-300",
  GOLD: "text-yellow-400",
  PLATINUM: "text-teal-300",
  EMERALD: "text-emerald-400",
  DIAMOND: "text-sky-300",
  MASTER: "text-fuchsia-400",
  GRANDMASTER: "text-red-400",
  CHALLENGER: "text-amber-300",
};

export function tierColorClass(tier: string): string {
  return TIER_COLORS[tier?.toUpperCase?.()] ?? "text-muted-foreground";
}

export function winRateColorClass(wr: number): string {
  if (wr >= 0.6) return "text-amber-400";
  if (wr >= 0.5) return "text-blue-400";
  return "text-muted-foreground";
}
