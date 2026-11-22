---
name: agent-spec-grilling
description: Use when the user asks to be grilled or to clarify an idea, or when agent-spec-router or agent-spec-writer finds the context not yet actionable. Interviews the user until the idea becomes actionable items, and fills the lane's plan when one is needed.
---

# Agent Spec Grilling

Turn ideas into actionable items. Interview the user until every branch of the decision tree is resolved.

- **Rounds.** Ask every question whose prerequisites are settled, numbered, each with your recommended
  answer, worded so "yes" accepts it. Wait, fold the answers in, then ask the next round.
- **Facts are yours, decisions are theirs.** Look up anything the repo, `.specs/LAB.md` or the material
  answers; ask only what is the user's to decide.
- **Write as you go.** Each answer lands in the plan in the turn it arrives.

Done when the goal is stated, the way to prove it is known, and no open question would change the plan.
Hand back to whoever called you.
