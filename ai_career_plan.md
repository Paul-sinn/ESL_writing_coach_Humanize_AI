# YOUR PERSONALIZED AI ENGINEER + CONSULTANT PLAN
### Built for: Non-CS background | US-based | Agentic AI + Consulting | 10-20 hrs/week
### Generated: 2026-04-14

---

> **NOTE:** Applied AI Researcher is not a 6-month goal from where you are right now.
> ML at 0, no CS background — researcher roles require deep ML theory, often a grad degree, and publications.
> Realistic $100K+ target: **AI Engineer + AI Consultant**.
> At 10-20 hrs/week, this is a **6-8 month plan**.

---

## SECTION 1: YOUR ARCHITECTURE LEARNING ROADMAP

### Your current position on the System 1 → System 2 spectrum:
You are currently at **Layer 3 only** — you know how to call an LLM, wire up tools, build routing logic, handle conversation state.
You have zero Layer 1 (ML prediction) and weak Layer 2 (decision logic with business rules). That's the gap between you and $100K.

---

### PHASE 1 — Understand what's actually happening inside your tools (Weeks 1-4)

- **Week 1:** Watch 3Blue1Brown's "Neural Networks" series (YouTube, free). Also watch his "Attention in transformers" video. Goal: conceptual intuition only — no need to understand every equation.
- **Week 2:** Watch Andrej Karpathy's "The spelled-out intro to neural networks" on YouTube. Build a neural net from scratch in Python. This is about hands-on understanding, not mathematical mastery.
- **Week 3:** Go back to every agent project you built and ask: "what is the LLM actually doing here? is it predicting? deciding? acting?" Map each project to the three layers. Write it down.
- **Week 4:** Read "Attention Is All You Need" paper — abstract and introduction only. Key takeaway: context window = memory. Everything in the context influences output.

### PHASE 2 — Build the missing layer (Weeks 5-8)

- **Week 5:** Fast.ai "Practical Deep Learning for Coders" (Lesson 1-3 only).
- **Week 6:** Learn the decision layer. Study basic business decision logic. Key formula: `Action = argmax(probability × business_value - cost_of_action)`
- **Week 7:** Take your online shopping website chatbot. Add a prediction layer: predict escalation probability. If > 70%, route to human agent. You've now built a three-layer system.
- **Week 8:** CS fundamentals you actually need: Big-O notation, hash maps, queues. Watch CS50's first 4 lectures (free, Harvard OpenCourseWare).

### PHASE 3 — Go deep on your niche (Weeks 9-12)

- Study eval frameworks for AI agents: LangSmith, Braintrust, or custom evals.
- Study multi-agent coordination patterns — read the actual LangGraph documentation end-to-end.
- Learn basic RAG architecture. Know enough to build it and know when NOT to use it.

---

## SECTION 2: YOUR SKILL VALUE AUDIT

**Formula: Skill Value = (Revenue Generated + Time Saved) × Scarcity**

### Current resume skills:

| Skill | Revenue | Time Saved | Scarcity | Verdict |
|-------|---------|------------|----------|---------|
| Automation workflow with AI agent | moderate | significant | LOW (500K+ people list this) | LOW as written |
| Orchestration | indirect | high | MEDIUM (growing fast) | MEDIUM — needs business outcome attached |
| Python agent architectures | indirect | indirect | LOW-MEDIUM (too generic) | LOW as written |
| Routing logic | moderate | significant | MEDIUM-HIGH if you go deeper | MEDIUM-HIGH |
| Role separation | indirect | indirect | LOW | LOW as standalone |

**THE REAL PROBLEM:** Every skill describes *how you built things*, not *what those things achieved*.
Reframe everything around outcomes, not tools.

### Skills you need to ADD:

**1. "AI system evaluation and testing"**
- Revenue: MASSIVE for consulting
- Scarcity: VERY HIGH
- Why: clients pay to know their AI works. Walk in with an eval framework and you immediately look like the most serious person in the room.

**2. "Business problem → AI system design"**
- Revenue: MASSIVE (consultants charge $200/hr for this)
- Scarcity: HIGH
- Why: formalize the thinking behind your online shopping website chatbot. Learn to ask: "what decision needs to be made? what data exists? what's the cost of a wrong prediction?"

**3. "LangGraph production patterns"** (go deeper than tutorials)
- Revenue: HIGH (enterprises paying a lot for LangGraph expertise right now)
- Scarcity: MEDIUM-HIGH

---

## SECTION 3: YOUR VISIBILITY PLAN — FIRST 10 LINKEDIN POSTS

### New LinkedIn Headline:
> Building AI agents that solve real business problems | Non-CS → AI Engineer | 18 projects, zero tutorials on the last one

---

### POST 1 — Your origin story

i never took a CS class in my life.

i grew up in korea, served in the military, then came to the US to study web design at CSM.

4 months ago i decided i wanted to become an AI engineer. no CS degree. no ML background. just python and stubbornness.

i followed 18 tutorial projects. built agents, pipelines, chatbots — all by copying what someone else did.

then i stopped following tutorials and built my first real thing: a multi-agent customer service system for an online shopping website. billing. orders. account management. with guardrails so the AI wouldn't go off-topic.

it worked.

i'm documenting the whole journey here — the gaps, the confusion, the things that actually clicked. if you're also breaking into AI without a traditional background, follow along.

what's the biggest thing that confused you when you started learning AI?

---

### POST 2 — The tutorial trap (contrarian)

After completing 18 AI projects, I did learn quite a lot, but not much really stayed with me. 

Looking back, I realized it was because I was mostly following instructions instead of figuring things out on my own.

that's what tutorial projects do to you. you feel productive. you ship something. you add it to your portfolio.

For me, I replayed the videos until I really understand, but I didn't actually know why it works. 

the moment i stopped following a tutorial and built something myself — a customer service agent with multi-domain routing and guardrails — i realized i'd been building muscle memory, not understanding.

tutorials teach you syntax. they don't teach you how to think about a problem.

the fix: after every tutorial, delete the code and rebuild it from scratch without looking. if you can't, you didn't learn it.

how many tutorials have you finished and forgotten?

---

### POST 3 — Build in public: e-commerce support agent

built my first original AI project. here's what i actually built and what i learned.

it's a multi-agent customer service system for e-commerce — handles billing disputes, order tracking, and payment issues.

every message goes through 5 stages before a response goes out:
triage → policy scope → completeness check → risk evaluation → specialized agent

the happy path took 2 days. the edge cases took 2 weeks.

two things i built that no tutorial mentions:

1. LLMs don't always return clean JSON. i wrote a fallback parser that finds `{}` in broken output and retries the parse. without this, the agent was silently crashing on roughly 15% of real inputs.

2. LLMs hallucinate. my triage model kept returning categories that didn't exist. i added output normalization — if the model returns something outside the allowed list, it falls back to a keyword classifier instead of breaking.

the gap between a demo and a production system is almost entirely failure handling.

what's the most unexpected way your AI agent has failed in production?

#AIEngineering #LangGraph #BuildInPublic

---

### POST 4 — What nobody tells you about AI agents

everyone teaches you how to build an AI agent.

nobody teaches you how to know if it's working.

i've built 18+ agent projects. most of them "worked" in the sense that they ran without errors.

but were they actually doing the right thing? giving accurate answers? routing correctly? i had no idea.

turns out there's a whole field around evaluating AI systems. evals. test cases. tracing. it's what separates toys from production systems.

i'm diving into this now. if you're building AI agents and you don't have an eval strategy, your agent might be confidently wrong 30% of the time and you'd never know.

does your AI project have a way to measure if it's actually performing?

---

### POST 5 — The non-CS path to AI (opinion)

you don't need a CS degree to become an AI engineer.

bold claim. let me back it up.

what you actually need:
— python (practical, not theoretical)
— enough ML to understand what the model is doing
— system design thinking (how do the pieces connect?)
— the ability to frame a business problem as an AI problem

what you don't need:
— deep algorithms knowledge
— academic math beyond basic statistics
— a computer science curriculum from 1995

i'm living proof. no CS degree. studying web design. 4 months into AI. building real systems.

the barrier to entry in AI is lower than the gatekeepers want you to believe.

what's the biggest thing you thought you needed but turned out not to?

---

### POST 6 — Technical breakdown: routing logic in AI agents

one of the most underrated skills in agentic AI: routing logic.

when a user sends a message to your agent, something has to decide: which tool? which sub-agent? which prompt?

most tutorials do this naively: keyword matching or a single LLM call that classifies intent.

the problem: naive routing fails on ambiguous inputs, multi-intent messages, and edge cases. which means your agent breaks exactly when it matters most.

better approach:
1. classify intent with confidence score (not just label)
2. if confidence < threshold, ask for clarification instead of guessing
3. handle multi-intent by breaking into sub-tasks
4. log every routing decision so you can improve over time

this is what i built into my online shopping website chatbot. the guardrail is just routing logic with a "none of the above" category.

what routing approach are you using in your agents?

---

### POST 7 — Korea → US → AI (personal)

most people who become AI engineers followed a straight path.

mine was: korea → military service → US → web design → fell completely in love with AI → decided to rebuild my entire career direction in 4 months.

the military taught me one thing that's actually more useful than any CS course: when you don't know something, you figure it out. resources are limited. failure has consequences. you adapt.

that mindset is why i built 18 projects in 4 months. not because i'm smart. because i treated every project like it mattered.

the AI field rewards people who ship and learn, not people who wait until they feel ready.

what's the unconventional background that actually helps you in tech?

---

### POST 8 — Business problem first, AI second

most junior AI engineers start with: "what can i build with AI?"

consultants start with: "what problem costs this business money?"

the difference in how much they get paid is not a coincidence.

i've been reframing how i think about every project:

bad: "i'll build a RAG system"
good: "customer support tickets take 8 minutes to resolve. what if that was 2 minutes?"

bad: "i'll make an AI agent"
good: "this company manually routes 500 support messages a day. what if zero were manual?"

the AI is the solution. not the goal. the goal is always a business outcome.

how do you frame your AI projects — by the tech or by the outcome?

---

### POST 9 — What i wish i knew before building AI agents

4 months. 18+ projects. here's what i wish someone told me earlier:

1. the happy path is not the product. edge cases are the product.
2. "it works" and "it works reliably" are completely different things.
3. the best AI system often uses less AI than you think.
4. if you can't explain why your agent made a decision, you can't fix it when it breaks.
5. your first project without a tutorial will teach you more than 10 with one.

i'm still learning all of these. number 4 is the one that's humbling me right now — i've built systems i can't fully explain. that's a problem i'm actively fixing.

which one of these hits closest for you?

---

### POST 10 — The eval problem (value post)

here's a framework i'm using to evaluate my AI agents before i'd ever show them to a client:

**3-layer eval:**
layer 1 — does it work at all? (basic functional test: does the agent complete the task?)
layer 2 — does it work correctly? (accuracy test: is the output actually right? sample 20 cases manually)
layer 3 — does it work reliably? (stress test: what happens with weird inputs, edge cases, multi-turn conversations, contradictory requests?)

most people only test layer 1. then they're surprised when their "working" agent fails in production.

i failed at this with my first original project. it passed layer 1. layer 2 revealed a routing bug that hit 15% of messages. layer 3 showed the guardrail broke on certain sentence structures.

fixed all of it. now it's actually production-ready.

what's your eval process for AI agents?

---

## SECTION 4: YOUR OUTREACH MACHINE

### Warm-up plan (you said nervous but willing):

- **Weeks 1-2:** 15-20 connection requests/day. Zero DMs. Target: AI engineers, founders of small AI startups, heads of operations at companies that could use customer service automation.
- **Weeks 3-4:** Comment on 5-10 posts/day. Add value, don't compliment. "this matches what i saw building a multi-agent customer service system — the routing layer was the hardest part to get right"
- **Week 5:** First DMs to people you've already commented on. Reference the post. Goal: conversation, not a job.
- **Week 6+:** Full outreach — 25 connections/day, 5 DMs/day.

### Target companies:
US-based companies with customer-facing operations (e-commerce, SaaS, healthcare admin, real estate) that would benefit from what you already built.
Find them: YC startup directory, Crunchbase (Series A-B, <50 employees), Product Hunt.

### Outreach Templates:

**Template 1 — The Callout + Value**
```
hi [name], noticed [company] is scaling customer support — you're handling [X] customers and the team is growing fast.

i recently built a multi-agent customer service system with routing logic for billing, orders, and account management. happy to share how it's structured if it's useful context for what you're building.

no pitch — just figured it might be relevant. worth a 15-min call?
```

**Template 2 — The Insight**
```
hi [name], i've been studying how companies at your stage handle customer service automation and noticed [company] is still routing manually / using basic chatbots.

built something recently that reduced routing errors significantly using a guardrail layer before the LLM — happy to walk through the architecture if you're curious.

either way, cool what you're building.
```

**Template 3 — The Follow-up (after 5-7 days)**
```
hey [name], circling back on this — no pressure at all, just didn't want it to get buried.

if the timing's off, totally understand. rooting for what you're building at [company] either way.
```

---

## SECTION 5: YOUR RESEARCH PAPER READING PLAN

| Week | Paper | Why it matters for YOU | What to read | Career takeaway |
|------|-------|----------------------|--------------|-----------------|
| 1 | "Attention Is All You Need" (Vaswani et al., 2017) | Every LLM you've used is built on this | Abstract + Introduction only | The transformer replaced everything before it. context window = memory. |
| 2 | "ReAct: Synergizing Reasoning and Acting in Language Models" (Yao et al., 2022) | Theoretical foundation of every agent you've built | Abstract + Section 2 | Reason-then-act is the pattern behind LangGraph. |
| 3 | "Toolformer: Language Models Can Teach Themselves to Use Tools" (Schick et al., 2023) | Explains tool use in LLMs from first principles | Abstract + Introduction | Tool calling isn't magic. it's pattern matching on a training distribution. |
| 4 | "Constitutional AI" (Anthropic, 2022) | How guardrails work at scale | Abstract + Section 1-2 | Your chatbot guardrail is a manual version of this. |
| 5 | "Chain-of-Thought Prompting Elicits Reasoning in Large Language Models" (Wei et al., 2022) | Explains why CoT works | Full paper (it's short) | Why "let's think step by step" works. |
| 6 | "LLM-as-a-Judge" (Zheng et al., 2023) | Foundation of AI evals — your consulting superpower | Abstract + Sections 1-3 | Use an LLM to evaluate another LLM's output. core technique behind scalable AI evaluation. |
| 7 | "Self-Consistency Improves Chain of Thought Reasoning" (Wang et al., 2022) | Better outputs through sampling | Abstract + Conclusion | Run the same prompt multiple times and take the majority vote. practical, shippable today. |
| 8 | "Large Language Models are Zero-Shot Reasoners" (Kojima et al., 2022) | Understanding emergent capabilities | Abstract only | Why GPT-4 can do things it was never explicitly trained for. |
| 9 | RAGAS paper on RAG evaluation | Clients will ask about RAG — know the eval story | Abstract + evaluation section | RAG fails in predictable ways. knowing how to measure RAG quality is a consulting advantage. |
| 10 | "Voyager: An Open-Ended Embodied Agent with Large Language Models" (Wang et al., 2023) | The frontier of agentic AI | Abstract + Introduction | Where autonomous agents are heading. |
| 11 | "AgentBench: Evaluating LLMs as Agents" (Liu et al., 2023) | Systematic agent evaluation | Abstract + evaluation methodology | Framework for evaluating your agents beyond "it works." |
| 12 | GPT-4 Technical Report or Claude Model Card | What frontier models say about themselves | Limitations section only | Limitations sections are a roadmap for what gets built next. |

### Arxiv Morning Digest Agent — System Prompt:
```
You are a research digest assistant for an AI engineer specializing in agentic AI systems 
and AI consulting for businesses. Every morning, you pull 3 papers from Arxiv in these areas: 
(1) LLM agents and autonomous systems, (2) AI evaluation and testing frameworks, 
(3) practical AI deployment and production systems. For each paper, write exactly 2 paragraphs: 
the first summarizes what the paper does and why it matters; the second explains one specific 
thing the reader could build or do differently based on this paper's findings. Keep language 
practical, not academic. The reader has a practitioner background, not a research background.
```

---

## SECTION 6: YOUR 9-12 MONTH WEEK-BY-WEEK TIMELINE

**At 10-20 hrs/week allocation:**
- 4-5 hrs: Architecture learning (papers, videos, reading)
- 5-7 hrs: Building (projects, applying what you learned)
- 2 hrs: Visibility (writing + posting on LinkedIn)
- 1 hr: Outreach (connections, comments, eventually DMs)

| Phase | Architecture Learning | Skill Building | Visibility | Outreach | Papers |
|-------|----------------------|----------------|------------|----------|--------|
| Phase 1 (Weeks 1-4) | 3Blue1Brown neural nets + Karpathy zero-to-hero | Rebuild online shopping website chatbot from scratch WITHOUT looking at old code | Publish posts 1, 2, 3 | 15 connection requests/day, zero DMs | Attention (wk1), ReAct (wk2) |
| Phase 2 (Weeks 5-8) | Fast.ai lessons 1-3 + CS50 AI first 4 lectures | Add prediction layer to chatbot (escalation classifier) | Publish posts 4, 5, 6 | Engage on 5-10 posts/day | Toolformer (wk3), Constitutional AI (wk4) |
| Phase 3 (Weeks 9-12) | Decision layer: expected value, business logic | Build 1 original project for a real use case (not shopping mall) | Publish posts 7, 8, 9, 10 | First 5 DMs to people you've been engaging with | CoT (wk5), LLM-as-Judge (wk6) |
| Phase 4 (Weeks 13-17) | LangGraph source code deep dive + eval frameworks | Build eval harness for your best project | Overhaul LinkedIn with new headline + outcome-based skills | 25 connections/day, 5 DMs/day | Self-consistency (wk7), Zero-shot (wk8) |
| Phase 5 (Weeks 18-22) | AI consulting case studies + business problem framing | Scope a real client problem. Write a mini proposal. | Post weekly about consulting process | Apply to 5 AI engineer roles/freelance projects | RAG eval (wk9), Voyager (wk10) |
| Phase 6 (Weeks 23-28) | Read frontier papers in your niche weekly | Deploy something publicly (GitHub, demo site) | Share deployment publicly, document the process | 500+ total outreach messages sent, 5+ real conversations | AgentBench (wk11), Model cards (wk12) |

### Monthly Milestones:

- **End of Phase 1 (~Month 1):** LinkedIn updated. Posts 1-3 published. Shopping mall chatbot rebuilt from scratch. You understand what transformers are doing conceptually.
- **End of Phase 2 (~Month 2):** Posts 4-6 published. Chatbot has a prediction layer. CS fundamentals gaps closed enough for a basic technical screen.
- **End of Phase 3 (~Month 3):** 10 posts published. First original project (not tutorial) live on GitHub. First 5 outreach DMs sent.
- **End of Phase 4 (~Month 4):** LinkedIn overhauled with outcome-based skills. Eval harness built and documented. 25 connections/day consistent. Resume rewritten around outcomes not tools.
- **End of Phase 5 (~Month 5-6):** 1 real or simulated consulting proposal written and shared publicly. 200+ outreach messages sent. 3+ real conversations with people at target companies.
- **End of Phase 6 (~Month 6-7):** 2 deployed projects with public URLs. 50+ LinkedIn posts. 500+ outreach messages. 12 papers read. At least 1 freelance engagement or final interview stage.

---

this plan is personalized to your specific situation — no CS degree, living in the US, agentic AI focus, 10-20 hrs/week, military discipline, 4-month sprint already behind you.

the gap between you and a $100K AI job is smaller than you think. you've already done the hardest thing — you built something real without a tutorial. the problem is you're invisible. nobody knows you exist.

that's fixable. today. right now.

open linkedin. copy post #1 from section 3 above. edit two sentences so it sounds exactly like you. publish it. that's your homework for today. not this week. today.

— ayush
