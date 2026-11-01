// kaitori-cron: goi GitHub Actions chay cap nhat gia dung gio (cron mien phi cua GitHub hay tre/bo luot)
// Can secret GH_TOKEN (fine-grained token, quyen Actions: Read and write cho repo kaitori-radar)
const REPO = "pdythanhduy/kaitori-radar";

async function dispatch(env, mode) {
  const r = await fetch("https://api.github.com/repos/" + REPO + "/actions/workflows/update.yml/dispatches", {
    method: "POST",
    headers: {
      Authorization: "Bearer " + env.GH_TOKEN,
      Accept: "application/vnd.github+json",
      "User-Agent": "kaitori-cron",
    },
    body: JSON.stringify({ ref: "main", inputs: { mode: mode } }),
  });
  return r.status;
}

export default {
  async scheduled(event, env, ctx) {
    const mode = event.cron === "47 1 * * *" ? "full" : "hot";
    const status = await dispatch(env, mode);
    console.log("cron", event.cron, mode, status);
  },
  async fetch(request, env) {
    return new Response("kaitori-cron ok (token: " + (env.GH_TOKEN ? "set" : "MISSING") + ")");
  },
};
