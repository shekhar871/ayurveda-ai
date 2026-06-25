import { useCallback, useEffect, useState } from "react";
import { api, type QueryResult, type StackStatus } from "./lib/api";

const USER_KEY = "ayur_user_id";
const SEASONS = ["", "vasanta", "grishma", "varsha", "sharad", "hemanta", "shishira"];

const EXAMPLES = [
  "weight loss",
  "acidity remedies",
  "hair loss Khalitya",
  "Pitta contraindications",
];

type Tab = "consult" | "profile" | "protocol" | "feedback";

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
      setUserId(null);
    },
  };
}

export default function App() {
  const [tab, setTab] = useState<Tab>("consult");
  const [online, setOnline] = useState<boolean | null>(null);
  const [stack, setStack] = useState<StackStatus | null>(null);
  const { userId, setUserId, clear } = useUserId();

  const refresh = useCallback(async () => {
    try {
      await api.health();
      setOnline(true);
      setStack(await api.stackStatus());
    } catch {
      setOnline(false);
      setStack(null);
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  const tabs: { id: Tab; label: string }[] = [
    { id: "consult", label: "Consult" },
    { id: "profile", label: "Profile" },
    { id: "protocol", label: "Care Plan" },
    { id: "feedback", label: "Feedback" },
  ];

  return (
    <div className="min-h-screen flex flex-col">
      <header className="border-b border-stone-200 bg-white">
        <div className="max-w-5xl mx-auto px-4 py-4 flex flex-wrap items-center justify-between gap-4">
          <div>
            <h1 className="font-serif text-xl font-bold text-emerald-900 tracking-tight">AyurVeda AI</h1>
            <p className="text-xs text-stone-500 mt-0.5">Classical reference · Citation verified</p>
          </div>
          <div className="flex items-center gap-2">
            {online === true && (
              <span className="inline-flex items-center gap-1.5 text-xs text-emerald-700 font-medium">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
                Online
              </span>
            )}
            <nav className="flex gap-1">
              {tabs.map((t) => (
                <button
                  key={t.id}
                  onClick={() => setTab(t.id)}
                  className={`nav-link ${tab === t.id ? "nav-active" : "nav-idle"}`}
                >
                  {t.label}
                </button>
              ))}
            </nav>
          </div>
        </div>
      </header>

      <main className="flex-1 max-w-5xl mx-auto w-full px-4 py-8">
        {tab === "consult" && (
          <ConsultPanel userId={userId} corpusCount={stack?.corpus?.verse_count} online={online} />
        )}
        {tab === "profile" && (
          <ProfilePanel userId={userId} setUserId={setUserId} clear={clear} onDone={() => setTab("consult")} />
        )}
        {tab === "protocol" && <ProtocolPanel userId={userId} />}
        {tab === "feedback" && <FeedbackPanel userId={userId} />}
      </main>

      <footer className="border-t border-stone-200 py-6 text-center text-xs text-stone-500">
        <p>For educational reference only · Consult a qualified Vaidya for medical advice</p>
      </footer>
    </div>
  );
}

function ConsultPanel({
  userId,
  corpusCount,
  online,
}: {
  userId: string | null;
  corpusCount?: number;
  online: boolean | null;
}) {
  const [query, setQuery] = useState("");
  const [season, setSeason] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<{ elapsed_ms: number; query: string; result: QueryResult } | null>(null);

  const submit = async (q?: string) => {
    const text = (q ?? query).trim();
    if (text.length < 3) return;
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      setResult(await api.query(text, userId, season || undefined));
      setQuery(text);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Something went wrong. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="font-serif text-2xl font-semibold text-stone-900">Symptom search</h2>
        <p className="text-sm text-stone-500 mt-1">
          Search classical texts by condition, symptom, or Sanskrit term
          {corpusCount ? ` · ${corpusCount} indexed passages` : ""}
        </p>
      </div>

      <div className="card">
        <textarea
          className="input-field min-h-[96px] resize-y"
          placeholder="e.g. acidity, Sthoulya, Khalitya, Pitta aggravation…"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) submit();
          }}
        />
        <div className="flex flex-wrap gap-3 mt-3 items-center">
          <select className="input-field w-auto min-w-[140px]" value={season} onChange={(e) => setSeason(e.target.value)}>
            <option value="">Season (optional)</option>
            {SEASONS.filter(Boolean).map((s) => (
              <option key={s} value={s}>{s}</option>
            ))}
          </select>
          <button className="btn-primary" onClick={() => submit()} disabled={loading || query.length < 3}>
            {loading ? "Searching…" : "Search"}
          </button>
        </div>
        <div className="flex flex-wrap gap-2 mt-4">
          {EXAMPLES.map((s) => (
            <button
              key={s}
              type="button"
              className="text-xs px-3 py-1 rounded-full border border-stone-200 text-stone-600 hover:border-emerald-700 hover:text-emerald-800 transition"
              onClick={() => {
                setQuery(s);
                submit(s);
              }}
            >
              {s}
            </button>
          ))}
        </div>
        {online === false && !loading && (
          <p className="mt-3 text-sm text-amber-700">Connecting to service… If this persists, refresh the page.</p>
        )}
        {error && <p className="mt-3 text-sm text-red-600">{error}</p>}
      </div>

      {loading && (
        <div className="card text-center py-10 text-stone-500 text-sm">Searching classical references…</div>
      )}
      {result && !loading && <ResultsView data={result} />}
    </div>
  );
}

function ResultsView({ data }: { data: { elapsed_ms: number; query: string; result: QueryResult } }) {
  const r = data.result;
  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center gap-2 text-sm">
        {r.grounded ? (
          <span className="text-emerald-700 font-medium">Verified</span>
        ) : (
          <span className="text-amber-700 font-medium">No matching references</span>
        )}
        {r.conditions_detected?.length ? (
          <span className="text-stone-500">· {r.conditions_detected.join(", ")}</span>
        ) : null}
        {r.sources_used != null && (
          <span className="text-stone-400">· {r.sources_used} sources · {data.elapsed_ms.toFixed(0)} ms</span>
        )}
      </div>

      <div className="card border-l-4 border-l-emerald-700">
        <h3 className="text-sm font-semibold text-stone-700 mb-2">Summary</h3>
        <p className="text-sm leading-relaxed text-stone-800">{r.answer}</p>
      </div>

      {r.safety_notes.length > 0 && (
        <div className="card border-l-4 border-l-amber-500 bg-amber-50/50">
          <h3 className="text-sm font-semibold text-amber-900 mb-2">Safety notes</h3>
          <ul className="list-disc pl-5 text-sm text-amber-900/90 space-y-1">
            {r.safety_notes.map((n, i) => (
              <li key={i}>{n}</li>
            ))}
          </ul>
        </div>
      )}

      {r.remedies.length > 0 && (
        <div>
          <h3 className="text-sm font-semibold text-stone-700 mb-3">Formulations</h3>
          <div className="grid gap-3 md:grid-cols-2">
            {r.remedies.map((rem, i) => (
              <div key={i} className="card">
                <div className="flex justify-between gap-2 mb-2">
                  <h4 className="font-medium text-stone-900">{rem.formulation_name}</h4>
                  <span className="text-xs text-stone-500 shrink-0">{rem.condition_confirmed}</span>
                </div>
                <p className="text-xs font-mono text-stone-500 mb-2">{rem.source_citation}</p>
                <p className="text-sm text-stone-700 leading-relaxed">{rem.modern_evidence_summary}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {r.citations.length > 0 && (
        <div className="card">
          <h3 className="text-sm font-semibold text-stone-700 mb-2">Citations</h3>
          <ul className="space-y-1 text-xs font-mono text-stone-500">
            {r.citations.map((c, i) => (
              <li key={i}>{c}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

function ProfilePanel({
  userId,
  setUserId,
  clear,
  onDone,
}: {
  userId: string | null;
  setUserId: (id: string) => void;
  clear: () => void;
  onDone: () => void;
}) {
  const [prakriti, setPrakriti] = useState('{"vata": 0.33, "pitta": 0.34, "kapha": 0.33}');
  const [vikriti, setVikriti] = useState('{"aggravated": []}');
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
      setStatus("Profile saved.");
      setTimeout(onDone, 600);
    } catch (e) {
      setStatus(e instanceof Error ? e.message : "Could not save profile.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-lg">
      <h2 className="font-serif text-2xl font-semibold text-stone-900 mb-1">Your profile</h2>
      <p className="text-sm text-stone-500 mb-6">Prakriti and Vikriti inform safety screening during search.</p>
      <div className="card space-y-4">
        <div>
          <label className="block text-sm font-medium text-stone-700 mb-1">Prakriti (JSON)</label>
          <textarea className="input-field font-mono text-xs" rows={2} value={prakriti} onChange={(e) => setPrakriti(e.target.value)} />
        </div>
        <div>
          <label className="block text-sm font-medium text-stone-700 mb-1">Vikriti (JSON)</label>
          <textarea className="input-field font-mono text-xs" rows={2} value={vikriti} onChange={(e) => setVikriti(e.target.value)} />
        </div>
        <div>
          <label className="block text-sm font-medium text-stone-700 mb-1">Allergies</label>
          <input className="input-field" value={allergies} onChange={(e) => setAllergies(e.target.value)} placeholder="comma-separated" />
        </div>
        <div className="flex gap-3 pt-2">
          <button className="btn-primary" onClick={save} disabled={loading}>{loading ? "Saving…" : "Save"}</button>
          {userId && <button className="btn-secondary" onClick={clear}>Sign out</button>}
        </div>
        {status && <p className="text-sm text-emerald-700">{status}</p>}
      </div>
    </div>
  );
}

function ProtocolPanel({ userId }: { userId: string | null }) {
  const [protocolId, setProtocolId] = useState("Guggulu Yoga");
  const [imbalance, setImbalance] = useState("Sthoulya");
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
      setResult({ error: e instanceof Error ? e.message : "Request failed" });
    } finally {
      setLoading(false);
    }
  };

  if (!userId) {
    return (
      <div className="max-w-lg card text-sm text-stone-600">
        Create a profile first to use care plan alternatives.
      </div>
    );
  }

  return (
    <div className="max-w-lg space-y-4">
      <div>
        <h2 className="font-serif text-2xl font-semibold text-stone-900 mb-1">Care plan</h2>
        <p className="text-sm text-stone-500">Find alternative formulations when a protocol is not effective.</p>
      </div>
      <div className="card space-y-4">
        <div>
          <label className="block text-sm font-medium text-stone-700 mb-1">Current formulation</label>
          <input className="input-field" value={protocolId} onChange={(e) => setProtocolId(e.target.value)} />
        </div>
        <div>
          <label className="block text-sm font-medium text-stone-700 mb-1">Observed condition</label>
          <input className="input-field" value={imbalance} onChange={(e) => setImbalance(e.target.value)} />
        </div>
        <button className="btn-primary" onClick={run} disabled={loading}>
          {loading ? "Searching…" : "Find alternatives"}
        </button>
      </div>
      {result && (
        <pre className="card text-xs font-mono overflow-auto bg-stone-50 text-stone-700">{JSON.stringify(result, null, 2)}</pre>
      )}
    </div>
  );
}

function FeedbackPanel({ userId }: { userId: string | null }) {
  const [formulation, setFormulation] = useState("Shatavari Swarasa");
  const [outcome, setOutcome] = useState("helped");
  const [day, setDay] = useState(14);
  const [notes, setNotes] = useState("");
  const [status, setStatus] = useState<string | null>(null);

  const submit = async () => {
    if (!userId) return;
    try {
      await api.feedback({
        user_id: userId,
        formulation_name: formulation,
        outcome,
        checkpoint_day: day,
        notes,
      });
      setStatus("Feedback recorded. Thank you.");
    } catch (e) {
      setStatus(e instanceof Error ? e.message : "Could not submit feedback.");
    }
  };

  if (!userId) {
    return (
      <div className="max-w-lg card text-sm text-stone-600">
        Create a profile first to submit treatment feedback.
      </div>
    );
  }

  return (
    <div className="max-w-lg">
      <h2 className="font-serif text-2xl font-semibold text-stone-900 mb-1">Feedback</h2>
      <p className="text-sm text-stone-500 mb-6">Record how a formulation worked for you.</p>
      <div className="card space-y-4">
        <div>
          <label className="block text-sm font-medium text-stone-700 mb-1">Formulation</label>
          <input className="input-field" value={formulation} onChange={(e) => setFormulation(e.target.value)} />
        </div>
        <div>
          <label className="block text-sm font-medium text-stone-700 mb-1">Outcome</label>
          <select className="input-field" value={outcome} onChange={(e) => setOutcome(e.target.value)}>
            <option value="helped">Helped</option>
            <option value="no_effect">No effect</option>
            <option value="worsened">Worsened</option>
          </select>
        </div>
        <div>
          <label className="block text-sm font-medium text-stone-700 mb-1">Day</label>
          <input type="number" className="input-field" value={day} onChange={(e) => setDay(Number(e.target.value))} min={1} />
        </div>
        <div>
          <label className="block text-sm font-medium text-stone-700 mb-1">Notes</label>
          <textarea className="input-field" rows={2} value={notes} onChange={(e) => setNotes(e.target.value)} />
        </div>
        <button className="btn-primary" onClick={submit}>Submit</button>
        {status && <p className="text-sm text-emerald-700">{status}</p>}
      </div>
    </div>
  );
}
