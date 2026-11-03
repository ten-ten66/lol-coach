export const CLASS_LABELS: Record<string, string> = {
  Fighter: "ファイター",
  Tank: "タンク",
  Mage: "メイジ",
  Assassin: "アサシン",
  Marksman: "マークスマン",
  Support: "サポート",
};

export const CLASS_ORDER = [
  "Fighter",
  "Tank",
  "Mage",
  "Assassin",
  "Marksman",
  "Support",
];

export function classLabel(tag: string): string {
  return CLASS_LABELS[tag] ?? tag;
}

export const SPELL_KEYS = ["Q", "W", "E", "R"];

export const STAT_FIELDS: { key: string; label: string; perLevelKey?: string }[] = [
  { key: "hp", label: "体力", perLevelKey: "hpperlevel" },
  { key: "mp", label: "マナ", perLevelKey: "mpperlevel" },
  { key: "attackdamage", label: "攻撃力", perLevelKey: "attackdamageperlevel" },
  { key: "armor", label: "物理防御", perLevelKey: "armorperlevel" },
  { key: "spellblock", label: "魔法防御", perLevelKey: "spellblockperlevel" },
  { key: "attackspeed", label: "攻撃速度" },
  { key: "movespeed", label: "移動速度" },
  { key: "attackrange", label: "射程" },
];
