export interface RegionOption {
  platform: string;
  label: string;
  defaultTag: string;
}

// Mirrors the backend's PLATFORM_TO_REGIONAL map (riot/regions.py).
export const REGIONS: RegionOption[] = [
  { platform: "jp1", label: "JP", defaultTag: "JP1" },
  { platform: "kr", label: "KR", defaultTag: "KR1" },
  { platform: "na1", label: "NA", defaultTag: "NA1" },
  { platform: "euw1", label: "EUW", defaultTag: "EUW" },
  { platform: "eun1", label: "EUNE", defaultTag: "EUNE" },
  { platform: "br1", label: "BR", defaultTag: "BR1" },
  { platform: "la1", label: "LAN", defaultTag: "LA1" },
  { platform: "la2", label: "LAS", defaultTag: "LA2" },
  { platform: "oc1", label: "OCE", defaultTag: "OC1" },
  { platform: "tr1", label: "TR", defaultTag: "TR1" },
  { platform: "ru", label: "RU", defaultTag: "RU" },
  { platform: "sg2", label: "SG", defaultTag: "SG2" },
  { platform: "ph2", label: "PH", defaultTag: "PH2" },
  { platform: "th2", label: "TH", defaultTag: "TH2" },
  { platform: "tw2", label: "TW", defaultTag: "TW2" },
  { platform: "vn2", label: "VN", defaultTag: "VN2" },
  { platform: "me1", label: "ME", defaultTag: "ME1" },
];

export const DEFAULT_REGION = "jp1";

export function regionLabel(platform: string): string {
  return REGIONS.find((r) => r.platform === platform)?.label ?? platform.toUpperCase();
}

export function defaultTagForRegion(platform: string): string {
  return (
    REGIONS.find((r) => r.platform === platform)?.defaultTag ?? platform.toUpperCase()
  );
}
