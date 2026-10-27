# AMD requirements and uncertainty

Checked 2026-10-22. Source: [organizer event page](https://lablab.ai/ai-hackathons/amd-lablab-ai-academy-challenge).
The public Match 4 details link on this page did not expose a starter-kit download in the retrieved content.
This is not proof that a kit is unavailable elsewhere. No repeated kit search was performed.

| Classification | Requirement/fact | Evidence or decision |
|---|---|---|
| OFFICIAL | Match 4 is Intelligent Web Information Retrieval | Organizer 'Match 4' section |
| OFFICIAL | Match 4 ends October 27, 2026 | Organizer Match 4 status and live banner |
| OFFICIAL | Agent navigates websites and retrieves requested information | Organizer Match 4 challenge description |
| OFFICIAL | Match 4 offers 1,800 points | Organizer Match 4 points label |
| OFFICIAL | Participation is individual | Organizer league header |
| OFFICIAL | Closed matches remain open for points, without live-match prizes | Organizer prizes/Match 3 sections |
| ENGINEERING CHOICE | Python, LangGraph, LangChain, FastAPI, TinyFish, Playwright/httpx | User's implementation brief |
| ENGINEERING CHOICE | 30-second internal target, 8 pages, 2 hops | Configurable provisional engineering defaults |
| ENGINEERING CHOICE | Evidence-first extractive answers and abstention | Internal reliability strategy |
| ENGINEERING CHOICE | Current Answer JSON schema and JSONL CLI | Internal evaluation interface only |
| PROVISIONAL | Browser, retrieval and inference may need adaptation for grading | Deployment planning assumption |
| UNKNOWN | Official input/output schema and entrypoint | Starter kit/organizer confirmation required |
| UNKNOWN | Allowed external APIs, TinyFish access, network policy | Organizer confirmation required |
| UNKNOWN | Docker requirement, ROCm/local inference requirement, GPU model | Organizer confirmation required |
| UNKNOWN | Exact budgets, scoring rubric, allowed model licenses | Organizer confirmation required |
| UNKNOWN | Rules on pre-existing project code and required submission materials | Organizer confirmation required; this code was newly created |

No participant submission architecture is treated as an official requirement. Public event details
do not establish grader compatibility. The AMD adapter fails explicitly until the real contract is known.
