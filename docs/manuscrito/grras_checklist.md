---
title: "Supplementary file 1 — GRRAS checklist"
subtitle: "Guidelines for Reporting Reliability and Agreement Studies (Kottner et al., 2011)"
header-includes: |
  ```{=typst}
  #show figure: set block(breakable: true)
  #show table: set text(size: 8.5pt)
  #show table: set par(justify: false)
  ```
---

Manuscript: *What can be measured from the broadcast? Validity of single-camera video for football-kick kinematics and swing-leg joint loads.* Section numbers refer to the submitted manuscript.

| # | GRRAS item | Where it is reported |
|:--|:--------------------------------|:--------------------------------|
| 1 | Identify in title or abstract that interrater/intrarater reliability or agreement was investigated | Title ("validity"); abstract ("method-comparison study", agreement against motion capture) |
| 2 | Name and describe the diagnostic or measurement device of interest explicitly | §1 (broadcast-video pipeline); §2.3 (RTMW-x detector, MotionAGFormer-B lifter, scaling, alignment, contact) |
| 3 | Specify the subject population of interest | §1 (football players kicking in broadcast matches); §2.1 (laboratory participants as reference population and its limits) |
| 4 | Specify the rater population of interest (if applicable) | Not applicable: the method is automated (detector + lifter). The reference "rater" is optical motion capture (§2.1) |
| 5 | Describe what is already known about reliability and agreement and provide a rationale for the study | §1 |
| 6 | Explain how the sample size was chosen; state the number of raters, subjects/objects and replicate observations | §2.7 (fixed by the public datasets; 83 participants); §2.1 (7 CMU kicks); §2.3 (5 views × 5 sizes × 2 frame rates; 3 noise seeds for CMU, 1 for MoVi) |
| 7 | Describe the sampling method | §2.1 (all seven CMU kick trials; all MoVi participants with a usable kick, after interpolating gaps of up to 0.25 s and excluding kicks with longer gaps; all 200 3DSP shots) |
| 8 | Describe the measurement process | §2.2 (features, loads, windows); §2.3 (virtual camera, error models, lifting); §2.4 (real video, digital twin); §2.5 (remedies) |
| 9 | State whether measurements were conducted independently | §2.3: video estimates never used the reference except for scale (thigh length) and one rigid alignment per sequence, which emulate known stature and pitch calibration; the adapted lifter was tested only on unseen participants and held-out broadcast residuals (§2.5) |
| 10 | Describe the statistical analysis | §2.7 (bias, MAE, limits of agreement, ICC(2,1), calibration slope, bootstrap CIs, acceptability criteria, TOST, SPM); §2.8 (injury-study size) |
| 11 | State the actual number of raters and subjects included and the number of replicate observations | §2.1 and Table 1; §3.4 (82 participants × 2 cameras); Tables 2–4 (n per analysis) |
| 12 | Describe the sample characteristics of raters and subjects | §2.1 (CMU: 2 participants; MoVi: 83 participants, 55 female, non-footballers, air kicks) |
| 13 | Report estimates of reliability and agreement including measures of statistical uncertainty | §3.3–3.7; Tables 2–4 (bias, MAE with 95 % CI, 95 % LoA, ICC with 95 % CI); Supplementary Figures |
| 14 | Discuss the practical relevance of results | §4.1–4.4 |
| 15 | Provide detailed results if possible (e.g., online) | Supplementary file 2 (complete statistical outputs); code and aggregated results in the public repository |
