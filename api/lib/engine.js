import { readFileSync } from "fs";
import { join } from "path";

const CORPUS = JSON.parse(
  readFileSync(join(process.cwd(), "data", "corpus.json"), "utf8")
);

const NEGATION_NEARBY = [
  "worsen", "worsens", "avoid", "contraindicated", "not recommended", "must be avoided",
  "increase", "aggravates",
];

const AMBIGUOUS = new Set([
  "loss", "pain", "help", "remedy", "remedies", "treatment", "cure", "problem",
  "condition", "disease", "disorder", "symptom", "symptoms", "issue", "issues",
]);

const CONDITION_ALIASES = {
  Amlapitta: ["acidity", "hyperacidity", "heartburn", "acid reflux", "amlapitta", "gerd"],
  Sthoulya: ["weight loss", "lose weight", "obesity", "overweight", "sthoulya", "medha", "fat reduction", "slimming"],
  Khalitya: ["hair loss", "khalitya", "baldness", "alopecia"],
  Darunaka: ["darunaka", "dandruff", "scalp flakes"],
  "Pitta aggravation": ["pitta aggravation", "pitta prakopa", "aggravated pitta"],
};

const GRAPH = {
  "Bhringraj Taila": { contraindicated_for: ["Pitta aggravation", "Amlapitta", "Acidity"] },
  "Trikatu Churna": { contraindicated_for: ["Pitta aggravation", "Amlapitta", "Acidity"] },
};

const MIN_SCORE = 0.38;

function tokens(text) {
  return (text.toLowerCase().match(/[a-zA-Z\u0900-\u097F]{2,}/g) || []);
}

function isNegationOnly(query, text) {
  const lower = text.toLowerCase();
  for (const term of tokens(query)) {
    if (term.length < 4 || !lower.includes(term)) continue;
    const idx = lower.indexOf(term);
    const window = lower.slice(Math.max(0, idx - 55), idx + term.length + 55);
    if (NEGATION_NEARBY.some((n) => window.includes(n))) return true;
  }
  return false;
}

function analyzeQuery(query) {
  const lower = query.toLowerCase().trim();
  let intent = "treatment";
  if (["contraindication", "contraindicated", "what to avoid", "should not take"].some((k) => lower.includes(k))) {
    intent = "contraindication";
  }
  const conditions = [];
  const topics = [];
  for (const [canonical, aliases] of Object.entries(CONDITION_ALIASES)) {
    if (aliases.some((a) => lower.includes(a))) {
      conditions.push(canonical);
      topics.push(canonical.toLowerCase().replace(/ /g, "_"));
    }
  }
  return {
    raw_query: query,
    intent,
    conditions,
    topics,
    is_contraindication: intent === "contraindication",
    wants_remedy: intent === "treatment" || intent === "general",
  };
}

function documentMatches(query, intent, doc) {
  const text = (doc.text || "").toLowerCase();
  const meta = doc.metadata || {};
  const metaTopics = (meta.topics || []).map(String);
  const metaConditions = (meta.conditions || []).map(String);
  const blob = [text, ...metaTopics, ...metaConditions].join(" ").toLowerCase();

  if (intent.wants_remedy && isNegationOnly(query, text)) return false;

  if (intent.conditions.length) {
    let matched = false;
    for (const cond of intent.conditions) {
      const c = cond.toLowerCase();
      if (blob.includes(c) || metaConditions.map((x) => x.toLowerCase()).includes(c)) {
        if (intent.wants_remedy && meta.content_type === "contraindication") return false;
        matched = true;
        break;
      }
    }
    if (!matched && !intent.is_contraindication) {
      const topicHit = intent.topics.some(
        (t) => blob.includes(t.replace(/_/g, " ")) || metaTopics.map((x) => x.toLowerCase()).includes(t)
      );
      if (!topicHit) return false;
    }
  }

  const qTokens = tokens(query);
  const specific = qTokens.filter((t) => !AMBIGUOUS.has(t));
  if (specific.length) {
    const blobSet = new Set(tokens(blob));
    if (!specific.every((t) => blobSet.has(t))) return false;
  } else if (intent.conditions.length) {
    if (!intent.conditions.some((c) => blob.includes(c.toLowerCase()))) return false;
  }

  if (qTokens.includes("weight") || qTokens.includes("obesity") || qTokens.includes("sthoulya")) {
    if (!["weight", "obesity", "sthoulya", "medha", "fat", "overweight"].some((w) => blob.includes(w))) return false;
    if (["hair", "khalitya", "dandruff", "darunaka", "bhringraj"].some((w) => blob.includes(w))) {
      if (!["hair", "khalitya", "dandruff"].some((w) => qTokens.includes(w))) return false;
    }
  }
  if (qTokens.includes("hair") || qTokens.includes("khalitya")) {
    if (!["hair", "khalitya", "bhringraj", "darunaka"].some((w) => blob.includes(w))) return false;
  }
  if (qTokens.includes("acidity") || qTokens.includes("amlapitta")) {
    if (!["acidity", "amlapitta", "hyperacidity", "heartburn"].some((w) => blob.includes(w))) return false;
  }
  return true;
}

function scoreDoc(query, intent, doc) {
  if (!documentMatches(query, intent, doc)) return 0;
  const text = (doc.text || "").toLowerCase();
  const meta = doc.metadata || {};
  const blob = [text, ...(meta.topics || []), ...(meta.conditions || [])].join(" ").toLowerCase();
  const qSet = new Set(tokens(query));
  const bSet = new Set(tokens(blob));
  let overlap = [...qSet].filter((t) => bSet.has(t)).length / Math.max(qSet.size, 1);
  let score = overlap * 0.55;
  if (text.includes(query.toLowerCase())) score += 0.2;
  if (intent.wants_remedy && meta.content_type === "indication") score += 0.2;
  for (const c of intent.conditions) {
    if (blob.includes(c.toLowerCase())) score += 0.3;
  }
  return Math.min(score, 1);
}

function formatCitation(g, s, a, sh) {
  return `${g} | ${s} | Adhyaya ${a} | Shloka ${sh}`;
}

function search(query, topK = 8) {
  const intent = analyzeQuery(query);
  const scored = CORPUS.map((doc) => ({
    ...doc,
    match_score: scoreDoc(query, intent, doc),
  }))
    .filter((d) => d.match_score >= MIN_SCORE && documentMatches(query, intent, d))
    .sort((a, b) => b.match_score - a.match_score)
    .slice(0, topK);
  return { intent, hits: scored };
}

function buildAnswer(intent, hits) {
  if (!hits.length) {
    return {
      answer: `No verified classical references for "${intent.raw_query}" are indexed yet. Try Ayurvedic terms such as Sthoulya (weight), Khalitya (hair loss), or Amlapitta (acidity).`,
      grounded: false,
      remedies: [],
      citations: [],
      safety_notes: [],
    };
  }

  const label = intent.conditions[0] || intent.raw_query;
  const lines = [`Classical references for ${label}:`];
  const seen = new Set();
  const remedies = [];
  const citations = [];
  const safety = [];

  for (const h of hits) {
    const meta = h.metadata || {};
    if (intent.wants_remedy && meta.content_type === "contraindication") continue;
    const fname = meta.formulation || "See classical text";
    const key = fname.toLowerCase();
    if (seen.has(key)) continue;
    seen.add(key);
    const cite = formatCitation(h.grantha, h.sthana, h.adhyaya, h.shloka);
    lines.push(`• ${fname}: ${(h.text || "").slice(0, 220)}`);
    citations.push(cite);
    remedies.push({
      condition_confirmed: label,
      formulation_name: fname,
      source_citation: cite,
      modern_evidence_summary: (h.text || "").slice(0, 280),
      duration_days: 28,
    });
    const g = GRAPH[fname];
    if (g && intent.conditions.some((c) => g.contraindicated_for.includes(c))) {
      safety.push(`Avoid ${fname}: contraindicated for ${intent.conditions.join(", ")} per knowledge graph.`);
    }
    if (lines.length > 5) break;
  }

  lines.push("Consult a qualified Vaidya for personalized dosing.");
  return {
    answer: lines.join(" "),
    grounded: remedies.length > 0,
    remedies: remedies.slice(0, 5),
    citations,
    safety_notes: safety,
  };
}

export function runQuery(query) {
  const started = performance.now();
  const { intent, hits } = search(query.trim());
  const result = buildAnswer(intent, hits);
  return {
    elapsed_ms: Math.round(performance.now() - started),
    query: query.trim(),
    result: {
      ...result,
      query_intent: intent.intent,
      conditions_detected: intent.conditions,
      query: query.trim(),
      sources_used: hits.length,
    },
  };
}

export function getStatus() {
  const granthas = new Set();
  const conditions = new Set();
  const formulations = new Set();
  for (const v of CORPUS) {
    if (v.grantha) granthas.add(v.grantha);
    const m = v.metadata || {};
    (m.conditions || []).forEach((c) => conditions.add(String(c)));
    if (m.formulation) formulations.add(String(m.formulation));
  }
  return {
    mode: "vercel",
    full_stack: false,
    corpus: {
      verse_count: CORPUS.length,
      granthas: [...granthas].sort(),
      conditions_indexed: [...conditions].sort(),
      formulations_indexed: [...formulations].sort(),
    },
    layers: [
      { name: "Knowledge base", role: "Classical corpus", status: "online" },
      { name: "Retrieval", role: "Validated lexical search", status: "online" },
      { name: "Safety graph", role: "Contraindication rules", status: "online" },
    ],
    data_stores: ["Indexed corpus"],
  };
}

export function retrieve(q, limit = 5) {
  const { hits } = search(q, limit);
  return { hits };
}
