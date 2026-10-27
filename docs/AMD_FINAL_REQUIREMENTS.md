# AMD Match 4 final requirements record

**Checked:** 2026-10-27 (Asia/Karachi)  
**Competition:** AMD AI League — Match 4: Intelligent Web Information Retrieval  
**Official event page:** https://lablab.ai/ai-hackathons/amd-lablab-ai-academy-challenge

## Verified from organizer pages

| Item | Verified rule or fact | Source |
|---|---|---|
| Match objective | Build an AI agent that navigates websites, understands a natural-language request, and accurately retrieves the specific information needed. | Official event page, Match 4 section |
| Match window | Match 4 is listed as Oct 13–Oct 27, 2026 and live submissions are shown on the event dashboard. | Official event page and `/live` dashboard |
| Participation | The league page says individual participation; the getting-started guide also permits a solo team. | Official event page; https://lablab.ai/getting-started-guide |
| Submission location | Projects are submitted from the participant team page before the deadline. | https://lablab.ai/getting-started-guide |
| Standard submission fields | Title, short description, long description, categories/technologies, participation mode where applicable, GitHub repository, demo platform, and demo URL. | https://lablab.ai/delivering-your-hackathon-solution |
| Standard presentation materials | Video presentation (MP4/MOV, up to 300 MB, recommended under 5 minutes) and slide presentation PDF are required by default. | https://lablab.ai/delivering-your-hackathon-solution; https://lablab.ai/hackathon-rules |
| Description limits | Title: 5–50 characters; short description: 50–255 characters; long description: 600–2000 characters. | https://lablab.ai/delivering-your-hackathon-solution |
| Repository visibility | A public GitHub repository is recommended/required by the standard guide so judges can review the code. | https://lablab.ai/delivering-your-hackathon-solution; https://lablab.ai/hackathon-rules |
| Deadline behavior | The rules state submissions close at the event deadline with a five-minute grace period; technical problems should be reported to organizers before the deadline. | https://lablab.ai/hackathon-rules |

## Not published or not confirmed

- No Match 4 starter-kit download was exposed by the retrieved event page.
- No official Match 4 input/output schema, stdin/stdout contract, grader entrypoint, or sample cases were exposed.
- No Match 4-specific Docker base image, ROCm version, GPU model, execution budget, or container invocation was exposed.
- No Match 4-specific network policy, external API allowlist, model-license policy, or TinyFish requirement was exposed.
- The event page does not specify whether a hosted demo URL is mandatory for this particular match beyond the standard submission guide.
- The organizer's form may add fields or change defaults; the live submission form and event page take precedence over this record.

## Engineering consequence

The project preserves its internal JSON/HTTP contract and keeps `app/evaluation/amd_adapter.py` fail-closed. It must not claim official grader compatibility until the actual Match 4 contract is supplied by the organizer or appears in the submission form.
