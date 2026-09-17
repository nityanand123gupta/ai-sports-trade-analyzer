# AI Multi-Agent Sports Trade Analyzer

A project that shows how a proposed NBA trade can be checked automatically
by a small team of specialist programs, each doing one job the way a
person in a team's front office would: looking up player data, rating
players, checking the trade against the league's spending rules, and
producing a final graded recommendation.

The whole project is two notebooks, meant to be taught or presented cell by
cell rather than run as a script.

## The two notebooks

| Notebook | What it is | Requirements |
|---|---|---|
| [`notebooks/01_trade_analyzer_core.ipynb`](notebooks/01_trade_analyzer_core.ipynb) | The complete engine, self-contained: data loading, a player value model based on age and stats, a salary-cap rules checker, and a final report generator. Plain, predictable code explained cell by cell with plots. | None. No account, no API key, no internet connection. |
| [`notebooks/02_agentic_crew_demo.ipynb`](notebooks/02_agentic_crew_demo.ipynb) | Loads notebook 1 and adds a real AI agent team on top, using [CrewAI](https://github.com/crewAIInc/crewAI): four AI agents reason over the same numbers to write a plain-language recommendation. | `pip install crewai` and a free `GEMINI_API_KEY` from [Google AI Studio](https://aistudio.google.com/apikey) (Anthropic's `ANTHROPIC_API_KEY` also works). Runs fine and explains itself without either. |

Start with notebook 1 — it's the complete story on its own. Notebook 2 is
the follow-up that shows how to add a real AI model on top.

## Why it's split this way

Notebook 1 makes the main point on its own: salary-cap math and trade
approval are exactly the kind of thing that should be handled by plain,
predictable code, not an AI model guessing at numbers. Notebook 2 then
shows where an AI model genuinely helps — writing explanations and weighing
judgment calls — once it's given numbers it can trust instead of being
asked to calculate them itself.

## Quick start

```bash
pip install -r requirements-notebook.txt
jupyter notebook notebooks/01_trade_analyzer_core.ipynb
```

Run the cells from top to bottom. Each specialist gets its own explanation
before the code that carries out its job.

Tip for presenting this: run one cell, pause on the explanation above it,
and let the audience guess the output before you run the next cell. The
notebook ends with an example of a trade that should not be allowed, plus a
few discussion questions.

## Running notebook 2 with a free API key

1. Get a free key at [Google AI Studio](https://aistudio.google.com/apikey)
   (no credit card required for the free tier).
2. Copy `.env.example` to `.env` and paste the key into `GEMINI_API_KEY`, or
   just set it in your shell:
   ```bash
   export GEMINI_API_KEY=your-key-here
   pip install crewai
   ```
3. Open and run `notebooks/02_agentic_crew_demo.ipynb`.

Already have an Anthropic key instead? Set `ANTHROPIC_API_KEY` and it will
be used automatically if no Gemini key is present.

## Data

`data/sample_players.json` is a small offline file with a few NBA teams'
rosters and approximate salaries/stats, used by both notebooks — no
internet connection needed. `data/cap_rules.json` holds the salary cap,
luxury tax, and spending-limit thresholds used by the rules checker.

> These figures and rules are simplified for teaching purposes. Check the
> official league rules before relying on this for anything real.

## How the salary-cap rules checker works

Notebook 1 implements a simplified version of the NBA's real spending
rules:

- **Under the cap** — a team can take back incoming salary up to its
  remaining room plus the outgoing salary.
- **Over the cap, including luxury-tax teams** — incoming salary must stay
  within a percentage of the outgoing salary (roughly 200%, 175%, or 125%
  depending on how much is being sent out).
- **First strict spending level** — can take back at most the outgoing
  salary plus $250,000, and cannot combine several outgoing players'
  salaries into one trade.
- **Second, strictest spending level** — cannot take back more salary than
  sent out at all, and also cannot combine outgoing salaries.

When a trade breaks these rules, the checker explains the problem and
suggests a specific fix (send out more salary) instead of just rejecting
the trade outright.

## Extending this project

- Replace the age-based value model with a trained machine-learning model.
- Add an agent that reads fan reaction to a rumored trade from social media.
- Add a negotiation simulation: two General Manager agents, one per team,
  counter-offer each other until they reach a deal.
- Connect the data-loading step to a live sports data service instead of
  the bundled sample file, or adapt the rules checker to another sport.
