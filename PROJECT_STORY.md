# CareSignal

> **Tagline:** Finding trusted care, faster.

---

## Inspiration

CareSignal was inspired by the stressful experience families face when trying to find trusted care for a loved one. Facility information, ratings, inspection details, location data, and reviews are often scattered across different sources and difficult to compare.

We wanted to make care discovery faster, clearer, and more trustworthy by bringing important decision signals into one simple experience.

---

## What it does

CareSignal helps users explore, compare, and evaluate care facilities in one AI-powered dashboard.

Users can:

- Browse facilities in a **Facility Explorer**
- Search nearby options using **Geo Search**
- Review quality and confidence indicators in **Trust Review**
- Ask natural-language questions through a **Chat Assistant**

At a high level, CareSignal turns fragmented care information into a guided decision workflow:

$$
\text{Better Data} + \text{AI Guidance} + \text{Clear UX} = \text{More Confident Care Decisions}
$$

---

## How we built it

We built CareSignal using **Databricks** as the data and AI foundation. Facility data is organized into an interactive dashboard with focused sections for search, geography, trust review, and chat-based assistance.

The project combines:

- Structured facility data
- Location-based search patterns
- Trust and review-style indicators
- A compact dashboard interface
- AI-assisted question answering grounded in available data

The core decision-support flow can be represented as:

$$
\text{Facility Search} \rightarrow \text{Geo Context} \rightarrow \text{Trust Signals} \rightarrow \text{AI-Guided Decision Support}
$$

---

## Challenges we ran into

One major challenge was deciding how to present trust signals clearly without overwhelming users or overclaiming certainty. Care decisions are sensitive, so the app needed to support human judgment rather than replace it.

Other challenges included:

- Choosing which facility signals were most useful to surface
- Balancing a compact dashboard with meaningful detail
- Keeping the AI assistant grounded in available data
- Designing a professional interface within the time limits of the hackathon

---

## Accomplishments that we're proud of

We are proud of building a polished, practical tool that addresses a real-world problem. CareSignal brings together search, geography, quality indicators, and AI assistance in a clean experience that helps users move from uncertainty to action.

We are especially proud that the project focuses on **decision support**, not automated decision-making. The goal is to help families ask better questions, compare options more clearly, and make more confident care choices.

---

## What we learned

We learned that care discovery is not just a data problem — it is also a trust and usability problem. Even when facility data exists, users still need help interpreting it, comparing options, and understanding tradeoffs.

We also learned that AI tools in sensitive domains should be:

- Transparent
- Focused
- Grounded in available data
- Designed to support, not replace, human judgment

A simple way to think about the project is:

$$
\text{CareSignal Impact} = f(\text{Data Quality}, \text{Trust}, \text{Usability}, \text{AI Guidance})
$$

---

## What's next for CareSignal

Next, we would expand CareSignal with richer facility datasets, verified review sources, stronger quality and compliance indicators, and more personalized recommendations based on user needs.

Future features could include:

- Saved facility shortlists
- Caregiver and family collaboration tools
- More detailed compliance and inspection signals
- Integration with care coordinators and insurers
- Personalized care matching based on user priorities

Our long-term vision is to make care discovery less fragmented and more supportive, helping families find trusted care faster when it matters most.
