export default function handler(_req, res) {
  res.setHeader("Access-Control-Allow-Origin", "*");
  res.status(200).json({
    status: "ok",
    service: "veda_ai_core",
    mode: "vercel",
    layers: ["retrieval", "validation", "citations"],
  });
}

export { getStatus };
