# Location source inventory

Inspected on 2026-09-11. Source is the published CSV in the local fetched
`origin/data/iteration2-location-name-enrichment` snapshot at commit
`c969c41ce49e946cce71f1df0b4a5dddc8e85697`:

- Published file: `data/vicmap_app_ready.csv`
- Git blob: `6c90da9a6700754966b6cc0c7f3d6a7b69049703`
- Baseline: `data/processed/vicmap/vicmap_app_ready.csv`
- Evidence: that commit's `data/README.md` and
  `pipeline/run_name_enrichment_pipeline_README.md`

The enrichment runner validates the consolidated candidate and, with `--publish`,
replaces only the published file. The baseline remains unchanged. Published and
baseline data each contain 3,237 records. Comparing by place_id found 517 changed
display names and no changes to category, feature type, subtype or coordinates.
Enrichment did not add facilities or change the activity classification.

The content branch starts at `eb5def1` from dev and still has the pre-enrichment
published CSV (blob `f52c9e56c18229bb2cfda39824b1050f0a9233fd`). The inventory and
mapping read the enrichment commit directly, without merging data changes into
this branch. The same counts in both files do not prove they are the same version.

| Category | Feature type | Subtype | Places |
| --- | --- | --- | ---: |
| court | sport facility | basketball court | 79 |
| court | sport facility | netball court | 35 |
| court | sport facility | tennis court | 180 |
| park_and_garden | reserve | gardens | 5 |
| park_and_garden | reserve | park | 2039 |
| picnic_day_use | recreational resource | day visitor area | 1 |
| picnic_day_use | recreational resource | picnic site | 9 |
| playground | recreational resource | playground | 457 |
| skate_bmx | recreational resource | bmx track | 6 |
| skate_bmx | recreational resource | skate park | 15 |
| sports_ground | sport facility | athletic field | 18 |
| sports_ground | sport facility | baseball field | 19 |
| sports_ground | sport facility | hockey ground | 5 |
| sports_ground | sport facility | sports complex | 41 |
| sports_ground | sport facility | sports ground | 327 |
| trail_access | recreational resource | trailhead | 1 |
| **Total** | | **16 combinations, 7 categories** | **3237** |

Priyan's content uses provisional codes including cycling_track, walking_track,
reserve_and_bushland and waterway_and_foreshore. Those are not the seven retained
dataset categories. No automatic renaming or migration is performed here.

Reproduce the inventory from any working directory with Python 3.10+ and Git:

```text
python content/tools/inspect_location_taxonomy.py --ref c969c41ce49e946cce71f1df0b4a5dddc8e85697
```

Run the command from the repository root as shown, or use the script's absolute
path elsewhere. Omitting `--ref` inspects the current working-copy CSV and labels
it as such. The script outputs JSON to the terminal, uses only the Python standard
library and makes no file, branch or remote changes. The specified commit must
already be present locally.
