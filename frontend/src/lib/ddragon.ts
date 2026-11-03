// Data Dragon static asset helpers. No API key required — these are public CDN URLs.

const DDRAGON = "https://ddragon.leagueoflegends.com";

// A few match-v5 `championName` values differ from the Data Dragon image id.
const CHAMPION_NAME_FIX: Record<string, string> = {
  FiddleSticks: "Fiddlesticks",
  Wukong: "MonkeyKing",
};

export function normalizeChampionName(name: string): string {
  return CHAMPION_NAME_FIX[name] ?? name;
}

export async function fetchLatestVersion(): Promise<string> {
  const res = await fetch(`${DDRAGON}/api/versions.json`);
  if (!res.ok) throw new Error("Data Dragon のバージョン取得に失敗しました");
  const versions: string[] = await res.json();
  return versions[0] ?? "15.1.1";
}

export function championIconUrl(version: string, championName: string): string {
  return `${DDRAGON}/cdn/${version}/img/champion/${normalizeChampionName(championName)}.png`;
}

export function profileIconUrl(version: string, iconId: number): string {
  return `${DDRAGON}/cdn/${version}/img/profileicon/${iconId}.png`;
}

export function itemIconUrl(version: string, itemId: number): string {
  return `${DDRAGON}/cdn/${version}/img/item/${itemId}.png`;
}

export function spellIconUrl(version: string, imageFull: string): string {
  return `${DDRAGON}/cdn/${version}/img/spell/${imageFull}`;
}

export function passiveIconUrl(version: string, imageFull: string): string {
  return `${DDRAGON}/cdn/${version}/img/passive/${imageFull}`;
}

// Splash / loading art live under a version-less path.
export function championSplashUrl(id: string, skinNum = 0): string {
  return `${DDRAGON}/cdn/img/champion/splash/${id}_${skinNum}.jpg`;
}

export function championLoadingUrl(id: string, skinNum = 0): string {
  return `${DDRAGON}/cdn/img/champion/loading/${id}_${skinNum}.jpg`;
}

// ---- Champion static data (key-free) ------------------------------------

export interface DDragonChampionSummary {
  id: string; // "Aatrox" (image / route id)
  key: string; // numeric id as string, e.g. "266"
  name: string;
  title: string;
  blurb: string;
  tags: string[]; // ["Fighter", "Tank"]
  info: { attack: number; defense: number; magic: number; difficulty: number };
}

export interface DDragonSpell {
  id: string;
  name: string;
  description: string;
  cooldownBurn: string;
  costBurn: string;
  image: { full: string };
}

export interface DDragonPassive {
  name: string;
  description: string;
  image: { full: string };
}

export interface DDragonSkin {
  id: string;
  num: number;
  name: string;
}

export interface DDragonChampionFull {
  id: string;
  key: string;
  name: string;
  title: string;
  lore: string;
  blurb: string;
  tags: string[];
  allytips: string[];
  enemytips: string[];
  partype: string;
  info: { attack: number; defense: number; magic: number; difficulty: number };
  stats: Record<string, number>;
  spells: DDragonSpell[];
  passive: DDragonPassive;
  skins: DDragonSkin[];
}

export async function fetchChampionList(
  version: string,
): Promise<DDragonChampionSummary[]> {
  const res = await fetch(`${DDRAGON}/cdn/${version}/data/ja_JP/champion.json`);
  if (!res.ok) throw new Error("チャンピオン一覧の取得に失敗しました");
  const json = await res.json();
  const values = Object.values(json.data ?? {}) as DDragonChampionSummary[];
  return values.sort((a, b) => a.name.localeCompare(b.name, "ja"));
}

export async function fetchChampionDetail(
  version: string,
  id: string,
): Promise<DDragonChampionFull> {
  const res = await fetch(`${DDRAGON}/cdn/${version}/data/ja_JP/champion/${id}.json`);
  if (!res.ok) throw new Error(`チャンピオン「${id}」が見つかりませんでした`);
  const json = await res.json();
  const first = Object.values(json.data ?? {})[0];
  if (!first) throw new Error(`チャンピオン「${id}」が見つかりませんでした`);
  return first as DDragonChampionFull;
}
