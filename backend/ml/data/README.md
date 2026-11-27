# Career Compass pilot labels

`pilot_profiles.json` contains 44 fictional profiles in 22 scenario families. The cases cover six countries and five broad education stages: school, senior secondary, diploma/technical, undergraduate, and postgraduate. Career labels use titles from `backend/seed_data.py`. The examples and labels were written for this pilot by the assistant. No student records, counselor judgments, admissions decisions, or career outcomes were used.

## Annotation rubric

Label each candidate using the fictional or consented profile, the career description, and the next education step. The ratings express relevance for exploration.

| Label | Meaning |
| --- | --- |
| `3` | Strong fit. The interests and evidence support a distinct path, with a realistic next step for the student's stage. |
| `2` | Credible option. The path has relevant evidence but the fit is less direct, the evidence is sparse, or further prerequisites need exploration. |
| `1` | Weak fit. A transferable interest or skill exists, with little evidence supporting this particular route. |
| `0` | Reviewed poor fit. There is a clear mismatch with the goals or evidence in this scenario. |

An absent title means the career has not been rated. Preserve that distinction when training and evaluating. A rating of `3` can describe a long-term aspiration. For example, a Matric student's strong science interest can make medicine worth exploring while their immediate next step is senior-secondary science study. Eligibility follows separately verified rules and official requirements.

`label_evidence` is an annotation note for review. Use only fields available at prediction time as features. Exclude `profile_id`, `group_id`, `labels`, and `label_evidence` from the feature vector. Group profiles that share a scenario, student, or near-duplicate variant under one `group_id` and keep the whole group in one split. `marks_cgpa` may be `null`; supported GPA scales are recorded in `study_preference`.

## Replace pilot labels with reviewed data

1. Build fictional or consented, de-identified profiles with relevant education stages and departments. Keep names, contact details, chat history, and account identifiers outside the training dataset.
2. Give reviewers the same rubric and catalog. Collect labels independently, record disagreements in a separate review log, and resolve them before freezing a dataset version.
3. Include several realistic alternative paths and several plausible negative candidates per profile. Reviewers should record uncertain cases explicitly or leave them unjudged.
4. Hold out whole scenario or student groups, including examples across each supported stage and region. Compare the model and rule-based baseline on the same judged candidates. Record which countries and stages have too little evidence to assess.
5. Keep reviewed examples in a separate versioned dataset with its own provenance and approval. Synthetic-pilot metrics describe agreement with authored scenarios and cannot establish production accuracy or eligibility.
