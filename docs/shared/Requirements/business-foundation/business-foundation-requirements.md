# Business Foundation - Requirements Document

**Version:** 1.0  
**Last Updated:** December 22,2024  
**Status:** Draft for Review

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Problem Statement](#2-problem-statement)
3. [Goals and Objectives](#3-goals-and-objectives)
4. [Information Architecture](#4-information-architecture)
5. [Foundation Hub (Direct Access)](#5-foundation-hub-direct-access)
6. [Setup Wizard (Guided Mode)](#6-setup-wizard-guided-mode)
7. [Section Details](#7-section-details)
8. [AI Integration](#8-ai-integration)
9. [Navigation and Access](#9-navigation-and-access)
10. [Data Migration](#10-data-migration)
11. [UI/UX Design System](#11-uiux-design-system)
12. [Implementation Phases](#12-implementation-phases)

---

## 1. Executive Summary

The Business Foundation module reimagines the current onboarding experience, transforming it from a one-time wizard into a living strategic asset. Users can complete an initial guided setup, then return anytime to view and edit individual sections without navigating the entire flow.

The enhanced data model captures richer information about the business, enabling more meaningful AI suggestions throughout the application. Products gain full descriptions, values include implementation guidance, and new sections provide crucial business context.

### Key Transformations

| Current State | Future State |
|--------------|--------------|
| Onboarding wizard only | Hub + Wizard dual access |
| Products: Title + Problem | Products: Full profile with features |
| Values: Just names | Values: Name + Meaning + Implementation |
| Limited business context | Rich profile for AI context |
| Complete and forget | Living, evolving document |

---

## 2. Problem Statement

### Challenge 1: Inflexible Access Pattern
Users must navigate the entire wizard to change a single piece of information. A CEO who wants to update their company's vision must click through multiple irrelevant steps, creating friction and discouraging refinement.

### Challenge 2: Shallow Product Information
Products currently capture only a title and the problem they solve. Missing is what the product actually does, its features, target audience, and differentiators. This limits our ability to provide relevant strategic suggestions.

### Challenge 3: Insufficient Business Context
The application lacks fundamental business context needed for meaningful AI suggestions:
- Industry classification
- Company stage and size
- Revenue range
- Geographic focus

Without this context, AI suggestions remain generic rather than tailored.

### Challenge 4: Values Without Depth
Core values are captured as a simple list of words. Users type "Innovation" or "Integrity" without articulating what these mean in practice or how they will be implemented. This makes values feel like empty platitudes rather than actionable principles.

### Challenge 5: One-Time Mentality
The "onboarding" terminology implies completion. Once done, users rarely return, even as their business evolves. The foundation becomes stale and disconnected from reality.

---

## 3. Goals and Objectives

### Primary Goals

1. **Enable Direct Access**: Users can view and edit any section of their business foundation independently, without navigating unrelated sections.

2. **Enrich Data Quality**: Capture deeper, more actionable information in every section, transforming shallow data into strategic assets.

3. **Provide AI Context**: Give the AI system enough business context to provide tailored, industry-specific, stage-appropriate suggestions.

4. **Encourage Ongoing Refinement**: Design the experience to invite regular review and updates as the business evolves.

### Success Criteria

- Users with complete foundations: 80% within 30 days
- Return visits to foundation: 40% of users within first quarter
- AI suggestion relevance score improvement: 25%
- Foundation health score average: 75%+

---

## 4. Information Architecture

### The Six Pillars

The Business Foundation consists of six interconnected pillars:

```
┌─────────────────────────────────────────────────────────────┐
│                    BUSINESS FOUNDATION                       │
├─────────────┬─────────────┬─────────────┬─────────────┬────┤
│  Business   │    Core     │   Target    │  Products   │    │
│  Profile    │  Identity   │   Market    │ & Services  │    │
├─────────────┼─────────────┼─────────────┼─────────────┤    │
│    Value    │  Business   │             │             │    │
│ Proposition │   Model     │             │             │    │
└─────────────┴─────────────┴─────────────┴─────────────┴────┘
```

### 4.1 Business Profile

**Purpose**: Provide factual context about the business for AI-powered features.

**Fields**:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| Business Name | Text | Yes | Legal or trading name |
| Business Description | Long Text | Yes | 2-3 sentence description of the business |
| Address | Object | No | Business address (preserved from existing onboarding) |
| Address - Street | Text | No | Street address |
| Address - City | Text | No | City |
| Address - State | Text | No | State/Province |
| Address - Zip | Text | No | Postal/ZIP code |
| Address - Country | Text | Yes* | Country (*required if address provided) |
| Industry | Select + Custom | Yes | Primary industry classification |
| Sub-Industry | Select + Custom | No | More specific classification |
| Company Stage | Select | Yes | Startup / Growth / Scale / Mature |
| Company Size | Select | Yes | Employee count range |
| Revenue Range | Select | No | Annual revenue range (optional, sensitive) |
| Year Founded | Number | No | When the business started |
| Geographic Focus | Multi-select | Yes | Markets served (Local, Regional, National, Global) |
| Headquarters Location | Text | No | City/Country (display purposes) |
| Website | URL | No | Company website

**Company Stage Options**:
- Startup (0-2 years, finding product-market fit)
- Growth (2-5 years, scaling what works)
- Scale (5-10 years, expanding markets/products)
- Mature (10+ years, optimization and innovation)

**Company Size Options**:
- Solo (1 person)
- Micro (2-10 employees)
- Small (11-50 employees)
- Medium (51-200 employees)
- Large (201-1000 employees)
- Enterprise (1000+ employees)

**Revenue Range Options** (displayed if user opts in):
- Pre-revenue
- Under $100K
- $100K - $500K
- $500K - $1M
- $1M - $5M
- $5M - $10M
- $10M - $50M
- $50M+
- Prefer not to say

### 4.2 Core Identity

**Purpose**: Capture the "soul" of the business - why it exists and what it believes.

#### Vision Statement

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| Vision Statement | Long Text | Yes | Future state the business aspires to create |
| Vision Timeframe | Select | No | When this vision should be realized (3, 5, 10, 20 years) |

**Guidance for users**: "Your vision describes the world you want to create. It should inspire and provide direction. Think 5-10 years ahead."

#### Purpose/Mission Statement

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| Purpose Statement | Long Text | Yes | Why the business exists, the impact it makes |
| Who We Serve | Text | No | Brief description of primary beneficiaries |

**Guidance for users**: "Your purpose explains why your business exists beyond making money. What positive impact do you make?"

#### Core Values

Each value is now a structured entity:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| Value Name | Text | Yes | The value (e.g., "Innovation") |
| Meaning | Long Text | Yes | What this value means to the organization |
| Implementation | Long Text | Yes | How this value is put into practice |
| Behaviors | Text Array | No | Specific behaviors that demonstrate this value |
| Display Order | Number | Auto | Order in the list |

**Example Value**:
```
Name: "Customer Obsession"
Meaning: "We start with the customer and work backwards. We work vigorously to 
         earn and keep customer trust."
Implementation: "Every feature decision requires documented customer feedback. 
                Customer satisfaction is reviewed weekly at all-hands."
Behaviors: 
  - "Ask 'how does this help the customer?' in every meeting"
  - "Respond to customer inquiries within 4 hours"
  - "Include customer quotes in product requirements"
```

**Minimum values**: 3  
**Maximum values**: 7

### 4.3 Target Market

**Purpose**: Define who the business serves and understand their needs deeply.

#### Niche Definition

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| Niche Statement | Long Text | Yes | Clear definition of the market niche |
| Market Size | Text | No | Estimated market size (TAM/SAM/SOM) |
| Growth Trend | Select | No | Declining / Stable / Growing / Rapidly Growing |

#### Ideal Customer Avatar (ICA)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| ICA Name | Text | Yes | Persona name (e.g., "Marketing Mary") |
| Demographics | Long Text | Yes | Age, role, industry, company size |
| Goals | Long Text | Yes | What they're trying to achieve |
| Pain Points | Long Text | Yes | Problems and frustrations they face |
| Motivations | Long Text | No | What drives their decisions |
| Objections | Long Text | No | Common concerns about solutions like yours |
| Where They Are | Long Text | No | Where to find them (channels, communities) |
| Buying Process | Long Text | No | How they evaluate and purchase |

**Multiple ICAs**: Users can define up to 5 ICAs to represent different customer segments.

### 4.4 Products & Services

**Purpose**: Describe what the business offers with enough detail for strategic planning.

Each product/service is a comprehensive entity:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| Name | Text | Yes | Product or service name |
| Tagline | Text | No | One-line description |
| Type | Select | Yes | Product / Service / Subscription / Hybrid |
| Description | Long Text | Yes | What it does (functionality, capabilities) |
| Problem Solved | Long Text | Yes | The pain point it addresses |
| Key Features | Text Array | No | Main features or components |
| Target Audience | Select | No | Which ICA(s) this serves |
| Pricing Tier | Select | No | Premium / Mid-market / Entry-level / Free |
| Pricing Model | Select | No | One-time / Subscription / Usage-based / Freemium |
| Differentiators | Long Text | No | What makes it unique vs. alternatives |
| Status | Select | Yes | Active / In Development / Planned / Retired |
| Revenue Contribution | Select | No | Primary / Secondary / Emerging |
| Display Order | Number | Auto | Order in the list |

**Minimum products**: 1  
**Maximum products**: 20

### 4.5 Value Proposition

**Purpose**: Articulate why customers should choose this business over alternatives.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| Unique Selling Proposition | Long Text | Yes | The primary reason customers choose you |
| Key Differentiators | Long Text | Yes | What sets you apart from competitors |
| Proof Points | Long Text | No | Evidence that supports your claims |
| Customer Outcomes | Long Text | No | Results customers achieve |
| Brand Promise | Text | No | The commitment you make to customers |

**Competitive Positioning** (optional section):

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| Primary Competitors | Text Array | No | Main competitors |
| Competitive Advantage | Long Text | No | Why you win against competitors |
| Market Position | Select | No | Leader / Challenger / Niche / Emerging |

### 4.6 Business Model

**Purpose**: Describe how the business creates and captures value.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| Business Model Type | Multi-select | Yes | B2B, B2C, B2B2C, Marketplace, etc. |
| Primary Revenue Stream | Text | Yes | Main source of revenue |
| Secondary Revenue Streams | Text Array | No | Additional revenue sources |
| Pricing Strategy | Long Text | No | Approach to pricing |
| Key Partners | Text Array | No | Critical business relationships |
| Distribution Channels | Text Array | No | How products/services reach customers |
| Customer Acquisition | Long Text | No | Primary methods for acquiring customers |

---

## 5. Foundation Hub (Direct Access)

### 5.1 Overview

The Foundation Hub is the primary interface for viewing and editing the business foundation. It presents all six pillars as expandable cards, showing completion status and key information at a glance.

### 5.2 Hub Layout

```
┌─────────────────────────────────────────────────────────────┐
│  BUSINESS FOUNDATION                                         │
│  The strategic bedrock of your business                      │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─ Header Actions ────────────────────────────────────────┐│
│  │ [Run Setup Wizard]  [AI Health Check]  [Export]         ││
│  └─────────────────────────────────────────────────────────┘│
│                                                              │
│  ┌─ Foundation Health ─────────────────────────────────────┐│
│  │                                                          ││
│  │  Overall Health: ████████░░ 82%                         ││
│  │                                                          ││
│  │  ┌────┐ ┌────┐ ┌────┐ ┌────┐ ┌────┐ ┌────┐             ││
│  │  │ ✓  │ │ ⚠  │ │ ✓  │ │ ⚠  │ │ ✓  │ │ ○  │             ││
│  │  │Prof│ │Iden│ │Mkt │ │Prod│ │Val │ │Biz │             ││
│  │  └────┘ └────┘ └────┘ └────┘ └────┘ └────┘             ││
│  │                                                          ││
│  │  💡 "2 products need descriptions to improve AI context" ││
│  └─────────────────────────────────────────────────────────┘│
│                                                              │
│  ┌─ Section Cards ─────────────────────────────────────────┐│
│  │                                                          ││
│  │  [Section cards listed below]                            ││
│  │                                                          ││
│  └─────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────┘
```

### 5.3 Section Card Design

Each section is displayed as a card with:

**Card Header**:
- Section icon
- Section name
- Completion indicator (✓ Complete / ⚠ Incomplete / ○ Empty)
- Edit button

**Card Body** (collapsed state):
- Key summary information (2-3 lines)
- Count of items (for arrays like products, values)
- Warning if important fields are missing

**Card Expansion**:
- Clicking the card or "View Details" expands to show more
- "Edit" opens the slide-out panel

### 5.4 Section Card Examples

**Business Profile Card**:
```
┌─────────────────────────────────────────────────────────────┐
│ 🏢 BUSINESS PROFILE                           ✓  [Edit →]   │
├─────────────────────────────────────────────────────────────┤
│ TechCorp Inc. • SaaS • Growth Stage                         │
│ 45 employees • $2M-$5M revenue • North America              │
│                                                              │
│ "We build enterprise software that simplifies complex       │
│  business processes for mid-market companies."              │
└─────────────────────────────────────────────────────────────┘
```

**Core Identity Card**:
```
┌─────────────────────────────────────────────────────────────┐
│ 💎 CORE IDENTITY                              ⚠  [Edit →]   │
├─────────────────────────────────────────────────────────────┤
│ Vision: "To become the leading platform for..."             │
│ Purpose: "We empower businesses to achieve..."              │
│ Values: Innovation, Integrity, Customer Focus, Excellence   │
│                                                              │
│ ⚠ 2 values missing implementation details                   │
└─────────────────────────────────────────────────────────────┘
```

**Products & Services Card**:
```
┌─────────────────────────────────────────────────────────────┐
│ 📦 PRODUCTS & SERVICES                        ⚠  [Edit →]   │
├─────────────────────────────────────────────────────────────┤
│ 3 products defined                                           │
│                                                              │
│ • PurposePath Pro (Premium) ✓                               │
│ • PurposePath Starter (Entry) ⚠ missing description         │
│ • PurposePath API (Add-on) ✓                                │
│                                                              │
│ ⚠ 1 product needs a description                             │
└─────────────────────────────────────────────────────────────┘
```

### 5.5 Slide-Out Panel for Editing

When a user clicks "Edit" on any section, a slide-out panel opens from the right:

**Panel Structure**:
```
┌─────────────────────────────────────────────────────────────┐
│  CORE IDENTITY                                       [×]    │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─ Vision ────────────────────────────────────────────────┐│
│  │                                                          ││
│  │  Vision Statement *                                      ││
│  │  ┌──────────────────────────────────────────────────┐   ││
│  │  │ To become the leading platform for strategic      │   ││
│  │  │ business planning and execution...                │   ││
│  │  └──────────────────────────────────────────────────┘   ││
│  │  [✨ AI: Refine vision]                                  ││
│  │                                                          ││
│  │  Timeframe: [5 Years ▼]                                 ││
│  │                                                          ││
│  └─────────────────────────────────────────────────────────┘│
│                                                              │
│  ┌─ Purpose ───────────────────────────────────────────────┐│
│  │  ... similar structure ...                               ││
│  └─────────────────────────────────────────────────────────┘│
│                                                              │
│  ┌─ Core Values ───────────────────────────────────────────┐│
│  │                                                          ││
│  │  [+ Add Value]                                          ││
│  │                                                          ││
│  │  ┌─ Innovation ─────────────────────────────── [⋮] ────┐││
│  │  │ Meaning: "We challenge conventional thinking..."     │││
│  │  │ Implementation: "20% time for experimentation..."    │││
│  │  │ ✓ Complete                                           │││
│  │  └──────────────────────────────────────────────────────┘││
│  │                                                          ││
│  │  ┌─ Integrity ──────────────────────────────── [⋮] ────┐││
│  │  │ Meaning: "We do the right thing..."                  │││
│  │  │ ⚠ Missing implementation details                     │││
│  │  │ [Complete this value →]                              │││
│  │  └──────────────────────────────────────────────────────┘││
│  │                                                          ││
│  └─────────────────────────────────────────────────────────┘│
│                                                              │
├─────────────────────────────────────────────────────────────┤
│  [Cancel]                              [Save Changes]        │
└─────────────────────────────────────────────────────────────┘
```

### 5.6 Inline Editing

For simple fields, enable inline editing directly on the hub:
- Click on text to edit in place
- Changes auto-save after 2 seconds of inactivity
- Subtle confirmation toast: "Vision statement updated"

---

## 6. Setup Wizard (Guided Mode)

### 6.1 Purpose

The Setup Wizard provides a guided experience for:
- First-time users completing their foundation
- Users who want a comprehensive review
- Users who prefer step-by-step guidance

### 6.2 Wizard Flow

```
Step 1: Business Profile
         │
         ▼
Step 2: Core Identity (Vision, Purpose, Values)
         │
         ▼
Step 3: Target Market (Niche, ICA)
         │
         ▼
Step 4: Products & Services
         │
         ▼
Step 5: Value Proposition
         │
         ▼
Step 6: Review & Activate
```

### 6.3 Wizard Interface

**Wizard Header**:
```
┌─────────────────────────────────────────────────────────────┐
│  BUSINESS FOUNDATION SETUP                                   │
│  Build the strategic bedrock of your business               │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ●───●───●───○───○───○                                      │
│  Profile  Identity  Market  Products  Value   Review        │
│              ↑                                               │
│        You are here                                          │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 6.4 Step Layout

Each step follows a consistent layout:

```
┌─────────────────────────────────────────────────────────────┐
│  Step 2: Core Identity                                       │
│  "Define your vision, purpose, and the values that guide    │
│   every decision in your business."                         │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─ Main Content Area ─────────────────────────────────────┐│
│  │                                                          ││
│  │  [Form fields for this step]                            ││
│  │                                                          ││
│  │  ┌─ AI Assistant ───────────────────────────────────┐   ││
│  │  │ 💡 Based on your business description, here are   │   ││
│  │  │    some suggestions for your vision...            │   ││
│  │  │                                                   │   ││
│  │  │ "To revolutionize how mid-market companies..."    │   ││
│  │  │ [Use this] [Modify]                               │   ││
│  │  └───────────────────────────────────────────────────┘   ││
│  │                                                          ││
│  └─────────────────────────────────────────────────────────┘│
│                                                              │
├─────────────────────────────────────────────────────────────┤
│  [← Back]  [Skip for now]              [Save & Continue →]   │
└─────────────────────────────────────────────────────────────┘
```

### 6.5 Skip Functionality

Users can skip any step:
- Skipped sections show as "Incomplete" in the hub
- Users can return via the hub to complete
- Critical fields still required before final activation
- Progress is saved even when skipping

### 6.6 Progress Persistence

- Progress auto-saves after each field change
- Users can exit and return later
- Last step is remembered
- Partial completion is preserved

### 6.7 Review Step

The final step shows a summary of all sections:

```
┌─────────────────────────────────────────────────────────────┐
│  Review Your Foundation                                      │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Foundation Health: ████████░░ 85%                          │
│                                                              │
│  ✓ Business Profile - Complete                              │
│  ✓ Core Identity - Complete                                 │
│  ✓ Target Market - Complete                                 │
│  ⚠ Products & Services - 1 item needs attention             │
│  ✓ Value Proposition - Complete                             │
│  ○ Business Model - Not started (optional)                  │
│                                                              │
│  ┌─ Recommendations ───────────────────────────────────────┐│
│  │ • Add descriptions to incomplete products               ││
│  │ • Consider defining your business model for better AI   ││
│  │   suggestions                                            ││
│  └─────────────────────────────────────────────────────────┘│
│                                                              │
│  [← Edit Sections]              [Complete Setup →]           │
└─────────────────────────────────────────────────────────────┘
```

---

## 7. Section Details

### 7.1 Business Profile Section

**Purpose**: Establish business context for AI-powered features.

**Form Layout**:
```
Business Name *
[_________________________________]

Business Description *
[                                                          ]
[                                                          ]
[                                                          ]
💡 "Describe what your business does in 2-3 sentences"

┌─ Business Address (optional) ──────────────────────────────┐
│                                                             │
│ Street Address                                              │
│ [123 Main Street                                    ]      │
│                                                             │
│ City                    State/Province      Zip/Postal     │
│ [San Francisco    ]    [CA           ]     [94105    ]    │
│                                                             │
│ Country *                                                   │
│ [United States ▼]                                          │
│                                                             │
└─────────────────────────────────────────────────────────────┘

Website (optional)
[https://                                             ]

Industry *
[Select industry... ▼]
  └─ [+ Add custom industry]

Company Stage *
○ Startup - Finding product-market fit
○ Growth - Scaling what works  
○ Scale - Expanding markets/products
○ Mature - Optimization and innovation

Company Size *
[Select employee range... ▼]

Revenue Range (optional)
[Prefer not to say ▼]
□ Don't ask me again

Year Founded (optional)
[2018    ]

Geographic Focus *
☑ Local
☐ Regional
☑ National
☐ Global
```

**AI Assistance**:
- Industry suggestions based on business description
- Stage recommendations based on company age and size
- Benchmark comparisons for similar companies

### 7.2 Core Identity Section

**Purpose**: Capture the organization's vision, purpose, and guiding principles.

**Vision Subsection**:
```
Vision Statement *
[                                                          ]
[                                                          ]
[                                                          ]
[✨ AI: Help me write a vision statement]

Timeframe
[5 Years ▼]

💡 "Your vision describes the future state you want to create. 
    Think big and inspiring."
```

**Purpose Subsection**:
```
Purpose Statement *
[                                                          ]
[                                                          ]
[                                                          ]
[✨ AI: Help me write a purpose statement]

Who We Serve
[Brief description of primary beneficiaries]

💡 "Your purpose explains WHY your business exists beyond 
    making money. What impact do you make?"
```

**Values Subsection**:
```
Core Values (3-7 values)

┌─ Value 1 ─────────────────────────────────────────── [×] ─┐
│                                                            │
│ Value Name *                                               │
│ [Innovation                    ]                           │
│                                                            │
│ What does this value mean to your organization? *          │
│ [We embrace new ideas and challenge conventional thinking  │
│  to find better solutions for our customers.              ]│
│                                                            │
│ How do you implement this value in practice? *             │
│ [We dedicate 20% of team time to experimentation.         │
│  Every quarter, we run innovation challenges.             ]│
│                                                            │
│ Example behaviors (optional)                               │
│ [Question assumptions         ] [+]                        │
│ [Prototype before perfecting  ]                            │
│ [Celebrate learning from failure]                          │
│                                                            │
└────────────────────────────────────────────────────────────┘

[+ Add Another Value]
[✨ AI: Suggest values based on my business]
```

### 7.3 Target Market Section

**Purpose**: Define who the business serves.

**Niche Subsection**:
```
Market Niche *
[                                                          ]
[                                                          ]
[                                                          ]
[✨ AI: Help define my niche]

💡 "A clear niche helps you stand out. Be specific about 
    WHO you serve and WHAT problem you solve for them."

Examples: 
• "Enterprise SaaS companies needing compliance automation"
• "Health-conscious millennials seeking meal delivery"
```

**ICA Subsection**:
```
Ideal Customer Avatar

Avatar Name *
[Marketing Mary                  ]

Demographics *
[35-50 years old, Marketing Director or VP at mid-market    ]
[B2B tech companies (50-500 employees), based in US/Canada  ]

What are they trying to achieve? *
[Scale their marketing operations while maintaining quality  ]
[Prove marketing ROI to leadership                          ]

What pain points do they face? *
[Too many tools, lack of integration                        ]
[Difficulty measuring campaign effectiveness                ]
[Limited budget for large enterprise solutions              ]

[✨ AI: Enrich my ICA with more details]

[+ Add Another ICA] (up to 5)
```

### 7.4 Products & Services Section

**Purpose**: Describe offerings with strategic depth.

```
┌─ Product 1 ─────────────────────────────────────── [×] ────┐
│                                                             │
│ Product Name *                                              │
│ [PurposePath Pro              ]                             │
│                                                             │
│ Tagline                                                     │
│ [Strategic planning platform for growing businesses   ]    │
│                                                             │
│ Type *                                                      │
│ ○ Product  ● Subscription  ○ Service  ○ Hybrid             │
│                                                             │
│ What does it do? *                                          │
│ [PurposePath Pro is an AI-powered strategic planning       │
│  platform that helps business leaders create, track,       │
│  and execute their strategic goals. It includes goal       │
│  setting, Measure tracking, team alignment tools, and          │
│  AI-powered recommendations.                              ]│
│ [✨ AI: Help me write a description]                        │
│                                                             │
│ What problem does it solve? *                               │
│ [Businesses struggle to translate vision into              │
│  actionable plans. Leaders spend too much time on          │
│  spreadsheets and not enough on strategic thinking.       ]│
│                                                             │
│ Key Features                                                │
│ [Goal setting wizard          ] [+]                         │
│ [Measure tracking dashboard       ]                             │
│ [AI strategy recommendations  ]                             │
│ [Team alignment tools         ]                             │
│                                                             │
│ Target Audience                                             │
│ [Marketing Mary ▼] (links to ICA)                          │
│                                                             │
│ Pricing                                                     │
│ Tier: [Premium ▼]  Model: [Subscription ▼]                 │
│                                                             │
│ What makes it unique?                                       │
│ [Unlike traditional planning tools, PurposePath uses       │
│  AI to provide contextual recommendations based on         │
│  your specific business situation and industry.           ]│
│                                                             │
│ Status: [Active ▼]  Revenue Role: [Primary ▼]              │
│                                                             │
└─────────────────────────────────────────────────────────────┘

[+ Add Another Product]
[✨ AI: Suggest products based on my business]
```

### 7.5 Value Proposition Section

**Purpose**: Articulate competitive positioning.

```
Unique Selling Proposition *
[The only strategic planning platform that combines         ]
[AI-powered insights with proven business frameworks to     ]
[help growing businesses achieve their goals faster.       ]
[✨ AI: Help me refine my USP]

Key Differentiators *
• [AI-powered recommendations tailored to your business    ]
• [Integrated coaching and accountability                  ]
• [Built specifically for growing businesses              ] [+]

Proof Points
[Over 500 businesses have achieved their quarterly goals   ]
[using PurposePath. Average goal completion rate: 78%.    ]

Customer Outcomes
[Customers report 3x faster goal completion               ]
[92% say they have better strategic clarity               ]

Brand Promise
[We promise to give you clarity on your path forward     ]
```

### 7.6 Business Model Section

**Purpose**: Describe how the business operates.

```
Business Model Type *
☑ B2B (Business to Business)
☐ B2C (Business to Consumer)
☐ B2B2C
☐ Marketplace
☑ SaaS (Software as a Service)
☐ Consulting/Services
☐ E-commerce

Primary Revenue Stream *
[Monthly and annual subscriptions to PurposePath Pro     ]

Other Revenue Streams
[Implementation services     ] [+]
[Training workshops         ]
[API access fees           ]

Pricing Strategy
[Value-based pricing with three tiers: Starter ($49/mo), ]
[Pro ($149/mo), and Enterprise (custom). Annual plans    ]
[offer 20% discount.                                     ]

Key Partners
[Strategic coaching networks] [+]
[Business accelerators     ]
[Certified consultants     ]

Distribution Channels
[Direct website sales      ] [+]
[Partner referrals        ]
[App marketplace listings  ]
```

---

## 8. AI Integration

### 8.1 Foundation Health Check

A comprehensive AI review of the entire foundation:

**Trigger**: Button on Foundation Hub or periodic prompt

**Output**:
```
┌─ Foundation Health Report ─────────────────────────────────┐
│                                                             │
│  Overall Health Score: 78/100                               │
│                                                             │
│  ✓ STRENGTHS                                               │
│  • Clear and compelling vision statement                    │
│  • Well-defined target market with detailed ICA             │
│  • Products have clear problem statements                   │
│                                                             │
│  ⚠ OPPORTUNITIES                                           │
│  • 2 products missing descriptions - add details to         │
│    improve AI recommendations                               │
│  • Values lack implementation details - makes them          │
│    harder to apply in daily decisions                       │
│  • Business model section empty - helps AI understand       │
│    your strategic priorities                                │
│                                                             │
│  💡 RECOMMENDATIONS                                         │
│  1. Complete product descriptions (15 min estimated)        │
│  2. Add implementation to each value (20 min estimated)     │
│  3. Define basic business model (10 min estimated)          │
│                                                             │
│  [Start with Product Descriptions →]                        │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 8.2 Section-Level AI Assistance

Each section has contextual AI help:

| Section | AI Capabilities |
|---------|----------------|
| Business Profile | Industry suggestions, stage assessment, benchmark data |
| Vision | Vision statement generation, refinement suggestions |
| Purpose | Purpose clarity check, impact articulation |
| Values | Value suggestions, meaning/implementation generation |
| Niche | Niche validation, market size estimation |
| ICA | ICA enrichment, pain point discovery |
| Products | Description generation, feature suggestions |
| Value Proposition | USP refinement, differentiator identification |
| Business Model | Revenue stream suggestions, pricing guidance |

### 8.3 Cross-Application Impact

The enriched foundation powers AI throughout the app:

**Goal Alignment** (improved accuracy):
- Industry context enables relevant benchmark comparisons
- Business stage influences recommendation maturity
- Values alignment check against stated values

**Strategy Suggestions** (more relevant):
- Industry-specific strategy patterns
- Company-stage-appropriate approaches
- Aligned with stated value proposition

**Measure Recommendations** (contextual):
- Industry-standard metrics
- Stage-appropriate targets
- Aligned with business model

---

## 9. Navigation and Access

### 9.1 Primary Access Points

**Main Navigation**:
```
├── Dashboard
├── Strategic Planning
│   └── ...
├── Operations
│   └── ...
├── Business Foundation  ← NEW top-level item
│   └── Hub (default view)
│   └── Setup Wizard
└── Settings
```

### 9.2 Contextual Access

**From Settings**: Link to Foundation Hub under "Company Settings"

**From Dashboard**: Foundation health widget with quick access

**From Goals**: "Edit Foundation" when alignment seems off

**From Onboarding**: Initial setup redirects to wizard

### 9.3 First-Time User Flow

1. User completes account creation
2. System checks for business foundation
3. If empty → Redirect to Setup Wizard
4. If partial → Show Hub with completion prompts
5. If complete → Show Hub (normal state)

---

## 10. Data Migration

### 10.1 Existing Data Mapping

| Current Field | New Location | Migration |
|--------------|--------------|-----------|
| `businessName` | `profile.businessName` | Direct copy |
| `address.street` | `profile.address.street` | Direct copy |
| `address.city` | `profile.address.city` | Direct copy |
| `address.state` | `profile.address.state` | Direct copy |
| `address.zip` | `profile.address.zip` | Direct copy |
| `address.country` | `profile.address.country` | Direct copy |
| `website` | `profile.website` | Direct copy (if exists) |
| `vision` | `identity.vision` | Direct copy |
| `purpose` | `identity.purpose` | Direct copy |
| `coreValues[]` (string array) | `identity.values[]` | Create CoreValue entries with name only; meaning and implementation flagged as incomplete |
| `niche` | `market.nicheStatement` | Direct copy |
| `ica` | `market.icas[0]` | Create single ICA entry with demographics field; other fields flagged as incomplete |
| `valueProposition` | `proposition.uniqueSellingProposition` | Direct copy |
| `products[].name` | `products[].name` | Direct copy |
| `products[].problem` | `products[].problemSolved` | Direct copy; description field flagged as incomplete |

**New Fields** (default to empty/null):
- Business Profile: `businessDescription`, `industry`, `subIndustry`, `companyStage`, `companySize`, `revenueRange`, `yearFounded`, `geographicFocus`, `headquartersLocation`
- Core Identity: `visionTimeframe`, `whoWeServe`
- Target Market: `marketSize`, `growthTrend`
- Products: `tagline`, `type`, `description`, `keyFeatures`, `targetAudienceIcaId`, `pricingTier`, `pricingModel`, `differentiators`, `status`, `revenueContribution`
- Value Proposition: `keyDifferentiators`, `proofPoints`, `customerOutcomes`, `brandPromise`, `primaryCompetitors`, `competitiveAdvantage`, `marketPosition`
- Business Model: Entire section (new)

### 10.2 Migration Strategy

1. **Automatic migration** on first access to new Foundation Hub
2. **Preserve all existing data** - no data loss
3. **Flag incomplete fields** - guide users to enhance with health score indicators
4. **No forced re-entry** - existing data is sufficient to continue using the application
5. **Graceful degradation** - AI features work with partial data, improve with more context

### 10.3 User Communication

- Toast notification: "We've enhanced the Business Foundation. Take a moment to review."
- Email for major updates
- In-app guide highlighting new capabilities

---

## 11. UI/UX Design System

### 11.1 Color Palette

**Business Foundation Accent**: Deep Amber (#B45309)
- Warm, foundational, stable
- Represents the "bedrock" concept

**Section Status Colors**:
- Complete: Emerald (#10B981)
- Needs Attention: Amber (#F59E0B)
- Empty/Not Started: Slate (#64748B)
- Error: Rose (#F43F5E)

### 11.2 Typography

**Section Headers**: 
- Font: System sans-serif, bold
- Size: 18px
- Color: Slate 900

**Field Labels**:
- Font: Medium weight
- Size: 14px
- Color: Slate 700

**Help Text**:
- Font: Regular
- Size: 12px
- Color: Slate 500

### 11.3 Component Patterns

**Section Cards**:
- Rounded corners (12px)
- Subtle shadow
- Hover state: slight lift
- Click expands inline or opens panel

**Form Fields**:
- Generous spacing
- Clear labels
- Inline validation
- AI assist buttons integrated

**Slide-Out Panels**:
- Width: Large (640px) or Medium (480px)
- Smooth animation
- Sticky header with title and close
- Scrollable content area
- Fixed footer with actions

### 11.4 Interaction Patterns

**Auto-Save**:
- Changes save automatically after 2s pause
- Subtle "Saved" indicator
- Conflict resolution for concurrent edits

**Inline Editing**:
- Click to edit mode
- Escape to cancel
- Enter to confirm
- Tab to next field

**AI Suggestions**:
- Appear as assistant bubble
- "Use this" applies suggestion
- "Modify" opens editing
- "Dismiss" hides suggestion

---

## 12. Implementation Phases

### Phase 1: Foundation Hub & Enhanced Data Model (4 weeks)

**Deliverables**:
- Business Foundation Hub page
- Six section cards with view/edit capability
- Enhanced data model with all new fields
- Slide-out panels for each section
- Basic form validation
- Data migration for existing users

**Success Criteria**:
- Users can view and edit any section directly
- All existing data migrated without loss
- Foundation health score visible

### Phase 2: Enhanced Setup Wizard (3 weeks)

**Deliverables**:
- Redesigned 6-step wizard
- Progress persistence
- Skip functionality
- Review and activate step
- First-time user redirection

**Success Criteria**:
- New users complete wizard in under 20 minutes
- Completion rate > 70%
- Skip & return workflow functional

### Phase 3: AI Integration (3 weeks)

**Deliverables**:
- Foundation health check
- Section-level AI assistance
- Cross-application integration (alignment, suggestions)
- AI-powered field suggestions

**Success Criteria**:
- AI suggestions accepted > 30% of time
- Health check identifies meaningful improvements
- Goal alignment scores improve with richer context

### Phase 4: Polish & Advanced Features (2 weeks)

**Deliverables**:
- Inline editing refinements
- Export foundation as PDF
- Foundation templates by industry
- Analytics and insights
- Mobile responsiveness

**Success Criteria**:
- User satisfaction score > 4.0/5.0
- Return visits to foundation > 40%
- Support tickets related to foundation < 5%

---

## Appendix A: API Considerations

### New Endpoints Needed

```
# Business Foundation
GET    /api/business-foundation
PUT    /api/business-foundation
GET    /api/business-foundation/health-check

# Sections (for granular updates)
PUT    /api/business-foundation/profile
PUT    /api/business-foundation/identity
PUT    /api/business-foundation/market
PUT    /api/business-foundation/products
PUT    /api/business-foundation/proposition
PUT    /api/business-foundation/model

# Products (CRUD)
POST   /api/business-foundation/products
PUT    /api/business-foundation/products/{id}
DELETE /api/business-foundation/products/{id}

# Values (CRUD)
POST   /api/business-foundation/values
PUT    /api/business-foundation/values/{id}
DELETE /api/business-foundation/values/{id}
PUT    /api/business-foundation/values:reorder

# ICAs (CRUD)
POST   /api/business-foundation/icas
PUT    /api/business-foundation/icas/{id}
DELETE /api/business-foundation/icas/{id}

# AI Endpoints
POST   /api/ai/foundation/health-check
POST   /api/ai/foundation/suggest-vision
POST   /api/ai/foundation/suggest-values
POST   /api/ai/foundation/suggest-ica
POST   /api/ai/foundation/suggest-products
```

---

## Appendix B: Glossary

| Term | Definition |
|------|------------|
| Business Foundation | The collection of core business information that provides context for strategic planning |
| Foundation Hub | The main page for viewing and editing business foundation sections |
| Setup Wizard | The guided step-by-step flow for completing the foundation |
| ICA | Ideal Customer Avatar - a detailed profile of the perfect customer |
| Foundation Health | A score indicating the completeness and quality of the foundation |
| Pillar | One of the six main sections of the business foundation |

---

**End of Requirements Document**

