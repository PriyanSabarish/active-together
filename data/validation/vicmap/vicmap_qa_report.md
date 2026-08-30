# Vicmap Classification QA Report

## Purpose

This QA review evaluates whether the Vicmap subtype-to-category rules correctly
map sampled locations to the seven approved activity categories.

It does not verify opening hours, fees, accessibility, current facility
condition or suitability for a specific activity template.

## Method

The QA sample was generated reproducibly from the validated
`vicmap_app_ready.csv` dataset using random seed `5120`.

Up to 30 records were sampled from each activity category. Every available
record was included when a category contained fewer than 30 records. This
produced a stratified sample of 152 records across all seven categories.

Two reviewers assessed the same sample independently. A third reviewer resolved
the two records on which their decisions differed. The completed review evidence
is stored in `vicmap_qa_sample.csv`.

## Results

- Total reviewed records: 152
- Correct classifications: 151
- Incorrect classifications: 1
- Unresolved records: 0
- Overall sample accuracy: 99.34%
- Initial agreement between the two reviewers: 150 of 152 (98.68%)

### Results by category

| Activity category | Reviewed | Correct | Incorrect | Sample accuracy |
| --- | ---: | ---: | ---: | ---: |
| `court` | 30 | 30 | 0 | 100.00% |
| `park_and_garden` | 30 | 30 | 0 | 100.00% |
| `picnic_day_use` | 10 | 10 | 0 | 100.00% |
| `playground` | 30 | 30 | 0 | 100.00% |
| `skate_bmx` | 21 | 20 | 1 | 95.24% |
| `sports_ground` | 30 | 30 | 0 | 100.00% |
| `trail_access` | 1 | 1 | 0 | 100.00% |
| **Total** | **152** | **151** | **1** | **99.34%** |

## Final resolution

The two initial disagreements were resolved as follows:

- `sample_id 61`, Sculpture Lawn: the original `picnic_day_use`
  classification was retained.
- `sample_id 111`, Diggers Rest Recreation Reserve - Cycling Velodrome: the
  original `skate_bmx` classification was judged incorrect, and
  `sports_ground` was recorded as the final category.

The original category and both reviewer decisions remain in the QA sample to
preserve an audit trail.

## Interpretation

The result indicates that the subtype-to-category mapping is highly reliable
within this sample. The single incorrect result should be reviewed as a possible
rule issue before changing the production mapping. A QA decision does not by
itself modify `vicmap_app_ready.csv`.

If the team decides that the relevant subtype rule is systematically incorrect,
the change should be made in `vicmap_subtype_review.csv`, followed by rerunning
wrangling and validation.

## Limitations

This result measures classification accuracy within a stratified sample. It does
not establish that every Vicmap record is current or that every location is
free, publicly accessible, open at a particular time or appropriate for every
family activity.

The smallest categories have limited evidence. In particular, `trail_access`
contains only one reviewed record, so its 100% sample result should not be read
as a precise population-level estimate.
