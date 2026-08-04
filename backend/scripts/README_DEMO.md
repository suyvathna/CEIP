# Testing CEIP in ten minutes

```bash
cd backend
python -m scripts.seed_demo
```

That builds one realistic job — *NR6 Skun – Kampong Cham Widening* — in a
state where every screen has exactly one thing worth looking at. Run it as
many times as you like; each run makes its own project and touches nothing
else.

Then follow this, in order. It should take about ten minutes.

---

## The one idea

The platform answers three questions, and everything on screen belongs to
one of them:

| Question | Where | Which engine |
|---|---|---|
| What paperwork do I owe this month? | **Compliance** tab | A — *always do* |
| Something happened. What clock just started? | **Claims / Variations / Determinations** tabs | B — *do-in-case* |
| What is closest to hurting me right now? | **Deadlines** (top bar) and the **bell** | both |

If you only ever look at one screen, look at **Deadlines**.

---

## The walk-through

**1 · Deadlines (top bar).** Everything live across every project, soonest
first. Two red chips at the top: a Notice of Dissatisfaction closing in 3
days, and a Sub-Clause 3.5 notice outstanding. Everything else is amber.
Use the *Engine A / Engine B* chips to split routine paperwork from running
clocks.

> **What to check:** red = you lose a right if you miss it. Amber = a
> breach you can put right. Nothing routine can ever be red.

**2 · The bell (top right).** The same information ranked worst-first, and
it says *"2 event-driven clocks (B), 7 routine compliance (A)"*. Click any
alert — it takes you straight to the record.

**3 · Open the demo project → Compliance tab.** This is Engine A: 23 live
obligations plus an 18-item pre-CEIP backlog, clearly separated. The
backlog is everything that fell due before the job was entered into the
system — kept so you can record or waive it, but it does not shout at you.

> **Try it:** open *Contract milestones & periods*, set a **Taking-Over
> Certificate** date, save. Every close-out deadline (14.10 Statement at
> Completion, the DNP, 14.11 Final Statement) appears, and the monthly
> obligations after that date retire. Now clear the date again — they come
> back. Press *Recalculate this project* and it tells you exactly what
> changed.

**4 · Claims tab → CLM-001.** The Engineer has determined it: 11 days
allowed against 24 claimed. Scroll to **Sub-Clause 3.7**.

> **This is the point of the whole platform.** The Engineer's letter was
> dated 27 days ago and reached site 25 days ago. The 28-day objection
> window runs from *receipt*, so there are 3 days left, not 1. Miss it and
> the 11 days become final and binding — not appealable to the DAAB, not in
> arbitration. Record a Notice of Dissatisfaction and watch the red alert
> clear immediately.

**5 · Variations tab → VO-001.** A drawing revision that thickens the base
course by 50 mm, issued under a routine transmittal with the word
"Variation" nowhere in it. Sub-Clause 3.5 requires notice *immediately and
before any related work starts*.

> **Try it:** edit it and tick *work has already started*. The clock stops
> saying "5 days left" and says **missed** — because under 3.5 it is,
> whatever the calendar says.

**6 · Events tab → EVT-001.** Soft clay found below formation 20 days ago.
Sub-Clause 4.12, notice due in 8 days, no claim raised yet. This is the gap
where entitlements quietly die — an event logged, everyone means to think
about it, and 28 days later the right is gone.

---

## What to judge it on

Not the number of screens. These three things:

1. **Would it have caught something you have actually lost money on?**
   (The 3.7.5 window and the 3.5 notice are the two designed for that.)
2. **Is the red/amber line drawn in the right place** for how your
   contracts actually run?
3. **Is the alert volume liveable** — would you still be reading the bell
   in week three?

If the answer to 3 is no, say so. Alert volume is a setting
(*Alert lead time* on the Compliance tab), and any rule that doesn't apply
to your contracts can be waived permanently.
