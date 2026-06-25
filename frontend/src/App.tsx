import { useCallback, useEffect, useState } from "react";
import { api, type Health, type QueryResult, type StackStatus } from "./lib/api";

const USER_KEY = "ayur_user_id";
const ONBOARDED_KEY = "ayur_onboarded";
const SEASONS = ["", "vasanta", "grishma", "varsha", "sharad", "hemanta", "shishira"];
const SAMPLE_QUERIES = [
  "weight loss Sthoulya",
  "acidity remedies",
  "Khalitya hair loss Bhringraj",
  "Pitta aggravation contraindications",
];

type Tab = "home" | "consult" | "profile" | "protocol" | "feedback" | "admin";

function useUserId() {
  const [userId, setUserId] = useState<string | null>(() => localStorage.getItem(USER_KEY));
  const save = (id: string) => {
    localStorage.setItem(USER_KEY, id);
    setUserId(id);
  };
  return {
    userId,
    setUserId: save,
    clear: () => {
      localStorage.removeItem(USER_KEY);
      localStorage.removeItem(ONBOARDED_KEY);
      setUserId(null);
    },
  };
}

export default function App() {
  const [tab, setTab] = useState<Tab>("home");
  const [health, setHealth] = useState<Health | null>(null);
  const [stack, setStack] = useState<StackStatus | null>(null);
  const { userId, setUserId, clear } = useUserId();

  const refresh = useCallback(async () => {
    try {
      setHealth(await api.health());
      setStack(await api.stackStatus());
    } catch {
      setHealth(null);
      setStack(null);
    }
  }, []);

  useEffect(() => {
    refresh();
    const t = setInterval(refresh, 12000);
    return () => clearInterval(t);
  }, [refresh]);

  const isFull = health?.mode === "docker" || stack?.full_stack;
  const tabs: { id: Tab; label: string; icon: string }[] = [
    { id: "home", label: "Home", icon: "🏠" },
    { id: "consult", label: "Consult", icon: "🪷" },
    { id: "profile", label: "Profile", icon: "👤" },
    { id: "protocol", label: "Protocol", icon: "📋" },
    { id: "feedback", label: "Feedback", icon: "✓" },
    { id: "admin", label: "System", icon: "⚙" },
  ];

  return (
    <div className="min-h-screen flex flex-col bg-gradient-to-b from-cream to-cream-dark/30">
      <header className="border-b border-cream-dark bg-white/80 backdrop-blur-md sticky top-0 z-50 shadow-sm">
        <div className="max-w-6xl mx-auto px-4 py-3 flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <div className="w-11 h-11 rounded-2xl bg-gradient-to-br from-leaf to-leaf-dark flex items-center justify-center text-xl shadow">
              🌿
            </div>
            <div>
              <h1 className="font-display text-xl sm:text-2xl text-leaf-dark tracking-tight">
                AyurVeda AI
              </h1>
              <p className="text-xs text-bark-muted">
                {isFull ? "Web App · Full OSS Stack" : "Web App · Demo Mode"}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2 flex-wrap">
            {health ? (
              <span
                className={`px-3 py-1.5 rounded-full text-xs font-semibold border ${
                  isFull
                    ? "bg-gradient-to-r from-saffron/20 to-leaf/10 text-bark border-saffron/40"
                    : "bg-amber-50 text-amber-800 border-amber-200"
                }`}
              >
                {isFull ? "● PostgreSQL · Qdrant · Neo4j" : "○ Lite demo"}
              </span>
            ) : (
              <span className="px-3 py-1.5 rounded-full bg-red-50 text-red-700 text-xs font-medium">
                Offline — run ./run-full.sh
              </span>
            )}
          </div>
        </div>
        <nav className="max-w-6xl mx-auto px-4 pb-2 flex gap-1 overflow-x-auto scrollbar-hide">
          {tabs.map((t) => (
            <button
              key={t.id}
              onClick={() => setTab(t.id)}
              className={`px-3 sm:px-4 py-2 rounded-xl text-sm font-medium whitespace-nowrap transition ${
                tab === t.id ? "tab-active" : "tab-inactive"
              }`}
            >
              {t.icon} {t.label}
            </button>
          ))}
        </nav>
      </header>

      <main className="flex-1 max-w-6xl mx-auto w-full px-4 py-6 sm:py-8">
        {!health && (
          <div className="card mb-6 border-amber-300 bg-amber-50">
            <h2 className="font-semibold text-amber-900">Start the application</h2>
            <p className="text-sm mt-2 text-amber-800">
              Open Terminal, run:{" "}
              <code className="bg-white px-2 py-0.5 rounded">cd veda_ai_core && ./run-full.sh</code>
            </p>
            <p className="text-xs mt-2 text-amber-700">Requires Docker Desktop for the full stack.</p>
          </div>
        )}

        {tab === "home" && (
          <HomeTab
            stack={stack}
            isFull={!!isFull}
            userId={userId}
            onConsult={() => setTab("consult")}
            onProfile={() => setTab("profile")}
          />
        )}
        {tab === "consult" && (
          <ConsultTab userId={userId} isFull={!!isFull} corpusCount={stack?.corpus?.verse_count} onNeedFullStack={() => setTab("admin")} />
        )}
        {tab === "profile" && (
          <ProfileTab userId={userId} setUserId={setUserId} clear={clear} isFull={!!isFull} onDone={() => setTab("consult")} />
        )}
        {tab === "protocol" && <ProtocolTab userId={userId} />}
        {tab === "feedback" && <FeedbackTab userId={userId} />}
        {tab === "admin" && <AdminTab onHealth={refresh} isFull={!!isFull} />}
      </main>

      <footer className="border-t border-cream-dark/80 bg-white/50 py-5 text-center text-xs text-bark-muted space-y-1">
        <p>AyurVeda AI · Citation-verified classical retrieval · Built by Shekhar Jadhav</p>
        <p className="opacity-80">Educational reference only — not a substitute for licensed medical care</p>
      </footer>
    </div>
  );
}

function HomeTab({
  stack,
  isFull,
  userId,
  onConsult,
  onProfile,
}: {
  stack: StackStatus | null;
  isFull: boolean;
  userId: string | null;
  onConsult: () => void;
  onProfile: () => void;
}) {
  const corpus = stack?.corpus;
  return (
    <div className="space-y-6">
      <section className="card overflow-hidden relative">
        <div className="absolute inset-0 bg-gradient-to-br from-leaf/5 via-transparent to-saffron/5 pointer-events-none" />
        <div className="relative">
          <p className="text-xs font-semibold uppercase tracking-widest text-saffron mb-2">Portfolio Project</p>
          <h2 className="font-display text-2xl sm:text-3xl text-leaf-dark mb-2">
            Classical Ayurveda, powered by open infrastructure
          </h2>
          <p className="text-bark-muted max-w-2xl leading-relaxed">
            Hybrid RAG over Sanskrit granthas with Neo4j contraindication screening, strict grounding gates,
            and citation-verified formulations — built with FastAPI, PostgreSQL, Qdrant, and React.
          </p>
          {corpus && (
            <div className="flex flex-wrap gap-4 mt-5 text-sm">
              <div className="px-4 py-2 rounded-xl bg-white/80 border border-leaf/20">
                <span className="font-bold text-leaf-dark">{corpus.verse_count}</span>
                <span className="text-bark-muted ml-1">indexed passages</span>
              </div>
              <div className="px-4 py-2 rounded-xl bg-white/80 border border-leaf/20">
                <span className="font-bold text-leaf-dark">{corpus.granthas.length}</span>
                <span className="text-bark-muted ml-1">classical granthas</span>
              </div>
              <div className="px-4 py-2 rounded-xl bg-white/80 border border-leaf/20">
                <span className="font-bold text-leaf-dark">{corpus.formulations_indexed.length}</span>
                <span className="text-bark-muted ml-1">formulations</span>
              </div>
            </div>
          )}
          <div className="flex flex-wrap gap-3 mt-6">
            <button className="btn-primary text-base px-6" onClick={onConsult}>
              Start consultation →
            </button>
            {!userId && (
              <button className="btn-secondary" onClick={onProfile}>
                Set up health profile
              </button>
            )}
          </div>
        </div>
      </section>

      <section className="grid sm:grid-cols-2 lg:grid-cols-4 gap-3">
        {[
          { title: "5-Layer Engine", desc: "OCR → Graph → Retrieval → LLM → Personalization" },
          { title: "Hybrid RAG", desc: "Qdrant vectors + Postgres FTS + BM25" },
          { title: "Safety Graph", desc: "Neo4j contraindication screening" },
          { title: "Grounded Output", desc: "RAG guard + shloka citation audit" },
        ].map((f) => (
          <div key={f.title} className="card py-4">
            <h3 className="font-semibold text-leaf-dark text-sm">{f.title}</h3>
            <p className="text-xs text-bark-muted mt-1">{f.desc}</p>
          </div>
        ))}
      </section>

      {stack && (
        <section className="card">
          <div className="flex justify-between items-center mb-4">
            <h3 className="font-display text-lg text-leaf-dark">Infrastructure status</h3>
            <span className={`text-xs font-bold px-2 py-1 rounded ${isFull ? "bg-leaf/15 text-leaf-dark" : "bg-amber-100 text-amber-800"}`}>
              {isFull ? "FULL STACK" : "LITE"}
            </span>
          </div>
          <div className="grid gap-2 sm:grid-cols-2">
            {stack.layers.map((l) => (
              <div
                key={l.name}
                className={`flex items-center gap-3 p-3 rounded-xl border ${
                  l.status === "online" ? "border-leaf/20 bg-leaf/5" : "border-red-200 bg-red-50"
                }`}
              >
                <span className={`w-2 h-2 rounded-full ${l.status === "online" ? "bg-leaf" : "bg-red-500"}`} />
                <div>
                  <p className="font-medium text-sm">{l.name}</p>
                  <p className="text-xs text-bark-muted">{l.role}</p>
                </div>
              </div>
            ))}
          </div>
          {isFull && (
            <p className="text-xs text-bark-muted mt-4">
              Data stores: {stack.data_stores.join(" · ")}
            </p>
          )}
        </section>
      )}
    </div>
  );
}

function ConsultTab({
  userId,
  isFull,
  corpusCount,
  onNeedFullStack,
}: {
  userId: string | null;
  isFull: boolean;
  corpusCount?: number;
  onNeedFullStack?: () => void;
}) {
  const [query, setQuery] = useState("");
  const [season, setSeason] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<{ elapsed_ms: number; query: string; result: QueryResult } | null>(null);
  const [lastQuery, setLastQuery] = useState("");

  const submit = async (q?: string) => {
    const text = (q ?? query).trim();
    if (text.length < 3) return;
    setLoading(true);
    setError(null);
    setResult(null);
    setLastQuery(text);
    try {
      const response = await api.query(text, userId, season || undefined);
      setResult(response);
      setQuery(text);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Query failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <section className="card">
        <h2 className="font-display text-xl text-leaf-dark mb-1">Symptom consultation</h2>
        <p className="text-sm text-bark-muted mb-4">
          {isFull
            ? "Hybrid search: Qdrant vectors + PostgreSQL FTS + BM25 + BGE-M3 reranking"
            : `Lite mode — ${corpusCount ?? 28} classical passages with strict relevance validation`}
        </p>
        {!isFull && (
          <button type="button" className="text-xs text-saffron underline mb-3" onClick={onNeedFullStack}>
            How to enable full stack →
          </button>
        )}
        <textarea
          className="input-field min-h-[100px] resize-y text-base"
          placeholder="Describe symptoms in English, Hindi, or Sanskrit terms…"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
        <div className="flex flex-wrap gap-3 mt-3 items-center">
          <select className="input-field w-auto min-w-[160px]" value={season} onChange={(e) => setSeason(e.target.value)}>
            <option value="">Season (Ritucharya)</option>
            {SEASONS.filter(Boolean).map((s) => (
              <option key={s} value={s}>{s}</option>
            ))}
          </select>
          <button className="btn-primary" onClick={() => submit()} disabled={loading || query.length < 3}>
            {loading ? "Analyzing…" : "Get guidance"}
          </button>
        </div>
        <div className="flex flex-wrap gap-2 mt-4">
          {SAMPLE_QUERIES.map((s) => (
            <button
              key={s}
              className="text-xs px-3 py-1.5 rounded-lg bg-cream-dark hover:bg-leaf/10 border border-cream-dark transition"
              onClick={() => {
                setQuery(s);
                submit(s);
              }}
            >
              {s}
            </button>
          ))}
        </div>
        {error && <p className="mt-3 text-red-600 text-sm">{error}</p>}
      </section>

      {loading && (
        <div className="card text-center py-8 text-bark-muted animate-pulse">
          Searching knowledge base for: <strong className="text-bark">{lastQuery}</strong>
        </div>
      )}
      {result && !loading && <QueryResults result={result} searchedQuery={lastQuery} />}
    </div>
  );
}

function QueryResults({
  result,
  searchedQuery,
}: {
  result: { elapsed_ms: number; query: string; result: QueryResult };
  searchedQuery: string;
}) {
  const r = result.result;
  return (
    <section className="space-y-4" key={searchedQuery}>
      <div className="card py-3 px-4 bg-leaf/5 border-leaf/20">
        <p className="text-sm">
          <span className="text-bark-muted">Results for: </span>
          <strong className="text-leaf-dark">{result.query || searchedQuery}</strong>
          {r.sources_used != null && (
            <span className="text-bark-muted"> · {r.sources_used} sources matched</span>
          )}
        </p>
      </div>
      <div className="flex flex-wrap gap-2 text-sm items-center">
        <span className={r.grounded ? "text-leaf font-semibold" : "text-amber-600 font-semibold"}>
          {r.grounded ? "✓ Citation-verified" : "⚠ Review citations"}
        </span>
        {r.query_intent && (
          <span className="px-2 py-0.5 rounded bg-saffron/15 text-xs font-medium">
            Intent: {r.query_intent}
            {r.conditions_detected?.length ? ` · ${r.conditions_detected.join(", ")}` : ""}
          </span>
        )}
        {!r.grounded && (
          <span className="px-2 py-0.5 rounded bg-amber-100 text-amber-800 text-xs font-medium">
            Not in knowledge base
          </span>
        )}
        <span className="text-bark-muted">· {result.elapsed_ms.toFixed(0)} ms</span>
      </div>
      <div className="card border-l-4 border-l-leaf">
        <h3 className="font-display text-lg text-leaf-dark mb-2">Guidance</h3>
        <p className="leading-relaxed text-bark">{r.answer}</p>
      </div>
      {r.safety_notes.length > 0 && (
        <div className="card border-l-4 border-l-amber-500 bg-amber-50/80">
          <h3 className="font-semibold text-amber-900 mb-2">⚠ Safety (Neo4j graph)</h3>
          <ul className="list-disc pl-5 text-sm space-y-1">
            {r.safety_notes.map((n, i) => (
              <li key={i}>{n}</li>
            ))}
          </ul>
        </div>
      )}
      <div>
        <h3 className="font-display text-lg text-leaf-dark mb-3">Formulations ({r.remedies.length})</h3>
        <div className="grid gap-4 md:grid-cols-2">
          {r.remedies.map((rem, i) => (
            <div key={i} className="card hover:shadow-md transition border-t-2 border-t-saffron/40">
              <div className="flex justify-between gap-2 mb-2">
                <h4 className="font-semibold">{rem.formulation_name}</h4>
                <span className="text-xs bg-leaf/10 text-leaf-dark px-2 py-0.5 rounded-full shrink-0">
                  {rem.condition_confirmed}
                </span>
              </div>
              <p className="text-xs font-mono text-bark-muted mb-2">📜 {rem.source_citation}</p>
              <p className="text-sm leading-relaxed border-t border-cream-dark pt-2">{rem.modern_evidence_summary}</p>
              <p className="text-xs text-bark-muted mt-2">{rem.duration_days} day protocol</p>
            </div>
          ))}
        </div>
      </div>
      <div className="card">
        <h3 className="font-medium mb-2">Verified citations</h3>
        <ul className="space-y-1 text-sm font-mono text-bark-muted">
          {r.citations.map((c, i) => (
            <li key={i}>{c}</li>
          ))}
        </ul>
      </div>
    </section>
  );
}

function ProfileTab({
  userId,
  setUserId,
  clear,
  isFull,
  onDone,
}: {
  userId: string | null;
  setUserId: (id: string) => void;
  clear: () => void;
  isFull: boolean;
  onDone: () => void;
}) {
  const [prakriti, setPrakriti] = useState('{"vata": 0.3, "pitta": 0.4, "kapha": 0.3}');
  const [vikriti, setVikriti] = useState('{"aggravated": ["Pitta aggravation"]}');
  const [allergies, setAllergies] = useState("");
  const [status, setStatus] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const save = async () => {
    setLoading(true);
    try {
      const res = await api.profile({
        user_id: userId,
        prakriti: JSON.parse(prakriti),
        vikriti: JSON.parse(vikriti),
        allergies: allergies.split(",").map((s) => s.trim()).filter(Boolean),
        contraindications: [],
        active_protocol: {},
      });
      setUserId(res.user_id);
      localStorage.setItem(ONBOARDED_KEY, "1");
      setStatus(isFull ? "Profile saved to PostgreSQL" : "Profile saved to local store");
      setTimeout(onDone, 800);
    } catch (e) {
      setStatus(e instanceof Error ? e.message : "Failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="card max-w-2xl mx-auto">
      <h2 className="font-display text-xl text-leaf-dark mb-2">Prakriti & Vikriti profile</h2>
      <p className="text-sm text-bark-muted mb-6">
        {isFull
          ? "Stored in PostgreSQL JSONB — enables graph contraindication checks during consultation."
          : "Stored locally — enables personalized safety checks in lite demo mode."}
      </p>
      <label className="block text-sm font-medium mb-1">Prakriti (JSON)</label>
      <textarea className="input-field font-mono text-sm mb-4" rows={3} value={prakriti} onChange={(e) => setPrakriti(e.target.value)} />
      <label className="block text-sm font-medium mb-1">Vikriti — aggravated doshas (JSON)</label>
      <textarea className="input-field font-mono text-sm mb-4" rows={2} value={vikriti} onChange={(e) => setVikriti(e.target.value)} />
      <label className="block text-sm font-medium mb-1">Allergies</label>
      <input className="input-field mb-6" value={allergies} onChange={(e) => setAllergies(e.target.value)} placeholder="comma-separated" />
      <div className="flex gap-3">
        <button className="btn-primary" onClick={save} disabled={loading}>{loading ? "Saving…" : "Save & continue"}</button>
        {userId && <button className="btn-secondary" onClick={clear}>Reset session</button>}
      </div>
      {status && <p className="mt-4 text-sm text-leaf-dark">{status}</p>}
    </div>
  );
}

function ProtocolTab({ userId }: { userId: string | null }) {
  const [protocolId, setProtocolId] = useState("Bhringraj Taila");
  const [imbalance, setImbalance] = useState("Khalitya");
  const [result, setResult] = useState<Record<string, unknown> | null>(null);
  const [loading, setLoading] = useState(false);

  const run = async () => {
    if (!userId) return;
    setLoading(true);
    try {
      setResult(
        await api.progressFailure({
          user_id: userId,
          current_protocol_id: protocolId,
          observed_imbalance: imbalance,
        })
      );
    } catch (e) {
      setResult({ error: e instanceof Error ? e.message : "Failed" });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6 max-w-2xl mx-auto">
      {!userId && (
        <div className="card bg-amber-50 border-amber-200 text-sm">Create a profile first to track treatment protocols.</div>
      )}
      <div className="card">
        <h2 className="font-display text-xl text-leaf-dark mb-2">Alternative pathway</h2>
        <p className="text-sm text-bark-muted mb-4">Neo4j graph query on progress failure (Day 14 checkpoint).</p>
        <label className="block text-sm font-medium mb-1">Current protocol</label>
        <input className="input-field mb-3" value={protocolId} onChange={(e) => setProtocolId(e.target.value)} />
        <label className="block text-sm font-medium mb-1">Observed imbalance (Roga)</label>
        <input className="input-field mb-4" value={imbalance} onChange={(e) => setImbalance(e.target.value)} />
        <button className="btn-primary" onClick={run} disabled={loading || !userId}>
          {loading ? "Querying Neo4j…" : "Find alternative formulation"}
        </button>
      </div>
      {result && (
        <pre className="card text-xs font-mono overflow-auto bg-bark/5 p-4">{JSON.stringify(result, null, 2)}</pre>
      )}
    </div>
  );
}

function FeedbackTab({ userId }: { userId: string | null }) {
  const [formulation, setFormulation] = useState("Bhringraj Taila");
  const [outcome, setOutcome] = useState("helped");
  const [day, setDay] = useState(14);
  const [notes, setNotes] = useState("");
  const [status, setStatus] = useState<string | null>(null);

  const submit = async () => {
    if (!userId) return;
    try {
      const res = await api.feedback({
        user_id: userId,
        formulation_name: formulation,
        outcome,
        checkpoint_day: day,
        notes,
      });
      setStatus(`Recorded · efficacy Δ ${res.efficacy_delta}`);
    } catch (e) {
      setStatus(e instanceof Error ? e.message : "Failed");
    }
  };

  return (
    <div className="card max-w-2xl mx-auto">
      <h2 className="font-display text-xl text-leaf-dark mb-4">Treatment feedback loop</h2>
      {!userId && <p className="text-amber-700 text-sm mb-4">Profile required.</p>}
      <label className="block text-sm font-medium mb-1">Formulation</label>
      <input className="input-field mb-3" value={formulation} onChange={(e) => setFormulation(e.target.value)} />
      <label className="block text-sm font-medium mb-1">Outcome</label>
      <select className="input-field mb-3" value={outcome} onChange={(e) => setOutcome(e.target.value)}>
        <option value="helped">Helped</option>
        <option value="no_effect">No effect</option>
        <option value="worsened">Worsened</option>
      </select>
      <label className="block text-sm font-medium mb-1">Checkpoint day</label>
      <input type="number" className="input-field mb-3" value={day} onChange={(e) => setDay(Number(e.target.value))} min={1} />
      <label className="block text-sm font-medium mb-1">Notes</label>
      <textarea className="input-field mb-4" rows={2} value={notes} onChange={(e) => setNotes(e.target.value)} />
      <button className="btn-primary" onClick={submit} disabled={!userId}>Submit feedback</button>
      {status && <p className="mt-4 text-sm text-leaf-dark">{status}</p>}
    </div>
  );
}

function AdminTab({ onHealth, isFull }: { onHealth: () => void; isFull: boolean }) {
  const [retrieveQ, setRetrieveQ] = useState("Bhringraj");
  const [hits, setHits] = useState<Record<string, unknown>[] | null>(null);
  const [msg, setMsg] = useState<string | null>(null);

  const seed = async () => {
    try {
      const r = await api.ingestSample();
      setMsg(`Indexed ${r.ingested} verses into ${isFull ? "Postgres + Qdrant" : "lite store"}`);
      onHealth();
    } catch (e) {
      setMsg(e instanceof Error ? e.message : "Failed");
    }
  };

  return (
    <div className="space-y-6">
      <div className="card">
        <h2 className="font-display text-xl text-leaf-dark mb-4">System administration</h2>
        <div className="flex flex-wrap gap-3">
          <button className="btn-primary" onClick={seed}>Re-index sample scriptures</button>
          <a href="/docs" target="_blank" rel="noreferrer" className="btn-secondary inline-flex items-center">
            API reference
          </a>
          {isFull && (
            <>
              <a href="http://127.0.0.1:7474" target="_blank" rel="noreferrer" className="btn-secondary inline-flex items-center">
                Neo4j browser
              </a>
              <a href="http://127.0.0.1:6333/dashboard" target="_blank" rel="noreferrer" className="btn-secondary inline-flex items-center">
                Qdrant UI
              </a>
            </>
          )}
        </div>
        {msg && <p className="mt-3 text-sm">{msg}</p>}
      </div>
      <div className="card">
        <h3 className="font-medium mb-3">Retrieval debug (hybrid)</h3>
        <div className="flex gap-2">
          <input className="input-field flex-1" value={retrieveQ} onChange={(e) => setRetrieveQ(e.target.value)} />
          <button className="btn-secondary" onClick={async () => setHits((await api.retrieve(retrieveQ)).hits)}>
            Search
          </button>
        </div>
        {hits && (
          <pre className="mt-4 text-xs font-mono overflow-auto max-h-64 bg-bark/5 p-4 rounded-xl">
            {JSON.stringify(hits, null, 2)}
          </pre>
        )}
      </div>
    </div>
  );
}
