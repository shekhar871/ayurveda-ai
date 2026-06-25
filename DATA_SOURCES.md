# Data Sources & Authenticity

AyurVeda AI indexes **primary classical Ayurvedic texts** paired with structured English glosses for hybrid retrieval. Every answer is grounded in registered citations — the system refuses to invent formulations when no passage passes validation.

## Classical sources (Sanskrit)

| Grantha | Stotra sections used | Topics indexed |
|---------|---------------------|----------------|
| **Charaka Samhita** | Sutra & Chikitsa Sthana | Sthoulya, Amlapitta, tridosha diet |
| **Ashtanga Hridayam** | Sutra & Chikitsa Sthana | Khalitya, Darunaka, Pitta, Guggulu |
| **Sushruta Samhita** | Sutra & Chikitsa Sthana | Pitta gunas, Triphala |
| **Bhaishajya Ratnavali** | Amlapitta chapter | Kamadudha Rasa |

Sanskrit verses in `data/corpus.json` use Devanagari script with grantha/sthana/adhyaya/shloka coordinates for citation verification.

## English clinical glosses

Entries tagged `ClinicalCompendium` are **structured English summaries** aligned to the adjacent Sanskrit verse. They exist to improve lexical retrieval and user readability — they are not independent medical claims. The citation address always points to the paired classical reference where applicable.

## Citation format

```
Grantha | Sthana | Adhyaya N | Shloka N
```

Example: `AshtangaHridayam | Chikitsasthana | Adhyaya 8 | Shloka 12`

## Graph relationships (Neo4j / lite graph)

Formulation nodes link to:

- **indicated_in** — classical conditions (Khalitya, Amlapitta, Sthoulya, …)
- **contraindicated_for** — dosha/condition conflicts (e.g. Bhringraj ↔ Pitta aggravation)
- **trials / citations** — evidence counters from indexed passages

## Validation pipeline

1. **Query intent** — maps colloquial terms to Ayurvedic conditions (e.g. "weight loss" → Sthoulya)
2. **Domain gate** — blocks cross-domain token matches (e.g. "loss" in hair vs weight)
3. **Citation audit** — verifies grantha coordinates exist in the citation registry
4. **Empty response** — honest "not indexed" message instead of hallucination

## Expanding the corpus

Add entries to `data/corpus.json`, then:

```bash
python3 scripts/seed_corpus.py lite   # or: full
```

Each entry requires: `text`, `grantha`, `sthana`, `adhyaya`, `shloka`, `language`, and `metadata` with `conditions`, `topics`, and `content_type`.
