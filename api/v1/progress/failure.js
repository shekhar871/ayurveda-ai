export default function handler(req, res) {
  res.setHeader("Access-Control-Allow-Origin", "*");
  res.setHeader("Access-Control-Allow-Methods", "POST, OPTIONS");
  res.setHeader("Access-Control-Allow-Headers", "Content-Type");

  if (req.method === "OPTIONS") return res.status(204).end();
  if (req.method !== "POST") return res.status(405).json({ detail: "Method not allowed" });

  const body = typeof req.body === "string" ? JSON.parse(req.body || "{}") : req.body || {};
  const started = performance.now();
  res.status(200).json({
    elapsed_ms: Math.round(performance.now() - started),
    alternative_formulation: "Triphala Kashaya",
    reason: `Alternative pathway for ${body.observed_imbalance || "condition"} when ${body.current_protocol_id || "protocol"} is insufficient.`,
    graph_path: "condition → alternative → citation",
  });
}
