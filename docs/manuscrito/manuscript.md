---
title: "What can be measured from the broadcast? Validity of single-camera video for football-kick kinematics and swing-leg joint loads"
author:
  - "Roberto Martín Gutiérrez^1^"
date: "Preprint, October 2026"
bibliography: referencias.bib
link-citations: true
header-includes: |
  ```{=typst}
  #show table: set par(justify: false)
  #show table: set text(size: 8.5pt)
  ```
---

^1^ Independent researcher, Spain. ORCID: [0009-0004-5724-3502](https://orcid.org/0009-0004-5724-3502). Correspondence: convderover@gmail.com

**Running title:** Kick biomechanics from broadcast video

**Keywords:** football; soccer; kicking; markerless motion capture; monocular 3D pose estimation; broadcast video; inverse dynamics; injury prevention; validity

# Abstract

**Purpose.** Professional football leagues now sense the ball directly (e.g. the connected ball of LaLiga EA Sports, 2026/27), but the body that strikes it can only be observed from broadcast video. Pipelines that extract shooting posture from a single camera exist, yet their error under broadcast conditions — small players, arbitrary camera angles, 25–50 frames per second (fps) — has not been quantified, and it is unknown whether the joint loads of the kicking leg, the quantity most closely tied to kicking-related muscle injuries, can be recovered at all.

**Methods.** We combined (i) the real 2D error of a state-of-the-art detector (RTMW-x) measured on 200 broadcast shots from the English Premier League (3DSP, 6 000 detections), (ii) laboratory ground truth for 90 kicks (7 instep ball kicks, CMU; 83 participants, MoVi), (iii) a virtual broadcast camera (5 views × 5 player sizes × 25/50 fps) driven by bootstrapped broadcast residuals, (iv) a published temporal 2D-to-3D lifter (MotionAGFormer) and (v) real-video validation on MoVi recordings with synchronised motion capture, including a per-recording digital twin that tests whether the simulation predicts real-video errors, and (vi) three remedies: lab-learnt bias correction, fusion of replay angles, and a lifter adapted to kicking under broadcast noise. We evaluated six kinematic features and three swing-leg net joint moments obtained by Newton–Euler inverse dynamics (open kinetic chain, no force plates required), and estimated the size of the prospective injury study needed to validate a load-based score as an injury predictor.

**Results.** The broadcast detector error was 7.6–12.9 % of player height, more than twice that on laboratory video of the same pixel size. In the typical broadcast condition (player 80 px tall, 25 fps, replay views) leg-feature errors were 16–20°, and only kicking-knee peak flexion and backswing hip extension reached moderate between-player agreement (ICC 0.64 and 0.55); trunk leans had small errors (7°) but poor agreement, because players differ little. Frame rate did not matter (25 versus 50 fps), whereas camera view and the contact instant did: knowing the instant — as the connected ball provides — reduced errors by 25 %. The digital twin predicted real-video errors (r = 0.84, mean discrepancy 3.9°), and real-video errors were in line with simulation once a confidence-scaling pitfall was removed. Fusing three replay angles raised hip-extension agreement from 0.40 to 0.78. A lifter adapted to kicking under broadcast noise halved simulated errors and improved five features on real images, but degraded real ball kicks. The swing-leg Kick Load Index was valid in the laboratory (ρ = 0.79 with kick intensity) but not recoverable from broadcast-like video (reliability λ = 0.08): validating it as an injury predictor would require about 590 kicking-related injuries (12–24 LaLiga seasons) instead of 48 with a laboratory-grade measurement.

**Conclusions.** With open models, single-camera broadcast video supports only coarse, aggregated kicking kinematics and no joint-load or injury-risk score. Anchoring kicks to the connected ball's contact time, fusing replays and adapting models with football-specific data are the levers; an injury score should be validated prospectively only after its reliability has been raised with club data. The protocol and code are released as an open benchmark.

# 1. Introduction

Kicking is the defining skill of football, and it is also a mechanism of injury. Muscle injuries account for almost one third of all time-loss injuries in men's professional football, and adductor (23 %) and quadriceps (19 %) injuries make up a large share of them [@ekstrand2011]; hip and groin injuries alone represent 12–16 % of all injuries every season [@werner2009; @werner2019]. Kicking is one of the two main actions behind acute adductor longus injuries [@serner2019] and a principal mechanism of rectus femoris strains [@mendiguchia2013]. The biomechanics of the kick — the backswing that stretches the hip flexors, the rapid knee extension and the braking of the shank before impact — has been described in detail in the laboratory [@lees2010; @kellis2007; @nunome2002; @dorge2002; @apriantono2006; @shan2005; @charnock2009].

In matches, however, the kick is only observed through broadcast video. Since August 2026 LaLiga EA Sports instruments every match ball with an inertial/radio-frequency sensor that reports position and the instant of every touch [@laliga2026]. The ball is now measured; the body that strikes it is not. Monocular human pose estimation has advanced quickly, and several groups have started to extract kicking posture from single-camera video: AutoSoccerPose builds 2D and 3D shot-posture sequences from broadcast footage [@yeung2024], and Noworolnik and Jaworek-Korjakowska derive nine kicking features from a side-view camera to rate shooting technique with a vision–language model [@noworolnik2025]. Global 3D player pose from broadcasts is the focus of WorldPose [@jiang2024worldpose] and related methods [@khan2026; @baumgartner2023].

What is missing is a measurement-error characterisation of the kicking variables themselves under broadcast conditions. Markerless systems have been validated for gait and laboratory tasks with multiple cameras [@kanko2021; @needham2021; @uhlrich2023], and for kicking on a pitch against manual digitisation [@palucci2022], but a broadcast camera is different: shooters often occupy 30–90 pixels of image height, the camera angle is arbitrary, the frame rate is 25 or 50 fps, and images are compressed. AthletePose3D showed that, in athletic movements, monocular joint angles can be strongly correlated with motion capture while joint velocities are not [@yeung2025]. Joint loads require second derivatives of position and are therefore expected to be even more fragile — yet they are precisely the quantities a medical department would want for a "joint suffering" or injury-risk score. Without known measurement error, any broadcast-derived technique or load metric is uninterpretable, and any injury model built on it cannot be validated.

This study asks which kicking variables can be measured from broadcast-like video with open models, at which player sizes and camera views, and whether a swing-leg joint-load score is recoverable. Our contributions are: (1) the real 2D error of a modern detector on broadcast shots as a function of player size, including its temporal structure; (2) a sensitivity study that propagates that error to six kicking features and three swing-leg joint moments using laboratory ground truth from 90 kicks and a virtual broadcast camera; (3) a real-video validation with synchronised motion capture, and a digital-twin test of the simulation itself; (4) an evaluation of three practical remedies — bias correction, fusion of the replay angles a broadcast already shows, and adaptation of the 3D lifter to kicking under broadcast noise; (5) a characterisation of the kick-contact instant, which the connected ball now timestamps; and (6) a quantitative answer to what it would take to validate a broadcast-derived load score as an injury predictor in a professional league. The protocol, code and derived residual bank are released as an open benchmark so that new pose models can be evaluated on broadcast-kick validity rather than on generic joint-position error.

# 2. Methods

## 2.1 Overview

Figure {{fig:design}} summarises the design and Table {{tbl:data}} the data. Laboratory kicks with optical motion capture provide ground truth (Section 2.2). From each kick we compute six kinematic features and three swing-leg joint loads (Sections 2.3–2.4). A virtual broadcast camera films the kick at controlled player sizes, views and frame rates, and its exact 2D projections are corrupted with the 2D error that a detector actually makes on broadcast shots (Sections 2.5–2.6). A temporal lifter reconstructs 3D (Section 2.7), features and loads are recomputed and compared with the reference (Section 2.10). The same pipeline is run on real video with synchronised motion capture, and each real recording is reproduced by its digital twin (Section 2.8).

![Study design. (1) Laboratory kicks recorded with optical motion capture provide the ground truth (shown: a CMU ball kick, fading poses up to ball contact). (2) A virtual broadcast camera films each kick from five views at five player sizes and 25 or 50 fps (insets: the same instant at 200, 80 and 50 px), and its exact 2D projections are corrupted with the residuals that a detector makes on real broadcast shots; real video with synchronised capture (MoVi) and a digital twin of each recording test the simulation. (3) The 2D keypoints are lifted to 3D with MotionAGFormer, with official or kick-adapted weights. (4) Six kinematic features and three swing-leg joint moments are compared with the laboratory (bias, mean absolute error, limits of agreement, ICC with the classes of Koo and Li), and the reliability is translated into the size of the injury study needed to validate a load score.](../../resultados/paper/fig1_design.png){#fig:design width=100%}

## 2.2 Ground-truth kicks

**CMU (ball kicks).** Seven trials labelled "soccer – kick ball" from the CMU Graphics Lab Motion Capture Database [@cmu] (subject 10, trials 01–06; subject 11, trial 01), captured with a Vicon system at 120 Hz. Virtual joint centres exported by the capture software (hip HJ0, knee FE0, ankle TI0, shoulder CL0, elbow HU0, wrist WR0) were verified through segment lengths (thigh 403 mm, shank 459 mm, upper arm 293 mm, forearm 281 mm in subject 10). Three markers on the ball were available in six trials. Trial 11_01 includes a run-up; trial 10_04 is a slow kick without ball markers (peak ankle speed 4.1 m/s versus 10.2–13.1 m/s in the others). Body mass is not provided; loads are normalised by body mass, which makes them independent of it.

**MoVi (multi-subject, with video).** The F round of MoVi [@ghorbani2021] contains, for each of 90 participants (60 female, 30 male), one "kicking" action captured with 67 markers at 120 Hz (Qualisys) and processed with Visual3D, together with synchronised video from two calibrated stationary cameras (800 × 600 px, 30 fps). Height and body mass are provided. Visual3D stores joints it could not reconstruct as (0, 0, 0); these were treated as gaps, gaps of up to 0.25 s were filled by linear interpolation (also applied to CMU), and kicks with longer gaps were excluded. Eighty-three participants had a usable, gap-free kicking segment (55 female, 28 male). These are kicks without a ball performed by non-footballers, so they serve to validate the measurement chain rather than to describe football technique. We used the Visual3D joint centres (hip, knee, ankle, shoulder, elbow, wrist, head) and the four head markers. Video and capture were synchronised as capture frame = 4 × video frame; we verified this by projecting the capture with the published calibration onto the RTMW detections (best offset 0 ± 2 capture frames, 2–4 px residual at the knees and ankles).

All joint positions were expressed in metres with *z* vertical, and mapped to the 17-joint Human3.6M skeleton expected by the lifter [@ionescu2014] (pelvis as mid-hip, thorax as mid-shoulder, spine as their midpoint).

: Data sets used. {#tbl:data}

| Data set | Role | Size | Rate | Notes |
|:--------|:--------------|:----------------|:-------|:----------------|
| CMU | Ground truth: real ball kicks | 2 participants, 7 kicks | 120 Hz | Vicon; ball markers in 6 kicks; one with run-up |
| MoVi (round F) | Ground truth and real video | 83 participants, 83 air kicks, 2 cameras | 120 Hz; video 30 fps | Visual3D; height and mass; non-commercial licence |
| 3DSP | Broadcast 2D detector error | 200 Premier League shots, 6 000 detections | 25 fps | Manual 2D annotation of the shooter |

## 2.3 Kick events and kinematic features

The kicking leg is the leg whose ankle reaches the higher peak speed. The contact instant is approximated by the peak of kicking-ankle speed; in the CMU trials with ball markers we compared it with the true contact, obtained by extrapolating the ball's launch line back to its resting position (needed because the foot occludes the ball at impact in 22–57 % of frames). Six features were computed from the eight-joint skeleton (shoulders, hips, knees, ankles; Figure {{fig:model}}a–d): support-knee flexion at contact; kicking-knee peak flexion (window −0.3 s to contact); kicking-hip peak extension (same window); kicking-hip range of motion (−0.3 s to +0.2 s); trunk sagittal lean at contact (relative to world vertical, positive forward); and trunk lateral lean at contact (positive towards the support leg). Hip flexion is measured in the body frame (trunk axis, pelvis lateral axis). These features overlap with those used by previous single-camera pipelines [@noworolnik2025] and with determinants of kick performance [@lees2010; @kellis2007].

## 2.4 Swing-leg joint loads (inverse dynamics without force plates)

Between the end of the backswing and ball contact the kicking leg does not touch the ground, so the net moments at its knee and hip are fully determined by the kinematics and inertia of the thigh, shank and foot (Figure {{fig:model}}e). We used a Newton–Euler model with the body-segment parameters of de Leva [-@deleva1996] (mass fractions, centre-of-mass locations and sagittal radii of gyration for males and females). Because broadcast-compatible skeletons have no foot points, the foot was modelled as a point mass at the ankle, and segment angular velocity was computed from the segment's longitudinal axis (ω = u × u̇), which neglects axial rotation. Moments were projected onto the lateral axis of the pelvis: positive values denote knee-extensor and hip-flexor moments. Positions were low-pass filtered (4th-order zero-lag Butterworth; 12 Hz for 120 Hz capture, min(12 Hz, 0.35 × fps) for video). Three peaks, normalised by body mass (N·m/kg), were extracted: peak hip-flexor moment and peak knee-extensor moment between the end of the backswing (minimum hip flexion in the 0.3 s before contact) and contact, and peak knee-flexor moment in the 100 ms before contact (the braking of the shank by the hamstrings). The ball impact force is not modelled; all windows end at contact. A composite Kick Load Index (KLI) is the mean of the three peaks expressed as z-scores relative to the MoVi reference distribution. The identical model was applied to the reference and to the video estimates, so the comparison isolates the measurement pipeline from model simplifications. The model was verified analytically (static limb, gravity-only moment; mirror symmetry; quadratic scaling with movement speed). Figure {{fig:model}}f shows the resulting moment curves for a full and a slow kick by the same player: the full kick reaches 1.01 N·m/kg of hip-flexor moment during the forward swing and 0.89 N·m/kg of knee-flexor (braking) moment just before contact, against 0.43 and 0.12 N·m/kg in the slow kick.

![The kick model on a real ball kick (CMU 10_01, 120 Hz). (a–d) Five of the six kinematic features read from the skeleton (the sixth is the kicking-hip range of motion): kicking-hip extension at the end of the backswing (a), kicking-knee peak flexion (b), support-knee flexion and trunk sagittal lean at ball contact (c) and trunk lateral lean at contact (d); orange: kicking leg; green: support leg. (e) Free-body diagram of the swing leg 50 ms before contact: segment weights at the centres of mass, hip reaction force and net joint moments. (f) Net hip and knee moments of this kick and of a slow kick by the same player (10_04, dashed); grey band: end of backswing to contact; orange band: last 100 ms; dots: the three load peaks used as variables.](../../resultados/paper/fig2_model.png){#fig:model width=100%}

## 2.5 2D detector error on broadcast shots

We used the 3D Shot Posture dataset (3DSP) [@yeung2024]: 200 shots from English Premier League broadcasts (via SoccerNet [@deliege2021]), 20 consecutive frames per shot at 25 fps, with 17 manually annotated keypoints of the shooter. RTMW-x (384 × 288, cocktail-14 training, ONNX) [@jiang2024rtmw; @jiang2023rtmpose] was run top-down with the person box given by the annotation extent plus a 20 % margin. To probe smaller players, a quarter of the shots were also processed at 75 % and 50 % scale (6 000 detections in total). Keypoints were matched by anatomical name; matching with left and right swapped was computed as a control. We report the RMS error per image axis over 12 limb joints as a function of player height *H* (head to lowest ankle) and fitted σ(*H*) = √((*aH*)² + *b*²). Because manual annotation of small players has its own error, these values are an upper bound of the detector error.

## 2.6 Virtual broadcast camera

Each ground-truth kick was resampled to 50 or 25 fps and filmed by a pinhole camera placed 40 m from the player at 15° elevation and at azimuths of 0° (frontal), 45°, 90° (lateral, kicking-leg side), 135° and 180° (rear). The focal length was set so that the median player height was *H* ∈ {400, 200, 120, 80, 50} px. Three 2D error models were added to the exact projections: none; independent Gaussian noise with the measured σ(*H*); and a residual bootstrap in which whole 20-frame sequences of real RTMW residuals from 3DSP (matched by anatomical name, scaled by *H*, resampled in time and concatenated) are added to the projection. The bootstrap preserves temporal correlation, joint-specific error and gross failures such as left–right confusion. Above about 90 px the broadcast residuals are extrapolated by scaling. CMU kicks used three random seeds per condition and MoVi kicks one (the 83 participants provide the replication).

## 2.7 2D-to-3D lifting

We used MotionAGFormer-B with its official Human3.6M weights [@mehraban2024] (243-frame windows; test-time flip augmentation). The 2D input is normalised within a square crop centred on the pelvis with side 2 × *H*: with full-image normalisation, as in the public demo, a small player yields errors of 50–90° even without noise, because the model never saw people of that size relative to the frame. Real detections were converted from COCO to Human3.6M with the rules of the official demo. The keypoint scores returned by RTMW are un-normalised SimCC maxima (typically 3–7), whereas the lifter was trained with confidences in [0, 1]; passing them unchanged distorted the reconstruction (kicking-knee peak flexion under-estimated by 41° on average), so a constant confidence of 0.9 was used for real and simulated input alike. The reconstruction was scaled so that the median thigh length equals the reference (equivalent to knowing the player's stature) and rigidly aligned to the reference (Kabsch, rotation and translation, once per sequence; equivalent to knowing the vertical from pitch calibration). Contact was either *known* (the frame and kicking leg are given, as an analyst or a ball tracker would provide) or *automatic* (ankle-speed peak of the reconstruction).

## 2.8 Real-video validation and digital twin

For every MoVi participant and each of the two cameras, YOLOX-m [@ge2021yolox] detected the person in the original frame (the box containing the projected pelvis was kept). Images were then downscaled so that the participant measured 120, 80 or 50 px and JPEG-compressed (quality 70), or kept at native resolution (about 280–380 px); RTMW-x estimated the pose inside the scaled box. We measured the 2D error against the projected capture, lifted to 3D and computed features and loads at 30 fps. The camera azimuth relative to the participant's facing direction, the elevation (6–8°) and the distance (4–5 m) were obtained from the calibration. In the digital twin, each recording was re-simulated with the virtual camera placed at exactly that geometry and frame set, with three 2D error models: none, real RTMW residuals from the *other* MoVi participants (lab-video residuals), and broadcast residuals from 3DSP. If the twin with lab-video residuals reproduces the errors measured on real images, the simulation is valid and its broadcast-residual variant is a credible estimate of broadcast error.

## 2.9 Remedies

*Bias correction.* For each camera view, a linear calibration reference ≈ *a* + *b*·estimate was fitted on laboratory kicks and applied to unseen participants (leave-one-participant-out), and, to test transfer to football, fitted on all MoVi kicks and applied to the CMU ball kicks.

*Replay fusion.* Broadcasts usually replay a shot from several cameras. We averaged the per-view feature estimates of two (45° and 135°) or three (45°, 90°, 135°) virtual replays of the same kick; the 2D errors of different cameras were drawn independently.

*Kick- and broadcast-adapted lifter.* MotionAGFormer-B was fine-tuned on synthetic broadcast data generated on the fly from MoVi motion capture: all 21 recorded actions of the training participants, with half of the windows centred on their kick, filmed by the virtual camera at random azimuth (0–360°), elevation (5–25°), distance (15–60 m), player height (40–400 px, log-uniform) and frame rate (25 or 50 fps), with broadcast residuals (60 % of samples), Gaussian noise (20 %) or exact projections (20 %), and random left–right flipping. Targets followed the image-space 3D convention of the original training (we verified that the official model reproduces it with a scale of 0.99–1.01). We used the original loss (MPJPE + 0.5 scale-normalised MPJPE + 20 × velocity error), AdamW (learning rate 5 × 10⁻⁵, cosine decay), batches of 8 and 1 000 iterations, with gradient checkpointing and mixed precision to fit an 8 GB GPU. Participants were split into two folds; each model was evaluated only on the participants it never saw, and the CMU ball kicks were never used for training. Both lifters received exactly the same 2D input in every comparison. (MoVi's licence permits this non-commercial research use but not the deployment of such weights in a commercial product.)

## 2.10 Statistics

For each variable and condition we report bias (mean of estimate − reference), mean absolute error (MAE), 95 % limits of agreement [@bland1986], Pearson's *r*, the intraclass correlation ICC(2,1) for absolute agreement [@shrout1979] interpreted with the thresholds of Koo and Li (< 0.5 poor, 0.5–0.75 moderate, 0.75–0.9 good, > 0.9 excellent) [@koo2016], the calibration slope λ (regression of the reference on the estimate), and the smallest detectable difference between two kicks, 1.96·√2·SD(error). ICC and λ were computed across MoVi participants within a condition, with 95 % confidence intervals from 1 000 bootstrap resamples of kicks (all views of a kick resampled together). The "typical broadcast" condition is *H* = 80 px, 25 fps, broadcast residuals and known contact; replay views are 45–135°.

## 2.11 What would an injury study need?

If a load score *W* measures the true load *X* with random error, an association between *X* and injury estimated through *W* is attenuated by the reliability λ (regression dilution) [@hutcheon2010]: the log hazard ratio per standard deviation of *W* equals √λ times that per standard deviation of *X*. Combining this with Schoenfeld's formula for a continuous covariate [@schoenfeld1983], the number of injuries needed to detect a true hazard ratio HR per SD with two-sided α = 0.05 and power 0.8 is *D* = (*z*~0.975~ + *z*~0.8~)² / (λ · ln² HR). We translate *D* into LaLiga seasons assuming 20 clubs × 25 first-team players and 0.05–0.10 kicking-related adductor or quadriceps muscle injuries per player-season (0.6 muscle injuries per player-season, 42 % of them adductor or quadriceps [@ekstrand2011], of which roughly a quarter to a half are attributable to kicking [@serner2019; @mendiguchia2013]; an explicit assumption).

## 2.12 Implementation and data availability

Python 3.11, NumPy, SciPy, PyTorch 2.10 (CUDA), ONNX Runtime and rtmlib; 59 unit tests (`python -m pytest`). Code, aggregated numerical results and figures are available at {{REPO_URL}}. The datasets are not redistributed: CMU (free for research), 3DSP (research; broadcast images are copyrighted and are not shown in the publication) and MoVi (non-commercial research licence). All data are public and were collected by their owners with ethical approval; no new human data were collected.

# 3. Results

## 3.1 The contact instant

In the five CMU kicks with ball markers the peak of kicking-ankle speed preceded the true ball contact by 19.6 ms on average (range 6.8–32.2 ms; Supplementary Figure {{figS:contact}}), i.e. 1–4 capture frames and less than one broadcast frame at 25 fps. Computing the features at the ankle-speed peak instead of the true contact changed them by at most 2.1° (support-knee flexion); peak features were unaffected. The ankle-speed peak is therefore an acceptable surrogate when the contact time is unknown. One trial previously reported as a soft touch (10_06, ball speed 3.5 m/s) is in fact a full kick (peak ankle speed 11.7 m/s) whose ball was lost by the capture system three frames after impact; the slow kick of the set is 10_04 (4.1 m/s).


## 3.2 Detector error on broadcast shots

Matching by anatomical name gave a mean 2D error of 4.35 px versus 16.6 px with left and right swapped, confirming the joint correspondence. The RMS error per axis grew with player height, σ(*H*) = √((0.063 *H*)² + 3.9²) px (6 000 detections), so that its relative size fell from 12.9 % of the player's height at about 27 px to 7.6 % at about 86 px (Table {{tbl:2d}}, Figure {{fig:2d}}a). Distal joints were the least accurate: ankles 14.4 % and wrists 13.7 % of *H*, against 5.6 % for hips and 5.5 % for shoulders (Figure {{fig:2d}}b). On laboratory video downscaled to the same sizes the error of the same detector was 3.1–4.0 % of *H* (2.7 % at native resolution), i.e. broadcast images are substantially harder than laboratory images of the same pixel size.

: Real 2D error of RTMW-x on 200 Premier League shots (3DSP), by player height. {#tbl:2d}

| Player height (median, px) | Detections | RMS error per axis (px) | % of height |
|---|---|---|---|
| 26.6 | 481 | 3.45 | 12.9 |
| 36.3 | 743 | 4.37 | 12.1 |
| 45.5 | 903 | 4.73 | 10.4 |
| 55.3 | 1 388 | 5.75 | 10.4 |
| 68.0 | 2 063 | 5.90 | 8.7 |
| 85.8 | 422 | 6.50 | 7.6 |

![2D detector error. (a) RMS error per axis relative to player height on broadcast shots (3DSP, dots: frames; line: binned RMS; dashed: fitted model) and on laboratory video downscaled to broadcast sizes (MoVi). (b) Broadcast error by joint.](../../resultados/paper/fig3_2d_error.png){#fig:2d width=100%}

## 3.3 Sensitivity to camera view, player size, frame rate, noise model and contact

Without any 2D noise the lifter alone produced a mean absolute error (six features, all views and sizes, 25 fps) of 9.2° on the MoVi kicks and 15.0° on the CMU ball kicks; within MoVi the error was unrelated to kick intensity (Spearman ρ = 0.12, *p* = 0.27; Supplementary Figure {{figS:intensity}}), so the higher error of the ball kicks reflects the different, football-specific movement (run-up, impact) rather than speed alone. The camera view dominated: without noise, MoVi errors were 5.0° (lateral), 7.3° (45°), 9.0° (135°), 11.1° (frontal) and 13.6° (rear); with broadcast residuals, 11.9°, 19.0°, 13.5°, 22.6° and 20.0° respectively (Figure {{fig:sens}}; CMU in Supplementary Figure {{figS:senscmu}}). Player size had little effect between 50 and 400 px (16.8–18.2°), because the detector's relative error is almost constant over that range.

The error model mattered. Independent Gaussian noise of the measured magnitude over-stated the error with respect to the real residual sequences by a factor of 1.05–1.8 depending on the feature (e.g. kicking-hip range 42.8° versus 23.8°; Supplementary Figure {{figS:ablation}}a). The frame rate did not matter: 16.7° at 50 fps versus 17.4° at 25 fps (Supplementary Figure {{figS:ablation}}b). The contact instant did: detecting it from the reconstructed pose instead of knowing it increased the mean error from 17.4° to 23.1° (+33 %), and by 26–33 % for the leg and trunk features other than support-knee flexion (Supplementary Figure {{figS:ablation}}c).

![Virtual broadcast camera, MoVi kicks (n = 83), 25 fps, broadcast residuals, known contact: mean absolute error of each feature versus player height, by camera view.](../../resultados/paper/fig4_sensitivity.png){#fig:sens width=100%}

Figure {{fig:recon}} shows what these numbers look like on a single kick and on the average waveform. From a lateral camera the reconstructed hip flexion followed the laboratory curve closely (mean absolute difference between the group-mean curves 3.3°), and knee flexion followed it up to peak flexion, but the extension of the knee through contact was missed: the reconstructed knee stayed 18° too flexed at contact and 36° too flexed 120 ms later. From a frontal camera, where knee flexion happens mostly in depth, the reconstructed knee angle was nearly flat (85–101° against 19–86° in the laboratory) while the hip curve was still followed with a mean difference of 6°.

![What the broadcast camera sees and what is reconstructed. (a) A real ball kick (CMU 10_01) at five instants around contact: motion capture (top row); the 2D input of a lateral broadcast camera with the player 80 px tall, 25 fps and real broadcast 2D residuals (second row); and the 3D reconstructed from a lateral and from a frontal camera (blue) superimposed on the truth (grey, kicking leg orange), aligned at the pelvis. (b) Kicking-knee and kicking-hip flexion around contact, laboratory versus reconstruction from a single camera in the same condition: mean ± SD over the 83 MoVi participants; time 0 is the contact taken from the laboratory skeleton.](../../resultados/paper/fig3_recon.png){#fig:recon width=100%}


## 3.4 Agreement in the typical broadcast condition

Table {{tbl:agreement}} summarises agreement at 80 px, 25 fps, with broadcast residuals and known contact. Over the replay views (45–135°) only two features reached moderate between-player agreement: kicking-knee peak flexion (MAE 16.6°, 95 % CI 14.6–18.8; ICC 0.64, 0.55–0.71) and kicking-hip peak extension (MAE 15.7°, 13.9–17.6; ICC 0.55, 0.39–0.68). Kicking-hip range of motion (ICC 0.45) and both trunk leans (ICC 0.42) were poor despite small absolute errors for the trunk (7.0–7.1°), because the between-player standard deviation of trunk lean was itself only about 7°. Support-knee flexion was biased by +15.6° and showed no agreement (ICC 0.07); its Bland–Altman plot shows a proportional bias, the error growing with the flexion (Supplementary Figure {{figS:bland}}). The limits of agreement of the leg features spanned ±40–60°, and the smallest detectable difference between two kicks was 59–82° — larger than the range of values observed across players. Agreement was lower when all views, including frontal and rear, were considered (Figure {{fig:icc}}).

: Agreement between the broadcast-like estimate and motion capture (MoVi, n = 83; 80 px, 25 fps, broadcast residuals, known contact, replay views 45–135°). MAE and ICC with 95 % bootstrap confidence intervals; SD: between-player standard deviation of the reference. {#tbl:agreement}

| Variable | Reference SD | Bias | MAE (95 % CI) | 95 % LoA | ICC(2,1) (95 % CI) | Class |
|:---------------------|------:|-----:|----------------:|-------------:|----------------:|:-----|
| Support-knee flexion at contact (°) | 8.8 | +15.6 | 20.4 (18.8–22.1) | −25.6 to 56.8 | 0.07 (0.02–0.13) | poor |
| Kicking-knee peak flexion (°) | 28.7 | +3.0 | 16.6 (14.6–18.8) | −41.2 to 47.1 | 0.64 (0.55–0.71) | moderate |
| Kicking-hip peak extension (°) | 20.0 | +1.2 | 15.7 (13.9–17.6) | −40.9 to 43.3 | 0.55 (0.39–0.68) | moderate |
| Kicking-hip range of motion (°) | 22.0 | +2.7 | 18.0 (15.5–21.1) | −55.3 to 60.7 | 0.45 (0.31–0.63) | poor |
| Trunk sagittal lean at contact (°) | 7.0 | −1.6 | 7.1 (6.3–8.0) | −19.9 to 16.8 | 0.42 (0.28–0.54) | poor |
| Trunk lateral lean at contact (°) | 7.5 | −4.3 | 7.0 (6.2–7.9) | −19.9 to 11.3 | 0.42 (0.32–0.51) | poor |
| Peak hip-flexor moment (N·m/kg) | 0.30 | +0.54 | 0.63 (0.54–0.72) | −1.01 to 2.09 | 0.10 (0.06–0.17) | poor |
| Peak knee-extensor moment (N·m/kg) | 0.11 | +0.11 | 0.17 (0.15–0.20) | −0.38 to 0.60 | 0.16 (0.04–0.30) | poor |
| Peak knee-flexor moment (N·m/kg) | 0.08 | +0.17 | 0.21 (0.18–0.24) | −0.30 to 0.64 | 0.06 (0.00–0.12) | poor |

![Between-player agreement, ICC(2,1), by feature and camera view (MoVi, 80 px, 25 fps, broadcast residuals, known contact).](../../resultados/paper/fig6_reliability.png){#fig:icc width=80%}

## 3.5 Real video and digital twin

On the real MoVi recordings (82 participants × 2 calibrated cameras; 30 fps) the detector's 2D error against the projected capture was 2.7 % of player height at native resolution (about 330 px) and 3.1–4.0 % after downscaling to 120–50 px and JPEG compression — less than half of the broadcast error at comparable sizes. Errors of the six features grew only moderately from native resolution to 50 px (Table {{tbl:real}}, Figure {{fig:real}}a): kicking-knee peak flexion 16.5° → 24.5°, kicking-hip range of motion 16.0° → 17.7°, support-knee flexion 10.3° → 12.8° and trunk lateral lean 3.5° → 4.4°. Two features carried large systematic biases that did not depend on image size — kicking-hip peak extension (+22°) and trunk sagittal lean (−13°) — consistent with the different definitions of detector keypoints (skin-surface hips and shoulders) and biomechanical joint centres. Between-participant agreement at 80 px was good for trunk lateral lean (ICC 0.71; 0.77 at native resolution), moderate for kicking-hip range of motion (0.67) and kicking-knee peak flexion (0.56), and poor for the remaining features. Knowing the contact instant lowered the mean error from 16.2° to 14.8°.

The digital twin reproduced the real-image errors (Figure {{fig:real}}b, Supplementary Table S1). Simulating each recording with its own camera geometry and the RTMW residuals of the other participants predicted the MAE measured on real images across features, cameras and sizes with *r* = 0.84 and a mean absolute discrepancy of 3.9° (13.0° simulated versus 14.8° real), and predicted which participants would have larger errors (mean per-cell correlation of the individual errors 0.42). Without 2D noise the twin was too optimistic (8.9°), and with broadcast residuals it was more pessimistic than the laboratory images (17.6°), as expected from the larger broadcast detector error. The simulation was slightly optimistic for the two features with definitional biases (kicking-hip peak extension 17.8° versus 24.0°, trunk sagittal lean 8.9° versus 13.4°), so the broadcast errors reported in Sections 3.3–3.4 are, if anything, lower bounds.

: Real-video agreement with motion capture (MoVi, 82 participants, two cameras, known contact). MAE in degrees, with ICC(2,1) in brackets. {#tbl:real}

| Feature | Native (~330 px) | 120 px | 80 px | 50 px | Bias at 80 px |
|:----------------------|----------:|----------:|----------:|----------:|------:|
| Support-knee flexion at contact | 10.3 (0.45) | 11.4 (0.39) | 12.5 (0.27) | 12.8 (0.24) | -8.5 |
| Kicking-knee peak flexion | 16.5 (0.62) | 18.4 (0.61) | 20.3 (0.56) | 24.5 (0.48) | -8.8 |
| Kicking-hip peak extension | 22.4 (0.48) | 23.7 (0.42) | 24.1 (0.39) | 25.9 (0.29) | +23.4 |
| Kicking-hip range of motion | 16.0 (0.68) | 15.5 (0.68) | 15.5 (0.67) | 17.7 (0.57) | +3.5 |
| Trunk sagittal lean at contact | 13.1 (0.18) | 13.5 (0.16) | 13.6 (0.15) | 13.4 (0.16) | -13.4 |
| Trunk lateral lean at contact | 3.5 (0.77) | 3.8 (0.73) | 3.8 (0.71) | 4.4 (0.63) | -0.9 |

![Real-image validation. (a) MAE of each feature on real video at native resolution and downscaled to broadcast player sizes. (b) Digital twin: MAE predicted by simulating each recording with its own camera geometry versus MAE measured on the real images, for three 2D error models.](../../resultados/paper/fig7_real_video.png){#fig:real width=100%}

## 3.6 Swing-leg joint loads

The laboratory load index behaved as expected of a load measure. Each peak moment increased with kick intensity across the 83 MoVi participants (Spearman ρ = 0.56–0.58 with peak ankle speed, all *p* < 10⁻⁷), and the Kick Load Index did so strongly (ρ = 0.79, *p* < 10⁻¹⁸; Figure {{fig:load}}a). The CMU ball kicks produced peak hip-flexor moments of 1.0–2.0 N·m/kg against 0.71 ± 0.30 N·m/kg for the MoVi air kicks, and the slow CMU kick had 0.43 N·m/kg. From broadcast-like video the loads were not recoverable: the peak moments were biased upwards and their between-player agreement was poor (ICC 0.06–0.16; Table {{tbl:agreement}}, Figure {{fig:load}}b), with calibration slopes λ of 0.05–0.11 — the measured score would retain about a tenth of any true association. A ridge model predicting the laboratory loads from the six posture features (leave-one-participant-out) explained 19–34 % of their variance with laboratory kinematics (*r* = 0.45–0.59) and, applied to broadcast-estimated postures, reached λ = 0.30–0.38 — better than inverse dynamics from video, but still poor.

Under the regression-dilution model, detecting a hazard ratio of 1.5 per standard deviation of the true Kick Load Index requires 48 injuries with a laboratory-grade measurement, 126 with the posture surrogate and about 590 with inverse dynamics from broadcast-like video (Figure {{fig:load}}c). At 0.05–0.10 kicking-related adductor or quadriceps injuries per player-season, the whole of LaLiga EA Sports (≈ 500 players) would accrue 25–50 such injuries per season: about one to two seasons for a laboratory-grade score, three to five for the surrogate, and twelve to twenty-four for the current broadcast estimate.

![Swing-leg joint loads. (a) Laboratory peak hip-flexor moment versus peak kicking-ankle speed (construct validity). (b) Peak hip-flexor moment from broadcast-like video (80 px, 25 fps, replay views) versus the laboratory reference. (c) Injuries needed to detect a given hazard ratio per SD of true load as a function of the reliability λ of the measured score; horizontal lines: injuries accrued by the whole league in one season at two assumed incidences.](../../resultados/paper/fig8_joint_load.png){#fig:load width=100%}

## 3.7 Remedies

*Replay fusion.* Averaging three replay angles (45°, 90°, 135°) raised between-player agreement over a single 45° camera for kicking-hip peak extension (ICC 0.40 → 0.78, now "good"; MAE 19.3° → 9.4°), kicking-knee peak flexion (0.61 → 0.76), hip range of motion (0.32 → 0.66) and trunk sagittal lean (0.48 → 0.68), and also over the single lateral view for every feature except trunk lateral lean (Figure {{fig:improve}}). Two replays (45° and 135°) captured most of the gain.

*Bias correction.* A view-specific linear correction learnt on laboratory kicks reduced absolute errors where bias was large (support-knee flexion, 12.9–34.7° → about 7°) but did not increase between-player agreement — it cannot add information — and, learnt on the MoVi air kicks and applied to the CMU ball kicks, it made them markedly worse (support-knee flexion 4.8° → 31.2°, kicking-hip peak extension 7.1° → 27.8°).

![Remedies at 80 px and 25 fps (MoVi, unseen participants): single lateral camera versus fusion of three replays, each without and with lab-learnt bias correction.](../../resultados/paper/fig9_improvements.png){#fig:improve width=100%}

*Kick- and broadcast-adapted lifter.* Fine-tuning reduced the 3D error (MPJPE, in units of player height) on the held-out participants' synthetic broadcast windows from 0.096 to 0.035 and 0.037 in the two folds (−62 %). On the virtual camera at 80 px (unseen MoVi participants, replay views) the mean feature error fell from 14.3° to 7.8° and five of the six features reached good between-player agreement (ICC 0.75–0.83; support-knee flexion 0.10 → 0.50; Supplementary Table S2, Figure {{fig:finetune}}a). Because the same bank of broadcast residuals was used for training and for this test, these figures are an upper bound. On real video downscaled to 80 px — real detections on images the model never saw — the gain was smaller but consistent for five features (mean error 15.0° → 13.1°; kicking-hip range of motion ICC 0.67 → 0.76, kicking-knee peak flexion 0.56 → 0.67, trunk lateral lean 0.71 → 0.76, trunk sagittal lean error 13.6° → 10.1°), while support-knee flexion worsened slightly (12.5° → 14.5°). On the CMU ball kicks, which are absent from the training data, the adapted lifter was worse than the official one (mean error 12.0° → 17.9°; kicking-hip range of motion 19.7° → 36.9°; Figure {{fig:finetune}}b): adaptation to air kicks does not transfer to football kicks with run-up and impact. Joint loads remained unreliable after adaptation (ICC ≤ 0.33).

![Official versus kick- and broadcast-adapted MotionAGFormer on (a) the virtual camera with unseen MoVi participants, (b) the virtual camera with the CMU ball kicks, never used in training, and (c) real video downscaled to 80 px. Mean absolute error; 80 px, broadcast residuals or real detections, known contact.](../../resultados/paper/fig10_finetune.png){#fig:finetune width=100%}


# 4. Discussion

## 4.1 What broadcast video can and cannot measure today

With open, general-purpose models, broadcast-quality video does not deliver individual-level kicking kinematics. In the typical broadcast condition the error of the leg features was of the order of 15–20°, comparable to or larger than the differences between players, and only the kicking-knee peak flexion and the backswing hip extension reached moderate agreement between players. Two results deserve emphasis because they run against intuition. First, a small absolute error is not enough: the trunk leans were measured with errors of about 7°, yet their agreement between players was poor, because players differ little in those variables — a broadcast metric must be judged against the spread of the population it will rank, not against its own error. Second, the frame rate did not matter (25 versus 50 fps), whereas the camera view, the contact instant and the detector's error at small player sizes did. Improving broadcast biomechanics is therefore not a matter of higher frame rates but of better 2D detection of small players, of choosing the right camera, and of knowing when the foot meets the ball.

The structure of the 2D error also matters for the conclusions a study reaches. Independent Gaussian noise of the same magnitude as the real detector error over-stated the error of several features by up to 1.8 times, because frame-to-frame jitter is more destructive for a temporal lifter than the temporally correlated errors a real detector makes. Simulations of video-based biomechanics should use real residual sequences, as we did, or, better, validate themselves against real images: the digital twin showed that a simulation driven by real residuals predicts real-image errors closely (r = 0.84, mean discrepancy 3.9°) and, if anything, slightly under-estimates them.

## 4.2 The connected ball and the body

The single most effective piece of information in our experiments was the contact instant. Detecting it from the reconstructed pose (ankle-speed peak) increased the error of the leg features by a third (mean absolute error 23.1° versus 17.4°) relative to knowing it. In LaLiga EA Sports this instant is now measured by the connected ball for every touch [@laliga2026], at the sub-frame resolution that our CMU analysis shows is sufficient (the ankle-speed peak precedes the true contact by about 20 ms, less than one broadcast frame, and changing the instant by that amount alters the features by at most 2°). Fusing the ball's timestamp with the broadcast pose is therefore not a marginal refinement but a prerequisite for usable kick biomechanics from video. Replays add a second, free source of improvement: averaging the three replay angles raised between-player agreement for every leg and trunk feature except support-knee flexion, lifting kicking-hip peak extension from poor to good (ICC 0.40 → 0.78 relative to a single 45° camera).

## 4.3 A joint-load ("joint suffering") score: measurable in the lab, not yet from television

The swing-leg inverse-dynamics model behaved as a load measure should: the Kick Load Index increased steeply with kick intensity across 83 participants (Spearman ρ = 0.79), the CMU ball kicks loaded the hip flexors two to three times more than the gentle air kicks of MoVi, and the only slow CMU kick had a third of the load of the full kicks. Peak hip-flexor and knee-extensor moments are the mechanical counterpart of the eccentric demand placed on rectus femoris and iliopsoas during the backswing-to-forward-swing transition, the phase implicated in rectus femoris and adductor injuries [@mendiguchia2013; @serner2019; @charnock2009]. From broadcast-like video, however, the same score could not be recovered: its reliability fell to λ ≈ 0.08, because inverse dynamics needs second derivatives of joint positions that a 25-fps reconstruction does not contain. A posture-only surrogate, which predicts the laboratory load from the six angles, was more robust (λ ≈ 0.38) but explained only about a third of the variance of the load even with perfect laboratory kinematics.

This has a direct consequence for anyone who wants an "injury score" from broadcast video. Measurement error attenuates any true association with injury, so the number of injuries a validation study needs grows as 1/λ. With a laboratory-grade measurement, detecting a hazard ratio of 1.5 per standard deviation of load would require about 48 kicking-related injuries — one to two LaLiga seasons at our assumed incidence. With today's broadcast estimate the requirement rises to about 590 injuries, about twelve to twenty-four seasons of the whole league, and a study of that length would be confounded by changes in squads, training and medical practice. The practical path is therefore not to fit an injury model on broadcast features now, but first to raise the reliability of the measurement — with football-specific adaptation, multi-view input and the connected ball — and only then to run a prospective study with the clubs' medical departments.

## 4.4 What it takes: football-specific data

Two remedies were cheap and useful. Lab-learnt bias corrections lowered the absolute error where the bias was large (for example the support-knee flexion), but they do not add information and, crucially, a correction learnt on air kicks made the errors of real ball kicks worse (for example support-knee flexion 4.8° → 31.2° and kicking-hip peak extension 7.1° → 27.8°). Adapting the lifter to kicking under broadcast noise roughly halved the simulated error for unseen participants and improved five of six features on real images, but made the CMU ball kicks worse (mean error 12.0° → 17.9°). Both findings point to the same bottleneck: models and corrections must be trained and validated on football kicks — shots with run-up and ball impact, filmed by broadcast cameras with synchronised 3D. Such data exist inside clubs (biomechanics laboratories, multi-camera training-ground systems) and leagues (stadium camera rigs used for tracking), and this is where a club-level collaboration would add most value. The protocol released with this paper turns any such dataset into a validation benchmark within hours.

Two implementation details had first-order effects and are easy to get wrong. Normalising the 2D input to the full broadcast frame, as the public demo does, made small players unreadable for the lifter (errors of 50–90° without any noise); a crop centred on the player removes this. And feeding the detector's raw keypoint scores as confidences, which for RTMW are not probabilities, biased the reconstructed kicking-knee flexion by about 40°. Neither problem produces an error message — only wrong biomechanics.

## 4.5 Recommendations for analysts and medical departments

1. Treat broadcast-derived leg angles of individual shots as unreliable unless the player measures at least 80 px, the view is lateral or 45°, and the contact instant is known; aggregate several replays and several shots per player.
2. Do not interpret trunk-lean differences between players as real without checking the between-player spread of the population being ranked.
3. Do not use broadcast inverse dynamics, joint velocities or loads for individual decisions; if a load index is needed, prefer posture-based surrogates and report their reliability.
4. Anchor every kick to the connected-ball contact time.
5. Before deploying any vendor metric of technique or load, ask for its agreement with motion capture under broadcast conditions — the protocol presented here provides one.

## 4.6 Limitations

The ground truth is laboratory-based. Only seven kicks (two participants) are genuine football kicks with a ball; the 83 MoVi kicks are air kicks by non-footballers, slower than match shots, and the lifter's errors were larger for the ball kicks (15.0° versus 9.2° without 2D noise), so the errors reported here are probably optimistic for full-power match shots. The 2D error was measured on 200 broadcast shots of one competition with manual annotations that include their own error (an upper bound of detector error), and it is extrapolated by scaling for players taller than about 90 px. The virtual camera reproduces geometry, size, frame rate and detector error, but not motion blur, occlusion by other players or the moving broadcast camera; the digital twin addresses this only for laboratory images. Real-video validation used two fixed cameras at 4–5 m rather than stadium cameras. Scale and the vertical were given (stature and pitch calibration); in practice both add error. Joint loads were computed with a simplified model (no foot inertia, no axial rotation, no ball impact), identical for reference and estimate, so they quantify measurability rather than absolute tissue loading. Injury incidence for the feasibility analysis is an explicit assumption, not a measurement. The broadcast residual bank used to fine-tune the lifter was also used in the corresponding virtual-camera test, so that gain is an upper bound; the real-video test is free of this overlap. Finally, we evaluated one detector and one lifter; other models may perform differently, which is why the benchmark is released.

## 4.7 Future work with a club or league

A prospective Phase 2 would combine (i) broadcast and tactical-camera video of every shot, (ii) the connected-ball contact time and ball speed, (iii) club motion-capture or multi-camera sessions of the same players for football-specific adaptation and validation, and (iv) the medical department's injury records. The first deliverable would be a reliability report per feature and camera; only features that reach λ ≥ 0.75 would enter an injury model, keeping the prospective study within one to two seasons.

# 5. Conclusions

1. Broadcast detection is the bottleneck. Its error is about 10 % of a typical shooter's height, more than twice that on laboratory video, and its temporal structure matters: Gaussian noise models over-state its effect by up to 1.8 times.
2. With open models, kicking-knee peak flexion and backswing hip extension are the only kinematic features with moderate between-player agreement from a single broadcast camera. Support-knee flexion is not measurable. Trunk leans have small errors but cannot rank players.
3. Frame rate is irrelevant between 25 and 50 fps. Camera view and the contact instant are decisive, and the connected ball's timestamp reduces errors by a quarter.
4. Replay fusion is a free improvement. Adaptation with synthetic broadcast data helps within the movement it was trained on but did not transfer to real ball kicks, so football-specific training and validation data are required.
5. A swing-leg joint-load index is valid in the laboratory but not measurable from broadcast today. With current reliability, validating it as an injury predictor would take a decade of league-wide injury data. The route is to raise reliability first, with club motion capture, the connected ball and multi-view input, and then run a prospective study with medical departments.

# Acknowledgements

The CMU data used in this project was obtained from mocap.cs.cmu.edu; the database was created with funding from NSF EIA-0196217. We thank the BioMotion Lab (MoVi), the authors of 3DSP/AutoSoccerPose and SoccerNet, OpenMMLab (RTMW, YOLOX) and the authors of MotionAGFormer for releasing their data and models.

# Funding

This research received no specific funding.

# Conflict of interest

None. The author works as a Research Engineer in AI & Computational Cardiology at ICICOR – Hospital Clínico Universitario de Valladolid (HCUV); this study was carried out independently, outside that position, and used no institutional resources or data.

# References

::: {#refs}
:::

# Supplementary figures

<!-- SUPLEMENTO -->

![Ankle-speed peak versus true ball contact in the CMU ball kicks. (a) Kicking-ankle speed aligned to the extrapolated contact; dots mark the speed peak. (b) Offset of the peak relative to contact; the grey band is one frame at 25 fps.](../../resultados/paper/fig2_contact.png){#figS:contact width=100%}

![Effect of (a) the 2D error model, (b) the frame rate and (c) knowing the contact instant, at 80 px.](../../resultados/paper/fig5_ablation.png){#figS:ablation width=100%}

![Virtual broadcast camera, real ball kicks (CMU, n = 7), 25 fps, broadcast residuals, known contact: mean absolute error of each feature versus player height, by camera view.](../../resultados/paper/figS1_sensitivity_cmu.png){#figS:senscmu width=100%}

![Lifter error without 2D noise (mean absolute error of the six features, all views and sizes, 25 fps) versus kick intensity (peak kicking-ankle speed). MoVi air kicks and CMU ball kicks.](../../resultados/paper/figS2_intensity.png){#figS:intensity width=60%}

![Bland–Altman plots of the six kinematic features in the typical broadcast condition (MoVi, n = 83; 80 px, 25 fps, broadcast residuals, known contact; replay views 45°, lateral and 135°). Solid line: bias; dashed lines: 95 % limits of agreement.](../../resultados/paper/figS3_bland.png){#figS:bland width=100%}
