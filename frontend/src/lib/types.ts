// Response shapes mirrored from the FastAPI backend (api/summoner.py, api/champions.py).

export interface ChampionAgg {
  champion: string;
  games: number;
  wins: number;
  win_rate: number;
  kda: number;
  avg_cs: number;
}

export interface MatchSummary {
  match_id: string;
  queue_id: number;
  game_start_at: string; // ISO 8601
  game_duration_sec: number;
  champion: string;
  role: string;
  win: boolean;
  kills: number;
  deaths: number;
  assists: number;
  cs: number;
}

export interface SummonerStats {
  game_name: string;
  tag_line: string;
  puuid: string;
  platform: string;
  total_games: number;
  total_wins: number;
  win_rate: number;
  by_champion: ChampionAgg[];
  matches: MatchSummary[];
}

export interface RankEntry {
  queue_type: string;
  tier: string;
  rank: string;
  league_points: number;
  wins: number;
  losses: number;
  win_rate: number;
}

export interface SummonerProfile {
  game_name: string;
  tag_line: string;
  puuid: string;
  platform: string;
  profile_icon_id: number;
  summoner_level: number;
  ranks: RankEntry[];
}

export interface Champion {
  id: number;
  key: string;
  name: string;
}

// ---- Champion stats (Tier list) ----

export interface ChampionStat {
  champion_id: number;
  champion_name: string;
  games: number;
  wins: number;
  win_rate: number;
  pick_rate: number;
}

// ---- Draft ----

export interface DraftPick {
  champion_id: number;
  role: string;
}

export interface DraftRequest {
  patch: string;
  tier_band: string;
  allies: DraftPick[];
  enemies: DraftPick[];
  missing_role: string;
  top_n: number;
}

export interface DraftRecommendation {
  champion_id: number;
  champion_name: string;
  score: number;
  vs_enemies_score: number;
  synergy_score: number;
  matchup_samples: number;
  synergy_samples: number;
}

export interface DraftResponse {
  patch: string;
  tier_band: string;
  missing_role: string;
  recommendations: DraftRecommendation[];
}

export interface DraftMeta {
  patches: string[];
  tier_bands: string[];
}

// ---- Leaderboard ----

export interface LadderEntry {
  rank_position: number;
  game_name: string | null;
  tag_line: string | null;
  league_points: number;
  wins: number;
  losses: number;
  win_rate: number;
}

export interface Ladder {
  platform: string;
  tier: string;
  queue: string;
  entries: LadderEntry[];
}
