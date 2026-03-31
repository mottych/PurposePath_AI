# From Velocity to Value

## Intent-Driven Product Development

## in the Age of AI

### Alex Batsuk

```
March 2026
```

## I. The Paradox We Inherited

Agile was a revolution. In 2001, seventeen developers gathered at a ski lodge in Snowbird, Utah,
and declared war on waterfall’s tyranny—the endless requirements documents, the phase-gate
bureaucracies, the eighteen-month death marches toward software nobody wanted. They won.
Spectacularly.

Then something curious happened. The revolution calcified into its own orthodoxy.

Sprint planning. Story points. Velocity tracking. SAFe frameworks with their baroque
hierarchies of Program Increment objectives and Architectural Runways. Scrum masters
became a profession. Certification bodies multiplied. The Agile Industrial Complex emerged,
complete with consultants, tools, and conferences—all dedicated to measuring how fast teams
moved while losing track of where they were going.

_We perfected the art of delivering the wrong thing faster._

This is not an indictment of Agile’s principles. The Manifesto remains sound: individuals over
processes, working software over documentation, customer collaboration over contract
negotiation, responding to change over following a plan. The failure was not in the philosophy.
It was in the implementation—the reduction of adaptive development to ceremony, the
substitution of velocity metrics for value validation, the quiet abandonment of the question Agile
never quite answered: _Should we build this at all?_

Into this void stepped Vibe Coding—the developer’s rebellion against process itself. Why write
specifications when you can prompt an AI and iterate in real-time? Why plan when you can
prototype? The instinct was correct: something had ossified. But speed without specification is
chaos with velocity. You arrive somewhere fast. You just don’t know where, or whether anyone
needed you there.

Lean Startup offered a partial answer: validate before you build, pivot when evidence demands.
Spec-Driven Development proposed another: make specifications executable, let them guide AI
generation. AWS formalized this with the AI-Driven Development Lifecycle; tools like Kiro
demonstrated what becomes possible when specifications become context for AI agents. Each
contribution advanced the conversation. None completed it.

The methodology wars produced insights and innovations, but they left the fundamental tension
unresolved. We optimized for throughput when outcomes mattered. We measured completion
when value mattered. We celebrated shipping when impact mattered.

We need a different question. Not “how fast can we deliver?” but “are we achieving what we set
out to achieve?”

Intent-Driven Development is the synthesis that answers this question.


## II. The Convergence That Changes Everything

Three simultaneous shifts created an inflection point. Separately, each would have been
significant. Together, they make possible what was previously theoretical.

**First: AI that can implement.** Large language models crossed a threshold. They don’t just
suggest code; they generate it. They don’t just autocomplete; they architect. GitHub Copilot,
Claude, Amazon Q Developer—these systems can take natural language descriptions and
produce working implementations. But capability without constraint is dangerous. An AI that
can build anything will build anything, including systems that violate security policies,
accessibility standards, or fundamental business logic. The power demands governance. The
question becomes: _how do we direct this capability toward outcomes that matter?_

**Second: Specifications that machines can read.** For decades, specifications existed in
documents that humans wrote and humans occasionally referenced. Word files. Confluence
pages. PDFs in SharePoint. These artifacts were write-only: created once, consulted rarely,
disconnected from the code they supposedly governed. But specifications can be structured.
They can live in version control alongside the code they inform. They can be parsed by the same
AI systems that generate implementations. The specification becomes executable—not in the
sense that it runs, but in the sense that it provides context that shapes what runs. Steering files,
constitution documents, rule sets—these artifacts transform from passive documentation into
active constraints that inform every AI interaction with the codebase.

**Third: IDEs that understand context.** Modern development environments—Cursor,
Windsurf, Kiro, VS Code with Copilot—are no longer text editors with syntax highlighting. They
are context-aware systems that can read specifications, understand constraints, and guide
implementation accordingly. When a constitution file declares that all API endpoints must
validate authentication, the AI assistant incorporates that constraint at generation time, not
review time. The shift-left philosophy reaches its logical conclusion: problems prevented are
cheaper than problems detected, and problems addressed at generation are cheaper than
problems caught in review.

The governance layer is maturing in parallel. Policy as Code tools—Open Policy Agent, Checkov,
HashiCorp Sentinel—codify compliance requirements as executable rules. Security policies
become testable assertions. Infrastructure configurations become auditable artifacts. The
human bottleneck—that review gate where someone verified compliance before blessing a
deployment—transforms into continuous, automated validation. Not because human judgment
doesn’t matter, but because human attention is precious and should focus on decisions that
require wisdom, not verification that requires only consistency.

The tools finally caught up to the vision. Now the vision must catch up to the tools.


## III. The Specification Hierarchy: Architecture of Intent

Intent-driven development replaces ad-hoc documentation with a coherent hierarchy. Four
layers, each with distinct purpose, each governing what lies below it. When every specification
knows its place, no decision is orphaned.

At enterprise scale, this hierarchy connects to a central codification repository—a governed
collection of specification templates, constitution patterns, and domain controls that
standardize product development across the organization. Individual product teams inherit
from this repository, ensuring consistency while retaining flexibility for domain-specific needs.
The repository itself is version-controlled, auditable, and subject to the same rigor as the
products it governs.

```
Figure 1: The Specification Hierarchy
```
### The Product Charter: Existential Layer

The charter answers the questions that precede all others. Why does this product exist? What
problem justifies its existence? What transformation does it promise? Who benefits, in what
order, when interests conflict?

This is not a PRD. Product Requirements Documents bundle features into releases, conflating
the strategic with the tactical until neither is visible. This is not a roadmap. Roadmaps sequence


work over time without explaining why the work matters. This is not a vision statement. Vision
statements inspire without constraining.

The charter is a constitution for the product. It establishes the ethical boundaries that no feature
may cross. It defines success not as delivery but as transformation—the measurable change in
user capability that justifies the product’s existence. It creates a stakeholder hierarchy that
resolves conflicts before they emerge: when the administrator’s convenience conflicts with the
end user’s effectiveness, the charter declares which wins.

A charter without a Harm Model is incomplete. Every product capable of helping is capable of
hurting. The charter names the negative outcomes the product must prevent, the trade-offs the
product may accept, and the boundaries the product must not cross. This is not pessimism. It is
professional discipline.

### Persona Specifications: Human Layer

Traditional personas describe users in ideal states. They are demographic profiles—“Sarah, 35,
marketing manager, values work-life balance”—that generate conference room agreement and
production-environment failure. Real users do not exist in ideal states. They exist under
deadline pressure, in edge conditions, with divided attention. They use products at 11 PM with
fractured focus. They encounter errors during quarter-close crunches. They need clarity
precisely when they are least able to seek it.

The persona specification asks a different question: _What does this user need when everything
is going wrong?_

This is the pressure profile principle. For every persona, define the most demanding realistic
scenario. What is their cognitive state under deadline pressure? What can they still do? What
can they no longer do? How much time do they have? What must the system provide without
requiring them to search for it?

A consultant at 11:47 PM with three rejected expense codes and a flight boarding in twenty
minutes is not the same consultant who reviewed documentation during onboarding. The
system that serves the first consultant must work for the second. The system designed only for
the first will fail the second—precisely when failure costs most.

Persona specifications emerge from collaboration. The Product Manager brings business context
and stakeholder insight. The UX Specialist brings research methodology and behavioral
expertise. The Product Architect brings understanding of what AI agents can and cannot infer
from persona data. Together, they map the capability spectrum from optimal through degraded
to high-pressure states. They document mental models, including the incorrect ones. They
define what builds trust and what breaks it. They name the failure modes—how the product
could negatively impact this person, and how to prevent it.

Not demographic theater. Psychological truth.


### Intent Specifications: Capability Layer

The intent specification defines what the product must make possible. Not what features to
build—capabilities to enable. Not how the system works—what the system accomplishes. The
distinction matters.

A feature is an implementation. An intent is an outcome. “Add export button” is a feature.
“Users can extract their data in formats their downstream systems accept” is an intent. The first
prescribes solution. The second defines success. The first closes options. The second opens
them.

Each intent contains a value hypothesis: a testable belief about what will improve for whom. It
contains validation signals: how we will know the hypothesis holds. It contains kill criteria: the
conditions under which we will deprecate this intent regardless of effort invested. This is not
defeatism. This is intellectual honesty. An intent without kill criteria will persist forever,
consuming resources without validation.

Each intent contains a harm model. Not the existential harms the charter addresses, but the
implementation-specific risks this capability could create. What data could be exposed? What
processes could break? What trust could erode? Harm modeling is not a checkbox exercise. It is
a discipline of anticipation.

The behavior specifications use Gherkin scenarios—Given/When/Then structures that are both
human-readable and machine-parseable. These scenarios emerge through collaborative
dialogue. The Product Manager provides business context and success criteria. The UX
Specialist provides user journey insight and interaction patterns. The Product Architect provides
understanding of how scenarios will be parsed by implementation agents. Together with AI
assistants, they generate comprehensive scenarios covering core paths, edge cases, error
conditions. Scenarios that don’t serve the intent are discarded. Scenarios that reveal gaps in the
intent trigger revision.

The result is a specification that no single discipline—and no single human—could produce
alone.

### Constitution Files: Behavioral Layer

Between intent and implementation lies a gap. The intent says what must be possible. The code
says how it’s achieved. But what governs the how? What ensures that security patterns are
followed, accessibility standards met, performance and quality attributes respected?

Constitution files bridge this gap. They are the codified standards, patterns, and guardrails that
constrain implementation. They are machine-readable, version-controlled, and enforceable at
generation time. When a constitution declares that all user inputs must be sanitized, the AI
assistant that generates code incorporates that constraint as context—not because a reviewer
will catch violations later, but because the constitution is part of the prompt.

At enterprise scale, constitution files inherit from the central codification repository.
Organization-wide security policies, accessibility requirements, and architectural patterns flow


down as domain controls. Product teams extend these with product-specific rules. The hierarchy
ensures consistency without rigidity: global standards are enforced automatically; local
adaptations are explicit and auditable.

This is governance without gates. The standards exist. They are explicit. They inform the same
systems that generate code. Human reviewers focus on judgment—does this implementation
serve the intent effectively?—rather than verification—were the standards followed? The shift-
left principle applies not just to testing but to governance itself: compliance baked in at
generation, not bolted on at review.

Constitution files include technical standards, security requirements, accessibility rules, and AI
execution envelopes. The envelope defines what autonomous agents may do without human
approval: which actions are pre-approved, which require review, which trigger escalation. As AI
capabilities expand, explicit envelopes become essential. The alternative is implicit trust, and
implicit trust does not scale.

## IV. The Collaborative Triad: Humans and Agents Together

Intent-driven development does not replace human judgment. It focuses it.

The concern is understandable: AI agents that can generate code, elaborate scenarios, and
validate specifications sound like automation of the product role. They are not. They are
amplification of the product role. The distinction is crucial.

But here is a deeper truth: the product role itself was always a simplification. Building products
that matter has never been the work of a single discipline. Intent-driven development makes
this explicit through the collaborative triad: Product Manager, UX Specialist, and Product
Architect working together, each bringing irreplaceable perspective.

**The Product Manager** brings business context, stakeholder relationships, and strategic
vision. They own the charter. They understand why the product exists, who it serves, and what
constraints govern its evolution. They navigate organizational dynamics, prioritize competing
demands, and ensure that what gets built aligns with what the business needs.

**The UX Specialist** brings research methodology, behavioral expertise, and design rigor. They
own the personas. They understand how users actually behave—not how we wish they behaved.
They map the pressure states, identify the mental models, define the communication
requirements. They ensure that what gets built works for humans under real conditions.

**The Product Architect** is an AI Engineer who brings technical understanding of AI
capabilities and constraints. They own the constitutions. They understand what AI agents can
infer from specifications, what context they need, what guardrails they require. They define
execution envelopes, design prompt architectures, ensure that specifications translate into
effective AI behavior.

Together, they create specifications that no single discipline could produce. The PM’s business
logic is grounded in the UX Specialist’s user reality. The UX Specialist’s design intent is


constrained by the Product Architect’s implementation understanding. The Product Architect’s
technical patterns serve the PM’s strategic goals.

**AI agents** participate in this collaboration as tireless partners. They handle structure,
completeness, consistency. They ensure specifications are well-formed. They flag missing
sections. They detect anti-patterns—the intent that is really a feature in disguise, the persona
that is really a demographic profile, the charter that is really a roadmap. They generate scenarios
systematically, covering edge cases humans overlook. They maintain traceability, ensuring every
intent links to its charter, every persona appears in the stakeholder hierarchy, every constitution
is referenced by the intents it governs.

But agents cannot do what humans do. Agents can verify that a value hypothesis is stated. They
cannot verify that the hypothesis is true. Agents can ensure a harm model is populated. They
cannot judge whether the risks named are honest or whether the mitigations are adequate.
Agents can generate scenarios based on inputs. They cannot verify that inputs reflect what users
actually need rather than what teams assume they need.

The collaboration model is explicit:

**Humans provide:** Research. Judgment. Values. Domain knowledge. Stakeholder
relationships. Cross-functional synthesis. The agents cannot conduct user interviews, observe
behavior in context, or navigate the political realities of organizational change. These remain
human responsibilities.

**Agents provide:** Structure. Consistency. Completeness. Scenario elaboration. Validation
against schema. Tireless attention to detail. The agents do not tire, do not forget constraints, do
not skip sections because the meeting is running long.

**Together:** Specifications that neither humans nor agents could produce alone. Human insight
structured by agent rigor. Agent comprehensiveness validated by human judgment. Three
disciplines synthesized into coherent artifacts that serve the enterprise.

This is not replacement. It is partnership with explicit roles. The agents ensure specifications are
well-formed. The triad ensures they are worth forming.

## V. What Dies, What Lives, What’s Born

Intent-driven development is not Agile with better documentation. It is a different operating
model. Some elements of prior methodologies transfer directly. Others do not. Still others
emerge that no prior methodology conceived.

**What dies:**

_Sprints._ The two-week sprint was an artifact of manual implementation velocity. When
engineers work with AI assistants that reference intent specs and constitution files directly, code
generation and testing compress from weeks to days—even hours for well-specified intents.
Work flows continuously from intent to deployment. The artificial bundling of work into time-


boxed increments no longer serves its original purpose. What remains is continuous delivery
governed by intent, not calendar.

_Story points._ Abstract estimation made sense when implementation effort was unpredictable
and teams needed a planning heuristic. But story points estimated effort; they never estimated
value. Intents are validated against value hypotheses and measured against expected signal
ranges. The question is not “how large is this?” The question is “does this deliver the outcome we
hypothesized?”

_Velocity tracking._ Teams measured points per sprint as a proxy for productivity. But throughput
is not impact. Delivering forty points of capabilities nobody uses is not success. Intent-driven
teams measure whether active intents are achieving their value hypotheses. Outcomes over
outputs.

_The backlog as source of truth._ In Agile, the backlog was the prioritized queue of work. Position
determined importance. Intent-driven development replaces queue with hierarchy. An intent
either serves the charter or it does not. Position in a list is irrelevant. Traceability to purpose is
everything.

_Gates and reviews as bottlenecks._ Human chokepoints where reviewers verified compliance are
replaced by codified governance. Constitution files inform generation. Policy as Code tools
validate continuously. Reviewers focus on judgment—does this implementation serve the intent
effectively?—rather than verification—were the standards followed? The shift-left principle
reaches its conclusion: embed quality at origin rather than inspect for it at exit.

_Siloed disciplines._ The PM who throws requirements over the wall. The designer who creates
artifacts in isolation. The architect who dictates without collaborating. Intent-driven
development demands the collaborative triad—disciplines working together on shared artifacts,
each contributing irreplaceable perspective.

**What lives:**

_Testable acceptance criteria._ Gherkin scenarios in behavior specifications serve the same
purpose as acceptance criteria on stories: defining done in testable terms. The format is more
structured. The purpose is identical.

_Iteration._ Intents evolve through research and feedback. Active intents may be revised as
learning accumulates. The specification is not frozen at creation. It evolves through deliberate
amendment, with changes logged and rationale preserved.

_Collaboration._ Intent specifications emerge from conversation among product, design,
engineering, and stakeholders. The format is more structured. The collaboration is essential.
Agents augment the conversation; they do not replace it.

_Customer focus._ Agile insisted on customer collaboration over contract negotiation. Intent-
driven development deepens this commitment by grounding it in pressure-tested personas. Not
abstract customer segments—specific humans whose failure modes are named and whose
degraded states are mapped.


**What’s born:**

_Kill criteria before building._ Every intent defines the conditions under which it would be
deprecated. This is not pessimism. It is rigor. If you cannot imagine failure, you are not being
honest about uncertainty. Kill criteria create permission to stop investing in capabilities that do
not deliver value.

_Harm models as first-class artifacts._ Charter harms address existential risk—should this
product exist at all? Intent harms address implementation risk—could this capability create
problems we haven’t anticipated? Both are explicit, documented, and reviewed. Harm modeling
moves from afterthought to prerequisite.

_Value hypotheses with validation signals._ Ship and measure replaces ship and celebrate. Every
intent contains a hypothesis about what will improve and for whom. Every hypothesis contains
signals that would validate or invalidate it. Every signal has expected ranges. Deviation triggers
investigation.

_Specification-as-code._ Specifications live in version control alongside the code they govern. They
are structured, machine-readable, and traceable. Changes are tracked. History is preserved. The
specification is not a document that exists somewhere else. It is part of the codebase, subject to
the same discipline, informing the same AI systems that generate implementation.

_Enterprise codification._ At scale, specification templates, constitution patterns, and domain
controls live in a central repository that governs product development across the organization.
This repository is version-controlled, auditable, and continuously refined. It represents the
organization’s accumulated wisdom about how to build products—encoded not in tribal
knowledge but in machine-readable artifacts that inform every AI interaction.

## VI. The Philosophical Foundation

Intent-driven development is not a methodology. It is an epistemological stance. It asserts that
knowing _why_ before _how_ is not bureaucracy—it is efficiency. It asserts that specification is not
the obstacle to building but the building that happens before anyone writes code.

Six principles ground this stance. They are not arbitrary preferences. They are structural truths
about how complex systems succeed or fail.

**Specification precedes implementation.** Code without specification is debt. You may not
know what you owe, but you owe it. Specification without code is aspiration—necessary but
insufficient. Together they form architecture: intention made executable, constraints made
enforceable, purpose made traceable.

**Degradation is normal.** Systems designed for optimal conditions fail when conditions
matter. Users experience fatigue, distraction, deadline pressure. Networks experience latency,
congestion, outage. Systems that require everything to work will fail when anything doesn’t.
Design for pressure, not comfort. Design for the user at 11:47 PM with competing demands, not
the user in the demo.


**Harm is foreseeable.** Every capability potent enough to help is potent enough to hurt. The
same feature that empowers legitimate use enables misuse. The same automation that reduces
friction reduces oversight. Acknowledging potential negative outcomes is not pessimism. It is
professionalism. Products that do not name their risks will discover them in production, at scale,
without mitigation.

**Value requires hypothesis.** If you cannot define failure, you cannot prevent it. If you cannot
define success, you cannot verify it. Every intent contains a hypothesis: we believe that enabling
this capability will produce this improvement for these people. The hypothesis may be wrong.
That is why we validate. Intents without kill criteria become zombies—consuming resources,
never retired, never validated.

**Hierarchy creates coherence.** When every document knows what governs it and what it
governs, decisions compound rather than conflict. The charter constrains personas, intents, and
constitutions. The personas inform intents. The intents reference constitutions. The
constitutions constrain implementation. Change the charter, and dependent specifications know
they must respond. Orphan a specification from the hierarchy, and it drifts into irrelevance—still
maintained, no longer meaningful.

**Autonomy requires envelope.** AI systems capable of acting autonomously need boundaries
that are explicit, not implied. The execution envelope defines what agents may do without
approval, what requires review, what triggers escalation. As capabilities expand, envelopes
become essential. The alternative—implicit trust that AI will do the right thing—does not scale.
It does not even work at small scale. It merely fails quietly until it fails consequentially.

These principles are not preferences. They are the physics of product development. Violate them
and encounter consequences; honor them and benefit from their structure. Intent-driven
development makes them explicit, enforceable, and—through codification—automatic.

## VII. The Invitation

We stand at an inflection point.

For the first time, the tools can read specifications as readily as they read code. For the first
time, governance can be codified rather than bottlenecked. For the first time, AI assistants can
generate implementations that comply with constraints they were never explicitly trained on—
because the constraints are in context, machine-readable, part of the prompt.

This convergence creates a choice.

One path continues optimizing for velocity. More sprints. More story points. More ceremonies
measuring movement. This path is comfortable. It is familiar. It leads nowhere new.

The other path optimizes for value. It asks not “how fast can we deliver?” but “are we achieving
what we set out to achieve?” It replaces throughput metrics with outcome validation. It replaces
documentation that humans write and never read with specifications that machines parse and
humans govern. It replaces implicit standards with explicit constitutions. It replaces


demographic personas with psychological truth. It replaces features with intents, estimation
with hypothesis, celebration with measurement.

This path is harder. It requires honesty about potential harms. It demands kill criteria before
building. It insists on pressure profiles, not happy paths. It makes explicit what was comfortable
to leave vague.

But this path leads somewhere. It leads to products that know what they are for. It leads to
teams that know why they are building. It leads to systems that perform under pressure, not just
systems that demo well.

The specification is not the obstacle to building.

It is the building that happens before anyone writes code.

And now, for the first time, the machines can read it.

_This document provides an overview of intent-driven product development. Companion guides for
Product Charter, Intent Specification, and Persona Specification offer detailed section-by-section
guidance. Constitution file specifications and Blueprints complete the hierarchy._


