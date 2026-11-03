import type {
  Champion,
  ChampionStat,
  DraftMeta,
  DraftRequest,
  DraftResponse,
  Ladder,
  SummonerProfile,
  SummonerStats,
} from "./types";

const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE ?? "http://127.0.0.1:8000/api/v1";

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  let res: Response;
  try {
    res = await fetch(`${API_BASE}${path}`, {
      ...init,
      headers: { Accept: "application/json", ...(init?.headers ?? {}) },
    });
  } catch {
    throw new ApiError(0, "バックエンドに接続できません（起動していますか？）");
  }
  if (!res.ok) {
    let detail = res.statusText || `HTTP ${res.status}`;
    try {
      const body = await res.json();
      if (body?.detail) {
        detail =
          typeof body.detail === "string" ? body.detail : JSON.stringify(body.detail);
      }
    } catch {
      // non-JSON error body; keep statusText
    }
    throw new ApiError(res.status, detail);
  }
  return (await res.json()) as T;
}

function summonerPath(platform: string, name: string, tag: string): string {
  return `/summoner/${platform}/${encodeURIComponent(name)}/${encodeURIComponent(tag)}`;
}

export function getSummonerProfile(
  platform: string,
  name: string,
  tag: string,
): Promise<SummonerProfile> {
  return apiFetch<SummonerProfile>(`${summonerPath(platform, name, tag)}/profile`);
}

export function getSummonerRecent(
  platform: string,
  name: string,
  tag: string,
  opts: { count?: number; queue?: number } = {},
): Promise<SummonerStats> {
  const params = new URLSearchParams();
  if (opts.count != null) params.set("count", String(opts.count));
  if (opts.queue != null) params.set("queue", String(opts.queue));
  const qs = params.toString();
  return apiFetch<SummonerStats>(
    `${summonerPath(platform, name, tag)}/recent${qs ? `?${qs}` : ""}`,
  );
}

export function getChampions(): Promise<Champion[]> {
  return apiFetch<Champion[]>("/champions");
}

export function getChampionStats(
  opts: { role?: string; patch?: string; queue?: number; minGames?: number } = {},
): Promise<ChampionStat[]> {
  const params = new URLSearchParams();
  if (opts.role) params.set("role", opts.role);
  if (opts.patch) params.set("patch", opts.patch);
  if (opts.queue != null) params.set("queue", String(opts.queue));
  if (opts.minGames != null) params.set("min_games", String(opts.minGames));
  const qs = params.toString();
  return apiFetch<ChampionStat[]>(`/champions/stats${qs ? `?${qs}` : ""}`);
}

export function getDraftMeta(): Promise<DraftMeta> {
  return apiFetch<DraftMeta>("/draft/patches");
}

export function recommendDraft(req: DraftRequest): Promise<DraftResponse> {
  return apiFetch<DraftResponse>("/draft/recommend", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(req),
  });
}

export function getLeaderboard(
  platform: string,
  opts: { tier?: string; queue?: string; limit?: number } = {},
): Promise<Ladder> {
  const params = new URLSearchParams();
  if (opts.tier) params.set("tier", opts.tier);
  if (opts.queue) params.set("queue", opts.queue);
  if (opts.limit != null) params.set("limit", String(opts.limit));
  const qs = params.toString();
  return apiFetch<Ladder>(`/leaderboard/${platform}${qs ? `?${qs}` : ""}`);
}
