# Sample Outputs (Provenance Demonstration)

These illustrate the exact shape of `AnswerResponse` (see
`src/generation/schema.py`) that `python -m src.pipeline "<question>"`
produces once `GEMINI_API_KEY` is configured and `python -m
src.ingestion.ingest` has been run. They are illustrative of the contract,
not a substitute for `eval/reports/eval_run_raw.json`, which contains the
actual per-question outputs from the most recent live evaluation run.

## Example 1 — Grounded answer with clause-level citation

**Question:** "What is the correct PPE doffing sequence and where must it occur?"

```json
{
  "answer": "Doff in this order: gloves, hand hygiene, gown, hand hygiene, eye protection, respirator, hand hygiene. Doffing must occur at the anteroom, not inside the patient room, except for the respirator.",
  "citations": [
    {"document": "SOP-IC-002", "clause_id": "4.3", "title": "Personal Protective Equipment (PPE) Donning and Doffing SOP"}
  ],
  "applicable_policy": "SOP-IC-002",
  "step_sequence": [
    "Remove gloves",
    "Perform hand hygiene",
    "Remove gown",
    "Perform hand hygiene",
    "Remove eye protection",
    "Remove respirator",
    "Perform hand hygiene"
  ],
  "responsible_role": "Infection Control Officer",
  "confidence": 0.95,
  "grounded": true,
  "abstained": false
}
```

## Example 2 — Multi-part question exercising query decomposition (AC-07)

**Question:** "What is the hand-hygiene protocol before a procedure, and who audits compliance with it?"

Sub-queries generated: `["hand-hygiene protocol before a procedure", "who audits hand-hygiene compliance"]`

```json
{
  "answer": "Before an invasive or aseptic procedure, staff must perform surgical hand antisepsis using a chlorhexidine-based scrub for a minimum of 2 minutes, followed by alcohol-based hand rub immediately before glove donning. Compliance is audited monthly by the Infection Control Officer using direct observation.",
  "citations": [
    {"document": "POL-IC-001", "clause_id": "3.4", "title": "Hand Hygiene Policy"},
    {"document": "POL-IC-001", "clause_id": "3.5", "title": "Hand Hygiene Policy"}
  ],
  "applicable_policy": "POL-IC-001",
  "step_sequence": [
    "Perform surgical hand antisepsis with a chlorhexidine-based scrub for at least 2 minutes",
    "Apply alcohol-based hand rub immediately before glove donning"
  ],
  "responsible_role": "Infection Control Officer",
  "confidence": 0.93,
  "grounded": true,
  "abstained": false
}
```

## Example 3 — Committed refusal example (abstention, AC-05)

**Question:** "What is the hospital's approved dosage range for intravenous vancomycin in pediatric patients?"

```json
{
  "answer": "I don't have enough grounded information in the committed hospital-policy corpus to answer this confidently. Please consult the relevant department directly or rephrase the question.",
  "citations": [],
  "applicable_policy": "",
  "step_sequence": [],
  "responsible_role": "",
  "confidence": 0.0,
  "grounded": false,
  "abstained": true
}
```

This exact object is `src.generation.schema.REFUSAL_EXAMPLE`, returned
whenever the deterministic code-level abstention check
(`_code_level_abstention_check`) or the model's own grounding assessment
determines the retrieved evidence is insufficient — satisfying the
Grounding & Advice Rule's requirement to prefer abstention over
hallucination.
