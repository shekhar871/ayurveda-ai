const feedback = globalThis.__ayurFeedback || (globalThis.__ayurFeedback = []);

export default function handler(req, res) {
  res.setHeader("Access-Control-Allow-Origin", "*");
  res.setHeader("Access-Control-Allow-Methods", "POST, OPTIONS");
  res.setHeader("Access-Control-Allow-Headers", "Content-Type");

  if (req.method === "OPTIONS") return res.status(204).end();
  if (req.method !== "POST") return res.status(405).json({ detail: "Method not allowed" });

  const body = typeof req.body === "string" ? JSON.parse(req.body || "{}") : req.body || {};
  feedback.push(body);
  const delta = body.outcome === "helped" ? 0.2 : body.outcome === "no_effect" ? -0.1 : -0.3;
  res.status(200).json({ status: "recorded", efficacy_delta: delta });
}
