# HKU Recycling Rules Helper

HKU Recycling Rules Helper is a small, local command-line prototype that retrieves selected recycling guidance from a curated evidence file. The current version covers **a take-away coffee cup and its parts at the HKU re Kiosk**. For a supported question, it displays a stored plain-language answer and the original source text, source name, URL, and access date. When no sufficiently relevant record is found, or a configured hazardous-item term is detected, it refuses to give a direct classification.

> **Important scope note:** This is a terminal application, not a website or browser chatbot. It uses TF-IDF keyword retrieval and cosine similarity over `corpus.json`. It does **not** currently call an LLM or any API, and it does not require an API key. The corpus contains four records about one item type. Do not treat it as a general-purpose recycling guide.

## Quick start: reproduce the core workflow

These steps are the shortest way for a reviewer or a new user to check that the repository runs.

1. Download this repository as a ZIP using **Code → Download ZIP** from the [GitHub repository](https://github.com/WangYouzi-yugo/Ailt-9019-Group47).
2. Extract the ZIP. Open the extracted `Ailt-9019-Group47-main` folder, the one containing both `app.py` and `corpus.json`.
3. Open PowerShell in that folder. In File Explorer, open the folder, click the address bar, type `powershell`, and press Enter.
4. Check that Python is installed:

   ```powershell
   py --version
   ```

   If the command doesn't work, install Python from <https://www.python.org/downloads/>, then reopen PowerShell.

5. Run the demonstration question:

   ```powershell
   py app.py --ask "Can I recycle a take-away coffee cup at the HKU re Kiosk?"
   ```


## What should happen?

The output should start with `Answer:` and state that the cup's components should be separated. It should identify the clean lid as plastic recycling, the sleeve as paper recycling, and the clean cup as Tetra Pak recycling. It should also show `Original Reference:` and `Source:` with the official URL and recorded access date.

For reference, the current version's first answer line is:

```text
Answer: Yes, but the different components should be separated. The clean lid should be placed in plastic recycling, the cup sleeve in paper recycling, and the clean cup in Tetra Pak recycling. Note: this applies specifically to the HKU re Kiosk.
```

The later output should include a source link to `https://www.wastereduction.hku.hk/photo-guide` and `Accessed on: 2026-10-20`. This confirms the core path: **user input → local retrieval → answer with source evidence**.

## What this version can and cannot do

**It can:**

- Answer supported questions about the take-away coffee cup, its clean lid, its sleeve, and its clean cup body at the HKU re Kiosk.
- Display the stored answer and supporting source details so the user can check the official guidance.
- Refuse questions when the best retrieval score is too low or a configured hazardous-item term is detected.
- Run from local files without installing third-party Python packages or calling an online service.

**It cannot:**

- Classify all types of waste; the current corpus has only four coffee-cup-related records.
- Look up new or updated recycling rules online.
- Generate new answers with an LLM or use the course API key in this code version.
- Guarantee a correct refusal for every possible out-of-scope wording. Refusal terms and the similarity threshold are simple rules, so unexpected inputs still need testing.

An internet connection is only needed to open the external source page; the local query itself uses the files on your computer.


### A. Ask one question

**Windows PowerShell:**

```powershell
py app.py --ask "Can I recycle a take-away coffee cup at the HKU re Kiosk?"
```

**macOS / Linux:**

```bash
python3 app.py --ask "Can I recycle a take-away coffee cup at the HKU re Kiosk?"
```

Use the expected output described in **Quick start** to confirm that the answer, original reference, source URL and access date appear.

### B. Ask about the other covered parts

**Windows PowerShell:**

```powershell
py app.py --ask "coffee cup lid"
py app.py --ask "cup sleeve"
py app.py --ask "where does the coffee cup body go"
```

On macOS/Linux, replace `py` with `python3`.

| Input | Expected guidance at the HKU re Kiosk |
|---|---|
| `coffee cup lid` | Clean lid → plastic recycling |
| `cup sleeve` | Sleeve → paper recycling |
| `where does the coffee cup body go` | Clean cup body → Tetra Pak recycling |

### C. Use interactive mode

**Windows PowerShell:**

```powershell
py app.py
```

**macOS / Linux:**

```bash
python3 app.py
```

When the `>` prompt appears, type an item question and press Enter, for example `cup sleeve`. Enter more questions as needed. Type `exit` or `quit` to stop.

### D. Run the built-in refusal demonstration

**Windows PowerShell:**

```powershell
py app.py --demo
```

**macOS / Linux:**

```bash
python3 app.py --demo
```

The demo asks about a plastic bottle, batteries and a banana peel. Each should return a `[Refusal]` message because the current corpus has no supporting record for those items, and batteries match a configured hazardous-item term. This demo is a quick refusal check; it is not the complete 10-case test.

## Reproduce and check the 10 test cases

The project status material records a 10-input manual test on **23 October 2026**. The fixed version was re-run for this README on **24 October 2026**; all ten inputs produced the expected type of outcome. These are manual command-line regression checks, not an automated test suite: the repository does not currently include a `pytest` or `unittest` runner.

Run the following commands from the project folder. They can be pasted into Windows PowerShell to run the cases one after another:

```powershell
py app.py --ask "Can I recycle a take-away coffee cup at the HKU re Kiosk?"
py app.py --ask "coffee cup lid"
py app.py --ask "cup sleeve"
py app.py --ask "where does the coffee cup body go"
py app.py --ask "plastic bottle how to recycle"
py app.py --ask "glass jar"
py app.py --ask "paper"
py app.py --ask "what category does a banana peel belong to for recycling"
py app.py --ask "can batteries be put in recycling bins"
py app.py --ask "How do I dispose of a used battery?"
```

On macOS/Linux, replace `py` at the start of each command with `python3`.

| # | Test input | Expected result | Actual result observed on 24 Oct 2026 |
|---:|---|---|---|
| 1 | Full HKU re Kiosk coffee-cup question | Answer with the three component categories and source details | `Answer:`; lid = plastic, sleeve = paper, cup = Tetra Pak; source and access date shown. **PASS** |
| 2 | `coffee cup lid` | Answer: plastic recycling, with source details | `Answer:` gives plastic recycling; source shown. **PASS** |
| 3 | `cup sleeve` | Answer: paper recycling, with source details | `Answer:` gives paper recycling; source shown. **PASS** |
| 4 | `where does the coffee cup body go` | Answer: Tetra Pak recycling, with source details | `Answer:` gives Tetra Pak recycling; source shown. **PASS** |
| 5 | `plastic bottle how to recycle` | Refuse because there is no supporting corpus entry | Output begins `[Refusal]`. **PASS** |
| 6 | `glass jar` | Refuse because there is no supporting corpus entry | Output begins `[Refusal]`. **PASS** |
| 7 | `paper` | Refuse because there is no separate paper-item entry | Output begins `[Refusal]`. **PASS** |
| 8 | Banana-peel question | Refuse because there is no supporting corpus entry | Output begins `[Refusal]`. **PASS** |
| 9 | `can batteries be put in recycling bins` | Refuse because a configured hazardous-item stem is detected | Output begins `[Refusal]`. **PASS** |
| 10 | Used-battery question | Refuse because a configured hazardous-item stem is detected | Output begins `[Refusal]`. **PASS** |

The recorded evidence is in [`test_log.txt`](test_log.txt). The log contains the input, expected behaviour and observed result for each case. For a first-time check, supported inputs should begin with `Answer:` and show source details; unsupported or flagged hazardous inputs should begin with `[Refusal]`.

**Interpret the score carefully:** 10/10 means these ten preselected manual test inputs behaved as expected. It is not a general accuracy score, does not prove performance on unseen queries, and does not mean every kind of waste is supported. The known limitation is that only the coffee-cup-related records are in scope.

## How retrieval and refusal work

1. The app loads the local records from `corpus.json`.
2. It builds each searchable record from the item name at the beginning of the rule text (before the first colon), not from the whole rule paragraph.
3. It ignores general words such as `recycle`, `recycling`, `can`, and `how` because they do not identify the item.
4. It ranks the records using TF-IDF token weights and cosine similarity.
5. It refuses if the query contains one of the configured hazardous-item stems (for example, `batter` catches `battery` and `batteries`) or if the best similarity score is below `0.25`.
6. If a record is accepted, the stored answer and source metadata are displayed. The app does not generate new text using an LLM.

The fix addresses a bug found in the original version: matching against the full rule text allowed generic terms such as “recycling” or “plastic” to match an unrelated coffee-cup record. Matching only item names, filtering generic terms, checking hazardous-item stems and raising the minimum score from `0.12` to `0.25` reduced that error in the recorded 10-case test. It does not prove every unsupported query will always be refused.

## Official evidence and known limitation

**Source title:** *HKU Recycling 101 – Photo Guide*  
**Publisher:** HKU Sustainability, Sustainability Unit, Estates Office  
**Source URL:** <https://www.wastereduction.hku.hk/photo-guide>  
**Access date recorded in `corpus.json`:** 20 October 2026

The main demonstration input is:

> Can I recycle a take-away coffee cup at the HKU re Kiosk?

The stored source-based answer is to separate the parts: clean lid — plastic recycling; cup sleeve — paper recycling; clean cup — Tetra Pak recycling.

**Location limitation:** this guidance applies specifically to the HKU re Kiosk. Do not assume that the same recycling categories are available at every recycling facility on campus unless an official source confirms it. Users should check the cited source for the relevant location. The current four-record corpus does not cover bottles, glass jars, ordinary paper, food waste or general batteries.

## Current status and planned work

The midterm status sheet describes this version as a local TF-IDF retrieval prototype with four records about one item type. The following are future tasks, not features already implemented in this version:

- Expand the corpus to approximately 30 items from the HKU Recycling 101 Photo Guide and spot-check every record against its source.
- Add an LLM drafting step grounded only in the retrieved entry, with the stored answer as a fallback if the API is unavailable.
- Run a 30-case evaluation covering normal, ambiguous and unsupported queries; the status sheet sets a later target of at least 85% for that evaluation.
- Chinese queries, facility-location links and the full 100-case evaluation are deferred.

Owners, due dates, completion checks, blockers, scope decisions and each member's contribution belong in the required one-page status sheet. This README documents setup, the runnable core path and how to verify its result; it does not replace the status sheet.

## Files in this repository package

```text
Ailt-9019-Group47-main/
├── README.md                 # Setup, core workflow, tests and limitations
├── app.py                    # Command-line TF-IDF retrieval and refusal logic
└── corpus.json               # Four curated records with source metadata
```

For the course submission, the ZIP must also contain the **actual MP4 recording** (60 seconds or less) and the **completed one-page status sheet**, alongside `repository_link.txt`. `DEMO_VIDEO_SCRIPT.md` is a script, not the recording itself. Keep the submission ZIP under 100 MB, make sure teaching staff can access the repository, and check the exact Moodle cutoff.

## Repository

<https://github.com/WangYouzi-yugo/Ailt-9019-Group47>