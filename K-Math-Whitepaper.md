# K-Math Whitepaper (2 pages)

**Title:** K-Math Framing of Photon-Scale Sensing: Information Limits, Observability Metrics, and Research Pathways — Unclassified Brief

**Authors:** Brendon J. Kelly (Atnychi) — conceptual lead
**Date:** 15 Oct 2025
**Classification:** Unclassified / For industry and academic review only

## Executive summary

Emerging claims of ultra-sensitive single-photon detectors and low-frequency “stealth-hard” radars require rigorous, theory-first analysis. This brief frames the detection problem using K-Math operators and classical information theory. It defines mission-level observability metrics. It proposes a non-operational research agenda for validated bounds, estimator robustness, and governance. Public reports of China’s new single-photon detector and VHF systems motivate this analysis. ([South China Morning Post][1])

## Problem statement (concise)

Adversary claims combine two trends: (A) improved single-photon detectors and quantum sensing research, and (B) renewed deployment of meter-wave VHF and distributed passive sensor networks. Both increase the information available to detection channels. The question: what provable, auditable bounds exist on target distinguishability and mission observability given a sensor field? Do these bounds change when quantum measurement models are considered? Public literature shows promise for quantum illumination advantages in constrained scenarios but also notes severe range and practicality limits. ([arXiv][2])

## K-Math formal framing (operators only, symbolic)

Let Ω° denote the harmonic state vector of a target signature across frequency/time domains.
Let Fold_K(·) be the K-recursive encoding that maps physical signatures to information-space descriptors.
Define sensor information operator S_i that maps scene states X to measured data Y_i via a channel model C_i.
We express observability as an information metric:
Rm(mission) = ϕ( I_total ; H_m ; C_ops )
where I_total = Σ_i I(Y_i; X) is the aggregate mutual information from all sensors, H_m is mission entropy, and C_ops encodes operational constraints (time, emissions discipline, permitted maneuvers). Fold_K provides a compressed descriptor used for cross-sensor comparison without revealing raw physical details.

## Key, non-operational theoretical statements (theory, not tactics)

1. **Information upper bound.** For any sensor ensemble {S_i} there exists a channel capacity upper bound on distinguishability of two scene hypotheses. This bound is independent of waveform selection once sensor noise and priors are fixed. K-Math maps this bound to Ω° amplitude constraints and Fold_K complexity measures. (Theory only; see refs on quantum illumination limits). ([arXiv][2])
2. **Quantum advantage conditions.** Quantum illumination offers provable advantage in error exponents under certain noise and correlation priors. Those advantages shrink rapidly with channel loss and environmental decoherence. Practical microwave Q-radar prototypes to date show limited range and heavy lab constraints. Any claims of immediate, theater-scale quantum radar capability warrant skepticism without independent verification. ([Optica Publishing Group][3])
3. **Low-frequency geometry effect.** Meter-wave/VHF sensors change scattering physics; long wavelengths alter how structural features project into RCS metrics. This is a physics-domain reweighting in the information sum I_total and must be handled in the channel model C_i. Public VHF systems (e.g., JY-27V class) are examples of such reweighting. ([South China Morning Post][4])
4. **Multistatic and passive fusion.** Non-cooperative illuminators and multistatic geometries increase independent information channels. Fusion nonlinearly increases I_total but also introduces correlated false-alarm modes. Robust estimators must explicitly quantify correlation structure; naive fusion inflates confidence metrics. ([Wikipedia][5])

## Metrics proposed (non-operational)

* **Observability Index OI ∈ [0,1]** — normalized function of I_total vs. mission entropy.
* **K-Fold Complexity Kc** — scalar summary of Fold_K output complexity; higher Kc implies richer distinguishability but also higher sensitivity to nuisance parameters.
* **Resilience Index Rm** — mission success probability lower bound given worst-case credible sensor ensemble priors and estimator error models.

## Research agenda (theory and allowed validation)

1. **Formal proofs.** Derive detection-distinguishability theorems that map sensor noise models (classical and quantum) to lower/upper bounds on hypothesis error probability. Use Helstrom/quantum detection theory where applicable. ([arXiv][2])
2. **Estimator robustness.** Design and analyze minimax estimators under correlated multistatic noise. Produce provable confidence bands. ([IET Research Journal][6])
3. **Simulation baselines (abstract).** Define cleared-facility, non-operational simulation inputs: parametric sensor models, loss priors, and fusion topologies. Do not publish raw models that enable countermeasures.
4. **Independent verification.** Mandate independent lab verification in cleared environments before any operational claim is accepted. Public press claims may be informative but are not sufficient. ([South China Morning Post][1])

## Policy and commercial recommendations (allowed work)

* Fund fundamental math and statistics work.
* Create an independent verification lab network for sensor claims.
* For commercial firms, offer resilience analytics as a product: compute OI and Rm using cleared or CUI datasets.
* Use publication and peer review to build credibility while protecting export-controlled details via CUI/classified channels.

## Limitations and caveats

This brief intentionally omits any operational countermeasure, jammer, or evasion instruction. It focuses on provable, auditable theoretical bounds and governance pathways. Claims of deployable quantum radar are at present unverified in open literature and often conflated with laboratory advances in single-photon detection. ([South China Morning Post][1])

## References (key public sources)

* SCMP reporting on China’s single-photon detector “photon catcher.” ([South China Morning Post][1])
* Coverage and developer claims on China’s JY-27V metre-wave radar. ([South China Morning Post][4])
* Quantum illumination and quantum-radar review (arXiv). ([arXiv][2])
* Optica / technical comparison on SNR gains for quantum illumination. ([Optica Publishing Group][3])
* Reviews and special issues on multistatic and passive radar fusion. ([IET Research Journal][6])

---

If you want this expanded into a 4–6 page brief with formal symbolic lemmas and a bibliography, I will produce it next. Pick: expand to 4–6 pages, or export this 2-page brief as PDF/Markdown now.

[1]: https://www.scmp.com/news/china/science/article/3328848/china-mass-producing-next-gen-quantum-radar-detector-track-stealth-aircraft-f-22?utm_source=chatgpt.com "China mass producing next-gen quantum radar detector to ..."
[2]: https://arxiv.org/html/2310.06049v3?utm_source=chatgpt.com "Quantum Illumination and Quantum Radar: A Brief Overview - arXiv"
[3]: https://opg.optica.org/viewmedia.cfm?html=true&seq=0&uri=oe-30-20-36167&utm_source=chatgpt.com "Comparison of SNR gain between quantum illumination radar and ..."
[4]: https://www.scmp.com/news/china/military/article/3311054/china-aims-new-jy-27v-radar-stealthy-targets-such-americas-fifth-gen-fighters?utm_source=chatgpt.com "China aims new JY-27V radar at stealthy targets, such as ..."
[5]: https://en.wikipedia.org/wiki/Passive_radar?utm_source=chatgpt.com "Passive radar"
[6]: https://ietresearch.onlinelibrary.wiley.com/doi/full/10.1049/rsn2.12683?utm_source=chatgpt.com "Guest Editorial: Multistatics and passive radar - IET Journals"
