# Ranking Evaluation Dataset

CareerPilot does not claim ranking quality from synthetic examples.

Use JSON Lines (JSONL), one relevance judgment per line:
{"candidate_id":"<uuid>","job_id":"<uuid>","relevance":3,"label_source":"human_review"}

Relevance is ordinal:
- 0 — not relevant
- 1 — weak/partial relevance
- 2 — relevant
- 3 — highly relevant

Labels must have documented provenance. Do not populate the evaluation set with guessed labels just to produce attractive metrics.

Evaluation protocol:
1. Freeze the candidate profile version.
2. Freeze the job corpus/version and evaluation timestamp.
3. Run the same retrieval/ranking pipeline used by the product.
4. Compare ranked results against the relevance judgments.
5. Report Recall@K, MRR, and NDCG@K together with evaluation-set size and label provenance.
6. Keep tuning/training data separate from evaluation data.

Metrics from different datasets or label protocols must not be compared as directly equivalent.
