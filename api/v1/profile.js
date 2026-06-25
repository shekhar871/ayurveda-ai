const store = globalThis.__ayurProfiles || (globalThis.__ayurProfiles = {});

export default function handler(req, res) {
  res.setHeader("Access-Control-Allow-Origin", "*");
  res.setHeader("Access-Control-Allow-Methods", "POST, OPTIONS");
  res.setHeader("Access-Control-Allow-Headers", "Content-Type");

  if (req.method === "OPTIONS") return res.status(204).end();
  if (req.method !== "POST") return res.status(405).json({ detail: "Method not allowed" });

  const body = typeof req.body === "string" ? JSON.parse(req.body || "{}") : req.body || {};
  const uid = body.user_id || `user-${Date.now()}`;
  store[uid] = {
    prakriti: body.prakriti,
    vikriti: body.vikriti,
    allergies: body.allergies || [],
    contraindications: body.contraindications || [],
    active_protocol: body.active_protocol || {},
  };
  res.status(200).json({ user_id: uid });
}
