import { retrieve } from "../lib/engine.js";

export default function handler(req, res) {
  res.setHeader("Access-Control-Allow-Origin", "*");
  const q = (req.query?.q || "").trim();
  const limit = Math.min(parseInt(req.query?.limit || "5", 10), 20);
  if (q.length < 3) return res.status(400).json({ detail: "Query too short" });
  res.status(200).json(retrieve(q, limit));
}
