# The Unofficial Guide — Project 1

> **How to use this template:**
> Complete each section *after* you've built and tested the corresponding part of your system.
> Do not write placeholder text — if a section isn't done yet, leave it blank and come back.
> Every section below is required for submission. One-liners will not receive full credit.

---

## Domain

**GRC Data Protection Policy Retrieval System.**

This system covers **global data protection and privacy law** — a Governance, Risk, and
Compliance (GRC) knowledge base built from the statutory data-protection acts of multiple
countries (Poland, Lesotho, Zambia, Iceland, the United States, Kenya, Nigeria, Ghana,
Uganda, and Mauritius). It lets a user ask natural-language questions about a jurisdiction's
data-protection rules — breach-notification timelines, data-subject rights, controller
obligations, enforcement authorities — and returns answers grounded in the actual legal text,
with the source country and document cited.

**Why this knowledge is valuable:** Organizations operating across borders must comply with
each jurisdiction's data-protection regime, and the rules differ in ways that carry real legal
and financial consequences (e.g., Zambia requires breach notification within 24 hours and
mandates in-country storage of sensitive data, while other regimes do neither). A
practitioner needs to find the *specific* governing provision for a *specific* country quickly.

**Why it's hard to find through official channels:** The primary sources are scattered across
dozens of separate government portals, gazettes, and third-party aggregators, each in its own
PDF format and layout. Many are scanned documents with OCR noise, and there is no single
searchable index that lets you compare provisions across jurisdictions. Official sites let you
*download* a country's act but not *ask a question* across the whole corpus — so answering
"how does Kenya's erasure right differ from Mauritius'?" normally means manually reading two
long statutes. This RAG system consolidates that scattered, hard-to-search material into one
queryable, citable interface.

---

## Document Sources

<!-- List every source you collected documents from.
     Be specific: include URLs, subreddit names, forum thread titles, or file names.
     Aim for variety — sources that together cover different subtopics or perspectives. -->

**Sources actually loaded in the current corpus** (`country_plus_policies.csv`, 218 rows → 2,000
chunks). Only these 5 jurisdictions are present in the data the system queries:

| # | Source | Type | URL or file path |
|---|--------|------|-----------------|
| 1 | Poland | Data Protection Law | https://uodo.gov.pl/en/file/754 |
| 2 | Lesotho | Data Protection Act 2011 | https://www.centralbank.org.ls/images/Legislation/Principal/Data_Protection_Act_2011.pdf |
| 3 | Zambia | Data Protection Act, 2021 (No. 3 of 2021) | https://www.parliament.gov.zm/sites/default/files/documents/acts/Act%20No.%203%20The%20Data%20Protection%20Act%202021_0.pdf |
| 4 | Iceland | Data Protection Law | https://www.dlapiperdataprotection.com/system/modules/za.co.heliosdesign.dla.lotw.data_protection/functions/handbook.pdf?country-1=IS |
| 5 | United States of America | Computer Fraud and Abuse Act | https://www.energy.gov/sites/prod/files/cioprod/documents/ComputerFraud-AbuseAct.pdf |

**Planned but NOT in the current dataset.** These five were listed in planning.md as intended
sources but were not included in the loaded CSV. They are documented here for transparency
because the evaluation set assumed them; questions targeting these jurisdictions (e.g. Kenya vs
Mauritius) currently cannot be answered and the system correctly refuses:

| # | Source | Type | URL or file path |
|---|--------|------|-----------------|
| 6 | Kenya | Data Protection Act, 2019 (No. 24 of 2019) | https://www.kentrade.go.ke/wp-content/uploads/2022/09/Data-Protection-Act-1.pdf |
| 7 | Nigeria | Nigeria Data Protection Act, 2023 | https://cert.gov.ng/ngcert/resources/Nigeria_Data_Protection_Act_2023.pdf |
| 8 | Ghana | Data Protection Act, 2012 (Act 843) | https://ghalii.org/akn/gh/act/2012/843/eng@2012-05-18 |
| 9 | Uganda | Data Protection and Privacy Act, 2019 | https://ict.go.ug/wp-content/uploads/2019/03/Data-Protection-and-Privacy-Act-2019.pdf |
| 10 | Mauritius | Data Protection Act 2017 (Act No. 20 of 2017) | https://natlex.ilo.org/dyn/natlex2/natlex2/files/download/108724/MUS108724.pdf |

---

## Chunking Strategy

<!-- Describe your chunking approach with enough specificity that someone else could reproduce it.
     Include:
     - Chunk size (characters or tokens) and why that size fits your documents
     - Overlap size and why (or why not) you used overlap
     - Any preprocessing you did before chunking (e.g., stripping HTML, removing headers)
     - What your final chunk count was across all documents -->

**Chunk size:** 450 characters (sentence-boundary aware).

**Overlap:** 75 characters.

**Why these choices fit your documents:** The embedding model (`all-MiniLM-L12-v2`)
truncates input at **128 tokens** — roughly 450–500 characters of English. My source
documents are long legal/regulatory texts (the `Body` field of each row often runs to
1,000+ characters), so embedding the whole field meant everything past the first ~128
tokens was silently discarded before embedding. In practice this meant only the opening
of each policy — frequently a table-of-contents header — was ever represented in the
vector store, which is why early retrieval returned section-listing fragments instead of
substantive rules. Setting the chunk size to 450 characters keeps each chunk safely under
the model's token ceiling so the *entire* policy text gets embedded. The 75-character
overlap preserves clauses/sentences that straddle a chunk boundary, so a rule split across
two chunks still embeds coherently in at least one of them. Preprocessing: I normalize
whitespace and split on sentence boundaries (`. `) rather than cutting at a fixed offset,
so chunks don't end mid-sentence (unless a single sentence exceeds the window).

**Final chunk count:** 2,000 chunks across 218 source policies.

---

## Sample Chunks

<!-- At least 5 labeled sample chunks, each with its source document name. -->

Five representative chunks straight from the Chroma collection (chunk IDs follow the
`row{row}_chunk{n}` scheme; text is whitespace-normalized as stored):

**Chunk 1 — Source: Zambia, Data Protection Act 2021** *(id `row3_chunk0`)*
> part x transfer of personal data outside the republic 70. crossborder transfer of personal
> data 71. conditions for crossborder transfer of personal data part xi general provisions 72.
> right to compensation 73. offences 74. power of data protection commissioner to compound
> certain offences 75. forfeiture 76. offence by …

**Chunk 2 — Source: Zambia, Data Protection Act 2021** *(id `row30_chunk0`)*
> (c) data being processed, as well as the source of that data; and (d) information about the
> basic logic involved in any automatic processing of data relating to the data in case of
> automated decision making. (3) a data subject has the right to notification of all third
> parties to whom that data subject's personal data has …

**Chunk 3 — Source: Lesotho, Data Protection Act 2011** *(id `row60_chunk0`)*
> 266 (a) (b) process such information only with the knowledge or authorisation of the data
> controller; and treat personal information which comes to their knowledge as confidential and
> shall not disclose it, unless required by law or in the course of the performance of their
> duties. the commission; and the data subject …

**Chunk 4 — Source: Iceland, Data Protection Law** *(id `row120_chunk0`)*
> the act on scientific research in the health sector governs approvals of scientific research in
> the health sector. chapter vi data protection officers and certification bodies. article 35
> data protection officers. the controller and the processor shall designate a data protection
> officer in every case where: 1. the pro…

**Chunk 5 — Source: Poland, Data Protection Law** *(id `row200_chunk0`)*
> chapter vii cooperation and consistency section 1 cooperation article 60 cooperation between
> the lead supervisory authority and the other supervisory authorities concerned 1. the lead
> supervisory authority shall cooperate with the other supervisory authorities concerned …

*Observation:* chunks 1 and 5 are structural/section-listing text, while 2–4 are substantive
provisions. This mix is expected given the source PDFs include tables of contents, and it is
relevant to the Failure Case Analysis — section-listing chunks can rank highly on
structurally-phrased queries.

---

## Embedding Model

<!-- Name the embedding model you used and explain your choice.
     Then answer: if you were deploying this system for real users and cost wasn't a constraint,
     what tradeoffs would you weigh in choosing a different model?
     Consider: context length limits, multilingual support, accuracy on domain-specific text,
     latency, and local vs. API-hosted. -->

**Model used:** `all-MiniLM-L12-v2` (Sentence-Transformers), producing 384-dimensional
embeddings. I run it locally and Chroma uses the same model to embed both documents and
queries. I configured the Chroma collection with cosine similarity (`hnsw:space: cosine`)
since these are normalized sentence embeddings.

**Production tradeoff reflection:** `all-MiniLM-L12-v2` is small, fast, and free to run
locally, which is ideal for a course project — but its **128-token context window** is the
biggest limitation for this domain. Legal/regulatory text contains long, clause-heavy
sentences, and a 128-token ceiling forced aggressive chunking (450 chars), which fragments
rules that naturally span more context. If cost weren't a constraint and I were deploying
for real users, I'd weigh:
- **Context length:** a model with a 512+ token window (e.g. `all-mpnet-base-v2`, ~768-dim)
  or an API-hosted embedding model with thousands of tokens of context would let me use
  larger, more semantically complete chunks — fewer mid-rule splits, better retrieval of
  multi-sentence provisions.
- **Accuracy on domain text:** legal language is specialized; a larger general model or one
  fine-tuned on legal/regulatory corpora would likely separate near-duplicate provisions
  (e.g. distinguishing one country's breach-notification rule from another's) more reliably.
- **Multilingual support:** these policies originate from many countries; a multilingual
  model (e.g. `paraphrase-multilingual-mpnet-base-v2`) would handle non-English source text
  if I expanded beyond English-translated documents.
- **Latency / local vs. API:** local MiniLM is the lowest-latency, lowest-cost option and
  keeps data on-device. An API-hosted model adds per-call latency, cost, and a data-egress
  consideration, traded for higher quality and longer context — worth it for accuracy-
  critical compliance use, less so for an interactive demo.

---

## Retrieval Test Results

<!-- At least 3 queries, each with the top returned chunks; explain relevance for at least 2. -->

Three queries run through `retrieve()`, captured as the **pre-filter baseline** (top-3, 0.15
similarity floor, no country filter) to illustrate retrieval behavior — including the
cross-jurisdiction contamination that motivated the country metadata filter now in the system.
Chunk text is truncated for readability.

**Query A: "What is Iceland's data privacy policy?"**
| Rank | Country | Similarity | Chunk (truncated) |
|---|---|---|---|
| 1 | Iceland | 0.73 | "…each data subject or his or her representative has the right to lodge a complaint with…" |
| 2 | Iceland | 0.69 | "…security, national defence, state security … shall apply until directive (eu) 2016/680…" |
| 3 | Iceland | 0.68 | "…transfer of personal data to another country or international organisations. decisions of the commission…" |

*Why these are relevant:* All three chunks are from the Iceland document, and together they
cover core privacy-policy substance — the right to lodge a complaint, the scope/exemptions of
the law, and cross-border transfer rules. The query names a single jurisdiction with little
generic vocabulary, so the embedding cleanly matched Iceland's text. This is the system's
best-case behavior.

**Query B: "Within what timeframe must a security breach be reported in Zambia?"**
| Rank | Country | Similarity | Chunk (truncated) |
|---|---|---|---|
| 1 | Zambia | 0.58 | "…twenty-four hours of any security breach affecting personal data processed. (2) a data processor shall notify…" |
| 2 | Iceland | 0.57 | "…the personal data breach is unlikely to result in a risk to the rights and freedoms of natural persons…" |
| 3 | Poland | 0.55 | "…unless the personal data breach is unlikely to result in a risk to the rights and freedoms…" |

*Why these are (partly) relevant:* Rank 1 is exactly right — the Zambia chunk stating the
24-hour breach-notification window. But ranks 2 and 3 are **other countries'** breach
provisions that use near-identical GDPR-derived wording ("unlikely to result in a risk to the
rights and freedoms of natural persons"). This is a live demonstration of the cross-jurisdiction
contamination risk: the correct chunk wins, but two of three slots are spent on the wrong
jurisdiction. **The country metadata filter (since implemented) reclaims those slots** — re-running
this query with the filter returns only Zambia chunks.

**Query C: "What are the registration requirements for a data controller?"**
| Rank | Country | Similarity | Chunk (truncated) |
|---|---|---|---|
| 1 | Zambia | 0.69 | "…part v regulation of data controllers, data processors and data auditors 19. prohibition from controlling or processing…" |
| 2 | Zambia | 0.66 | "…registration in a prescribed manner and form on payment of a prescribed fee…" |
| 3 | Zambia | 0.66 | "…certificate of registration, if the applicant meets the prescribed requirements…" |

(Relevance: all three are Zambia's Part V registration provisions — a coherent, on-topic set.)

---

## Grounded Generation

<!-- Explain how your system enforces grounding — how does it prevent the LLM from answering
     beyond the retrieved documents?
     Describe both your system prompt (what instruction you gave the model) and any structural
     choices (e.g., how you formatted the context, whether you filtered low-relevance chunks).
     Do not just say "I told it to use the documents" — show the actual instruction or explain
     the mechanism. -->

**System prompt grounding instruction:** The generation step (`rag_query.py`) uses this exact
system prompt:

> You are a regulatory-compliance assistant. Answer the user's question USING ONLY the numbered
> context passages provided. Do not use outside knowledge. If the context does not contain the
> answer, reply exactly: "I don't have enough information in the provided documents to answer
> that." Cite the passages you used with their country name and bracket number, e.g.
> (Iceland [1]). Be concise and factual.

Three things enforce grounding beyond the instruction itself:
1. **Closed-book framing** — "USING ONLY the numbered context passages" + "Do not use outside
   knowledge" tells the model the retrieved passages are its only source of truth.
2. **An explicit refusal path** — a fixed sentence the model must return when the context is
   insufficient. This is what makes failure *visible* instead of hallucinated: in evaluation,
   questions whose supporting text wasn't retrieved (or whose source documents aren't in the
   corpus, e.g. Q4) produced this refusal rather than a made-up answer.
3. **Low temperature (0.2)** — keeps the model from drifting into fluent-but-unsupported
   elaboration.

**Structural choices:** Retrieved chunks are formatted into a *numbered* context block, each
line prefixed with `[n] Country: … | Source: … | URL: …` before the chunk text, so the model
can cite by number and country. I also **filter low-relevance chunks**: `retrieve()` converts
each cosine distance to a similarity score and drops anything below `MIN_SIMILARITY = 0.15`, so
weak matches are never presented to the model as if they were evidence.

**How source attribution is surfaced in the response:** Two layers. (1) The LLM cites inline by
country + bracket number, e.g. *"...within twenty-four hours (Zambia [1])"*. (2) The `ask()`
function returns a separate `sources` list — `[1] Zambia (similarity 0.70) — <URL>` — which the
Gradio UI renders in a dedicated **"Retrieved from"** pane, so the user always sees which
documents (and how strongly they matched) backed the answer, independent of the model's prose.

---

## Example Responses

<!-- At least 2 responses with source attribution visible, plus one out-of-scope refusal. -->

**Example 1 — in-scope (single jurisdiction).**
Q: *"What is Iceland's Data Privacy Policy?"*
> Iceland's Data Privacy Policy includes the right of each data subject to lodge a complaint with
> the data protection authority if they believe their personal data is being processed in a way
> that infringes the regulation **(Iceland [1])**. The policy also includes the right to have
> inaccurate, misleading, or incomplete personal data rectified **(Iceland [2])**. Additionally,
> the policy regulates the transfer of personal data to another country or international
> organizations, with decisions made by the Commission applicable in Iceland **(Iceland [3])**.
>
> Retrieved from:
> • [1] Iceland (similarity 0.73) — https://www.dlapiperdataprotection.com/...?country-1=IS
> • [2] Iceland (similarity 0.69) — https://www.dlapiperdataprotection.com/...?country-1=IS
> • [3] Iceland (similarity 0.68) — https://www.dlapiperdataprotection.com/...?country-1=IS

**Example 2 — in-scope (registration rules).**
Q: *"What are the registration requirements for a data controller?"*
> The registration requirements for a data controller are not explicitly stated in the provided
> passages. However, a certificate of registration is issued if the applicant meets the
> "prescribed requirements" **(Zambia [3])**. The process for registration is outlined in
> sections 20 and 21 **(Zambia [1])**, and registration is done "in a prescribed manner and form
> on payment of a prescribed fee" **(Zambia [2])**.
>
> Retrieved from:
> • [1] Zambia (similarity 0.69) — https://www.parliament.gov.zm/.../Act%20No.%203...2021_0.pdf
> • [2] Zambia (similarity 0.66) — https://www.parliament.gov.zm/.../Act%20No.%203...2021_0.pdf
> • [3] Zambia (similarity 0.66) — https://www.parliament.gov.zm/.../Act%20No.%203...2021_0.pdf

Note how the model honestly hedges ("not explicitly stated…however") and attributes every claim
to a numbered Zambia source rather than inventing specifics.

**Example 3 — out-of-scope (refusal).**
Q: *"What is the best recipe for chocolate chip cookies?"*
> I don't have enough information in the provided documents to answer that.
>
> Retrieved from:
> • [1] Poland (similarity 0.17)

The corpus has no relevant content, so only one weak chunk (similarity 0.17) clears the filter,
and the grounding prompt forces the fixed refusal instead of the model answering from general
knowledge — exactly the desired behavior for a compliance assistant.

---

## Query Interface

<!-- Describe input/output fields and a sample interaction transcript. -->

The interface is a **Gradio web app** (`app.py`), launched with `python app.py` and served at
http://localhost:7860.

**Input field:**
- *Your question* — a free-text box where the user types a natural-language question (Enter or
  the **Ask** button submits). A set of clickable **example questions** is provided so a viewer
  immediately understands how to use it.

**Output fields:**
- *Answer* — the grounded, citation-bearing answer text from the LLM (8-line box).
- *Retrieved from* — the list of source chunks that backed the answer, each line showing the
  country, similarity score, and document URL (4-line box), so attribution is always visible
  independent of the answer prose.

**Sample interaction transcript:**
```
[User types in "Your question"]:  What is Iceland's Data Privacy Policy?
[User clicks "Ask"]

[Answer]:
  Iceland's Data Privacy Policy includes the right of each data subject to lodge a
  complaint with the data protection authority ... (Iceland [1]). The policy also
  includes the right to have inaccurate, misleading, or incomplete personal data
  rectified (Iceland [2]) ... transfer of personal data to another country ... (Iceland [3]).

[Retrieved from]:
  • [1] Iceland (similarity 0.73) — https://www.dlapiperdataprotection.com/...?country-1=IS
  • [2] Iceland (similarity 0.69) — https://www.dlapiperdataprotection.com/...?country-1=IS
  • [3] Iceland (similarity 0.68) — https://www.dlapiperdataprotection.com/...?country-1=IS
```

---

## Evaluation Report

<!-- Run your 5 test questions from planning.md through your system and record the results.
     Be honest — a partially accurate or inaccurate result that you explain well is more
     valuable than a suspiciously perfect result. -->

Results below are with the **country metadata filter enabled and top-k = 5** (per named
jurisdiction). See the note after the table for how these changed from the pre-filter baseline.

| # | Question | Expected answer | System response (summarized) | Retrieval quality | Response accuracy |
|---|----------|-----------------|------------------------------|-------------------|-------------------|
| 1 | Zambia breach-notification timeframe? | Within 24 hours (Section 49(1)). | "A data controller must notify the Commissioner within twenty-four hours of any security breach (Zambia [1], [2])." | Relevant (all chunks Zambia) | **Accurate** |
| 2 | Does Zambia impose data localization; is sensitive data treated differently? | Yes — Section 70 requires in-country storage; sensitive data must always stay in Zambia. | "Zambia's Act does not explicitly impose data localization… sensitive data transfer requires explicit consent (Zambia [5])." | Relevant jurisdiction, but the Section 70 storage-mandate chunk did not surface for this phrasing | **Partially accurate / inaccurate** — engages the transfer rules but wrongly says localization isn't imposed |
| 3 | "Child" age under Lesotho 2011 vs Zambia? | Lesotho: under 18 (fixed); Zambia: per its Constitution (no number). | Refused with the fixed no-answer string. | **Relevant** — now retrieves both Lesotho *and* Zambia chunks (filter working) | Inaccurate (no answer) — honest refusal; the specific child-age definition chunk (OCR-garbled) wasn't retrieved |
| 4 | Erasure/portability differences: Kenya 2019 vs Mauritius 2017? | (Unanswerable — neither country is in the loaded corpus.) | Refused with the fixed no-answer string. | N/A — no Kenya/Mauritius documents exist in the dataset | **Correct refusal** — the system rightly declines rather than fabricating |
| 5 | Which laws have a dedicated enforcement authority; what is Zambia's called? | Office of the Data Protection Commissioner (Section 4). | "Zambia's authority is the Zambia Information and Communications Technology Authority (Zambia [1])." | Relevant jurisdiction, but ranks the defined-term "authority"=ZICTA chunk above the Section 4 chunk | **Inaccurate** — confidently wrong (named ZICTA, not the Office of the Data Protection Commissioner) |

**Summary:** 1 of 5 fully correct (Q1) and 1 correct refusal of out-of-corpus data (Q4). The
country metadata filter **eliminated cross-jurisdiction contamination** — Q1/Q2/Q5 now retrieve
only the named country, and Q3 retrieves both named jurisdictions — but it did **not** raise the
raw accuracy score, because the remaining failures are not retrieval-routing problems:
- **Q2** flipped from an honest refusal to a *partially incorrect* answer: with k=5 it now finds
  cross-border-transfer text but not the Section 70 storage mandate, so it wrongly concludes
  localization "isn't imposed." (A confident partial answer is arguably worse than the prior
  refusal — a tradeoff of widening k.)
- **Q3** is now a **data-quality** failure: the filter correctly surfaces Lesotho chunks, but the
  chunk defining a child's age is OCR-corrupted ("1b yeus" for "18 years"), so it doesn't embed
  near the query and never reaches the model.
- **Q4** is a **coverage** failure: Kenya and Mauritius were never loaded, so the refusal is the
  correct behavior.
- **Q5** is a **defined-term collision**: the Act defines the word "authority" to mean ZICTA, so
  chunks containing "authority" outrank the Section 4 chunk that actually names the *Office of the
  Data Protection Commissioner*.

**Retrieval quality:** Relevant / Partially relevant / Off-target  
**Response accuracy:** Accurate / Partially accurate / Inaccurate

---

## Failure Case Analysis

<!-- Identify at least one question where retrieval or generation did not work as expected.
     Write a specific explanation of *why* it failed, tied to a part of the pipeline.

     "The answer was wrong" is not an explanation.

     "The relevant information was split across a chunk boundary, so retrieval returned
     only half the context — the model didn't have enough to answer correctly" is an explanation.

     "The embedding model treated the professor's nickname as out-of-vocabulary and returned
     results from an unrelated review" is an explanation. -->

**Question that failed:** "Which of these laws establishes a dedicated enforcement authority, and
what is Zambia's called specifically?" (Evaluation Q5.) This failure *persists even after* adding
the country metadata filter, which makes it the most instructive case.

**What the system returned:** A confident but **wrong** answer — "Zambia's dedicated enforcement
authority is the Zambia Information and Communications Technology Authority (ZICTA)." The correct
answer is the **Office of the Data Protection Commissioner** (established in Section 4 of the
Act). The retrieved chunks were correctly all-Zambia (the filter worked), but the top-ranked
chunk was the Act's *definitions* section.

**Root cause (tied to a specific pipeline stage): the retrieval ranking stage, via a defined-term
collision.** Zambia's Act contains a definition clause: *"authority means the Zambia Information
Communications and Technology Authority…"*. The query uses the word "authority," so this
definitions chunk embeds extremely close to the query and ranks #1 — above the Section 4 chunk
that actually establishes the *Office of the Data Protection Commissioner*. The grounding worked
(the model only used retrieved text and cited it), but it was handed a chunk where the word
"authority" refers to a *different, telecoms* body. I confirmed the correct chunk exists and ranks
within the top ~8 for a reworded query, so this is a ranking/precision problem, not a missing-data
problem. Notably, the metadata filter — which fixed cross-jurisdiction contamination elsewhere —
does **not** help here, because the collision is *within* a single jurisdiction's document.

**What you would change to fix it:** (1) Add a **reranking** step — retrieve a wider net (k=15–20
within the filtered jurisdiction) and rerank with a cross-encoder, which would weight the Section 4
"establishment" language over a definitions cross-reference. (2) **Exclude or down-weight
definitions/table-of-contents chunks** at ingestion (e.g., tag chunks that are section-listings or
defined-term glossaries) so they don't crowd out substantive provisions. (3) Carry a
`section_number` in metadata so an answer about "the enforcement authority" can prefer the
establishing section. The same definitions-chunk noise contributes to Q2's partial answer, so a
rerank + chunk-type tagging change would likely improve both.

---

## Spec Reflection

<!-- Reflect on how planning.md shaped your implementation.
     Answer both questions with at least 2–3 sentences each. -->

**One way the spec helped you during implementation:** The Anticipated Challenges section in
planning.md predicted "cross-jurisdiction contamination from near-identical GDPR-derived text"
*before* I wrote any retrieval code, and it named the defense: filter by country before the
vector search. When my evaluation run later produced exactly that failure (Q4 returned only
Zambia chunks for a Kenya/Mauritius question), I didn't have to guess at the cause — the spec
had already diagnosed it, so I could write a precise Failure Case Analysis and a concrete fix
rather than flailing. The spec turned a confusing result into an expected, explainable one.

**One way your implementation diverged from the spec, and why:** The spec called for
token-based, section-aware chunking (~512 target / 800 ceiling) using `all-MiniLM-L6-v2`. During
implementation I found the embedding model I actually loaded (`all-MiniLM-L12-v2`) truncates at
**128 tokens** — far below the planned chunk size — which meant any 512-token chunk would have
been silently cut off and most of each policy never embedded. I diverged to a **450-character,
sentence-boundary-aware** chunker sized to fit under that real token ceiling, prioritizing
"embed the whole document" over "respect section structure." A second, unplanned divergence
surfaced during evaluation: the loaded corpus contains only **5 of the 10** planned jurisdictions
(Kenya, Mauritius, Nigeria, Ghana, Uganda were never ingested), which is why one test question is
unanswerable. I have since implemented the planned **country metadata filter** and top-k = 5,
which removed cross-jurisdiction contamination — but the Failure Case Analysis shows the
remaining accuracy bottlenecks are data-quality (OCR) and within-document ranking (defined-term
collisions), not jurisdiction routing, which is where I'd invest next (reranking + chunk-type
tagging + an OCR cleanup pass).

---

## AI Usage

<!-- Describe at least 2 specific instances where you used an AI tool during this project.
     For each: what did you give the AI as input, what did it produce, and what did you
     change, override, or direct differently?

     "I used Claude to help me code" is not sufficient.
     "I gave Claude my Chunking Strategy section from planning.md and asked it to implement
     chunk_text(). It returned a function using a fixed character split. I overrode the
     chunk size from 500 to 200 because my documents are short reviews, not long guides." -->

**Instance 1 — Migrating off LangChain and fixing the embedding pipeline**

- *What I gave the AI:* My initial `Embedding_Setup.py`, which used LangChain wrappers
  (`HuggingFaceEmbeddings`, `Chroma.from_documents`), and the `ModuleNotFoundError: No module
  named 'langchain'` traceback. I asked it to make the script run against my actual
  `requirements.txt` (which lists `sentence-transformers` and `chromadb`, not LangChain).
- *What it produced:* A rewrite using the native chromadb API — `SentenceTransformerEmbeddingFunction`,
  `PersistentClient`, and `collection.add/upsert` — and it identified that several errors
  (`Chroma`, `similarity_search_with_scores`) were LangChain-only methods that don't exist in
  native chromadb. It also wired the CSV in with pandas.
- *What I changed or overrode:* I directed it to switch the distance space to **cosine** and to
  surface similarity (not raw distance) in the output. I also kept the design split into a
  separate ingestion script vs. query module rather than one file, because re-embedding 218
  policies on every query would be wasteful.

**Instance 2 — Diagnosing bad retrieval and setting the chunk size**

- *What I gave the AI:* The symptom that retrieval kept returning table-of-contents fragments
  instead of substantive rules, plus my planning.md Chunking Strategy (which specified ~512-token
  section-aware chunks).
- *What it produced:* It checked the embedding model's actual limit (`model.max_seq_length`) and
  found `all-MiniLM-L12-v2` truncates at **128 tokens** — meaning my planned 512-token chunks
  would have been silently cut off, so only the opening of each policy was ever embedded. It then
  implemented a `chunk_text()` using a 450-character, sentence-boundary-aware window with 75-char
  overlap, taking 218 policies to 2,000 chunks.
- *What I changed or overrode:* I accepted the character-based chunker as a pragmatic fit to the
  128-token ceiling, overriding my own spec's token-based section chunking — but I flagged this as
  a deliberate divergence (see Spec Reflection) and noted that section-aware chunking remains the
  better long-term approach if I move to a longer-context embedding model.
