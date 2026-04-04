# GenLayer Studio — UX Improvements

This folder documents real UX issues and platform limitations discovered while building four Intelligent Contracts on GenLayer Studio (studionet).

The contracts built and tested:
- Price Feed Oracle — crypto, forex and commodities
- Weather Oracle — live weather for 13 cities
- Social Media Oracle — Hacker News live data
- GenLayer Key Vault — secure private API key management

Everything in this document comes from real development experience — not theoretical issues.

---

## What Is Covered

**UX_IMPROVEMENTS.md** contains two sections:

**1. UX Issues** — eight problems encountered while using GenLayer Studio, each with a description of what happened, the impact on development, and a suggested fix for the GenLayer team.

**2. Known Limitations** — four platform-level limitations discovered while testing on GenLayer Studio, including which external APIs block GenLayer validator requests, how `gl.message.sender_account` behaves, and why `strict_eq` fails for live data fetches.

---

## Quick Reference

| Issue | Type | Priority |
|---|---|---|
| Schema error gives no detail | UX | High |
| Array input has no format example | UX | High |
| JSON responses show as raw text | UX | Medium |
| UNDETERMINED has no explanation | UX | High |
| Simulation Mode is easy to miss | UX | High |
| Upgrade code shows no confirmation | UX | Medium |
| Read methods do not auto-refresh | UX | Medium |
| APIs blocking GenLayer validators | Limitation | High |
| `gl.message.sender_account` unreliable | Limitation | High |
| `assert` not reverting transactions | Limitation | Medium |
| `strict_eq` fails for live data | Limitation | High |