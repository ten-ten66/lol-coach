import { ApiError } from "./api";

/** Human-friendly Japanese message for an API/network error. */
export function apiErrorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    if (error.status === 404) return "見つかりませんでした。入力内容を確認してください。";
    if (error.status === 401 || error.status === 403)
      return "Riot API キーが無効または失効しています。/opt/lol-coach/.env の RIOT_API_KEY を更新してください（開発キーは24時間で失効します）。";
    if (error.status === 429)
      return "レート制限に達しました。少し待ってから再試行してください。";
    if (error.status === 0) return error.message;
    return `エラーが発生しました（${error.status}）: ${error.message}`;
  }
  return "予期しないエラーが発生しました。";
}
