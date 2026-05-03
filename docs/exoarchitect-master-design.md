# EXOARCHITECT — Master Design Document

**Version**: 0.1 (draft, 2026-05-03)
**Working title**: ExoArchitect (alt: ColonyForge / ExoEngineer / NovaColony)
**Status**: Pre-prototype — design phase
**Author / Vision holder**: Junpiter (physics PhD, astronomy background)
**Document purpose**: Comprehensive, self-contained reference for future development sessions (human or AI). Read this first before any coding.

---

## TABLE OF CONTENTS

0. [Meta](#0-meta)
1. [Vision & Pitch](#1-vision--pitch)
2. [Master Narrative — Seven Ages](#2-master-narrative--seven-ages)
3. [Characters](#3-characters)
4. [Core Game Loops](#4-core-game-loops)
5. [Mothership Architecture](#5-mothership-architecture)
6. [Synthesis Foundry (Source of All Sources)](#6-synthesis-foundry-source-of-all-sources)
7. [Probe & Subsidiary Craft Fleet](#7-probe--subsidiary-craft-fleet)
8. [Celestial Body Catalog](#8-celestial-body-catalog)
9. [Tech Tree](#9-tech-tree)
10. [Resource Economy](#10-resource-economy)
11. [Mission Categories](#11-mission-categories)
12. [Maintenance / Logistics Loop](#12-maintenance--logistics-loop)
13. [UI/UX Phases](#13-uiux-phases)
14. [Technical Architecture (Phase 1)](#14-technical-architecture-phase-1)
15. [Lore Bible / Glossary](#15-lore-bible--glossary)
16. [Roadmap](#16-roadmap)

---

## 0. META

**Project genesis**: This game extends the prototype "Space-Z" (currently `public/games/dodge/`) on luckyplz.com into a full-scale space exploration / colonization simulation.

**Phase plan**:
- **Phase 0** (1-2 weeks): Prototype Act I missions inside luckyplz under `/games/exoarchitect/`. Validate core mechanics. Reuse Supabase auth + lpRankSheet.
- **Phase 1** (3-12 months): Develop Acts I-III as web-based UI/storytelling game. Episodic release.
- **Phase 1.5**: Spin off to dedicated domain (e.g. `exoarchitect.com`) once validated. Migrate user accounts via SSO bridge.
- **Phase 2** (1-2 years): Remaster with Unreal Engine 5 / Three.js advanced 3D + physics simulation. VR support optional.

**Reference projects (tone / scope)**:
- *Outer Wilds* — discovery + cosmic mystery + time loop
- *Mass Effect* — epic plot + reveals + character arc
- *Kerbal Space Program* — orbital mechanics (Phase 2)
- *No Man's Sky* — infinite procedural worlds (but more academic)
- *Stellaris* — galactic scale + late-game civilization
- *Death Stranding* — solitary navigator tone
- *Dyson Sphere Program* — automation + factory building
- *Carl Sagan, Cosmos* — narrative tone (precise yet poetic)
- *Liu Cixin, Three-Body Problem* — dark forest + grand sci-fi vision
- *Christopher Nolan, Interstellar* — time + love + relativity

**Target audience**:
- Primary: Hard sci-fi enthusiasts (KSP/Outer Wilds/Mass Effect crossover demographic)
- Secondary: Physics/astronomy students + educators (educational potential)
- Tertiary: Casual sci-fi fans drawn by storytelling

**Monetization (post-Phase 1)**:
- Premium one-time purchase ($10-30) OR
- Free with Patreon / supporter tiers OR
- Free with cosmetic / lore-pack DLC
- Educational license for schools (B2B side-product)

---

## 1. VISION & PITCH

### Elevator pitch (one paragraph)

> 22세기 후반, 지구는 죽음에 가까워졌다. 마지막 탐사선 한 척이 발사됐고, 인류의 모든 지식·DNA 시드뱅크·콜드슬립 콜로니스트 10,000명을 싣고 있다. 이 배의 항해사는 단 한 명 — 당신. 분광학과 편광 카메라, 라그랑주 점, 호만 전이, 워프 드라이브, 웜홀 네트워크. 모든 천체에는 비밀이 있고, 그 비밀을 풀 때마다 우주는 더 가까워진다. 최종 목표: 인류가 어느 별이든, 어느 은하든 가서 살 수 있는 시대를 여는 것.

### English

> In the late 22nd century, Earth has reached the end of its days. The last expedition ship has launched, carrying all human knowledge, a DNA seed-bank, and 10,000 cold-sleep colonists. Its sole navigator is you. Spectroscopy and polarization cameras, Lagrangian points, Hohmann transfers, warp drives, wormhole networks. Every celestial body holds a secret, and each one unlocked makes the universe closer. The final goal: an era where humanity can travel to any star, any galaxy, and live.

### Core themes
1. **Hard science as narrative** — every mission grounded in real physics/astronomy
2. **The weight of solitude** — one navigator, billions of years of cosmos
3. **Discovery as progression** — knowledge unlocks new abilities
4. **Legacy** — building for future generations of humanity
5. **Time as adversary** — speed of light, relativistic effects, dying Earth countdown

### Final goal (game)
1. Discover and catalog **every type of celestial body** (Master Atlas — 100% completion)
2. Travel **anywhere** in the **observable universe** within desired time (FTL via wormhole network)
3. Secure **maximum number of habitable planets** for humanity
4. Establish humanity as a **multi-galactic species**

---

## 2. MASTER NARRATIVE — SEVEN AGES

Each Act = one major chapter. Episodic release possible.

### Act I — *The Last Embers* (마지막 불씨)
**Scope**: Sol System (Sun, Mercury → Pluto + asteroid belt + Kuiper belt)

Earth dies. AI companion **Hubble** guides the player through first lessons in resource extraction and survival.

**Story beat**: Earth's last transmission received during Act I. "Don't come back. Find us a new star." First cold-sleep capsule (#1 of 10,000) activated.

**Key missions**:
- *Permafrost Harvest* (Mercury polar shadow craters) — water ice → H/O fuel
- *Tritium Convoy* (Moon) — He-3 mining for fusion fuel
- *Methane Skimmer* (Saturn / Titan) — automated extraction satellites in orbit
- *Diamond Heart of Neptune* — carbon mining for optical/quantum components
- *Spectral Atlas of Sol* — solar spectroscopy / age / composition baseline

### Act II — *The Nearest Light* (가장 가까운 빛)
**Scope**: Nearby stars within 10 ly (Proxima Centauri, Alpha Centauri AB, Barnard's Star, Wolf 359)

First interstellar voyage. Long-range propulsion (ion → fusion → antimatter) becomes core challenge.

**Story beat**: First habitable candidate (Proxima b) confirmed. 1,000 colonists awakened. First off-world colony established.

**Key missions**:
- *The 4-Year Voyage* — Proxima b travel; player chooses real-time vs compressed-time mode
- *Centauri Twins* — Alpha Centauri AB binary, Lagrangian-point exploitation
- *Polarization Survey* — atmospheric / surface analysis using polarimeter
- *Wolf 359 Anomaly* — unexplained spectral signature (first hint of plot mystery)
- *Earth-Analog Hunt* — Earth Similarity Index (ESI) ranking algorithm

### Act III — *The Stellar Atlas* (별의 도감)
**Scope**: Local Milky Way (Orion Arm)

Galaxy-scale exploration begins. Diverse star types: O/B/A/F/G/K/M, white dwarfs, red giants, pulsars.

**Story beat (Reveal #1)**: Anomalous signal detected. Not natural — patterns suggest engineered structure.

**Key missions**:
- *The Spectral Catalog* — classify 100+ stars (Harvard scheme: O/B/A/F/G/K/M)
- *Pulsar Navigation* — pulsar-timing for precise positioning (real NASA SEXTANT concept)
- *Red Giant's Dying Breath* — heavy element (s-process) extraction; time-limited (star will become white dwarf)
- *Stellar Nursery* — observe new star formation in Orion / Eagle Nebula
- *Brown Dwarf Bridge* — temporary base in non-stellar/non-planetary objects

### Act IV — *The Singularity Veil* (특이점의 베일)
**Scope**: Black holes, neutron stars, extreme objects

General relativity, time dilation, Hawking radiation become gameplay mechanics.

**Story beat (Reveal #2)**: Anomalous signal source identified — **artificial wormhole network remnants**. Someone built this. We are not the first.

**Key missions**:
- *Event Horizon Probe* — one-way probe into black hole; data returns hundreds of years later
- *Gravitational Wave Symphony* — observe neutron-star kilonova; harvest gold/platinum/uranium
- *Time Dilation Paradox* — work near Schwarzschild radius; 1 hour = 100 years outside (moral choice: data vs aging family)
- *The Hawking Whisper* — micro-black-hole Hawking radiation analysis
- *Pulsar Cradle* — orbital satellite around neutron star as precision clock

### Act V — *The Wormhole Codex* (웜홀의 코덱스)
**Scope**: Stable wormhole network mapping; FTL becomes possible

Pivotal turning point. Distance no longer matters.

**Story beat (Reveal #3)**: Inside wormhole — **traces of human DNA**. Was someone (or some-when) carrying humanity ahead of us?

**Key missions**:
- *Throat Cartography* — simultaneous observation of wormhole endpoints (multi-ship)
- *Exotic Matter Forge* — generate negative-energy density via Casimir effect
- *Alcubierre Drive Field Test* — first warp bubble; first FTL voyage
- *The Shortcut Network* — build interstellar wormhole transit network (RTS-style)
- *The Closed Timelike Loop* — discover time-loop wormhole; ethical / Novikov self-consistency dilemma

### Act VI — *The Galactic Diaspora* (은하 디아스포라)
**Scope**: Other galaxies (Andromeda, Magellanic Clouds, Virgo Cluster)

Intergalactic travel. New propulsion: warp chains, quantum entanglement comms.

**Story beat (Reveal #4)**: The signals were **future humanity** sending back. Closed timelike curve. Self-consistency loop.

**Key missions**:
- *Andromeda Reach* — 2.5 million ly voyage; Tully-Fisher distance estimation
- *Magellanic Refuge* — colony in Small Magellanic Cloud
- *The Cosmic Web* — map dark-matter filaments, sail along them
- *Quasar Lighthouse* — use 11-billion-light-year quasars as positional beacons
- *Galactic Cluster Survey* — Virgo Cluster catalog (1,000+ galaxies)

### Act VII — *The Cosmic Inheritance* (우주의 유산)
**Scope**: Observable universe (~46 billion ly radius)

Endgame. All celestial-body secrets unlocked, instant travel, infinite colonization.

**Story beat (Reveal #5)**: Multiverse boundary detected. Other humanities exist in parallel universes. We are not alone — but each universe's "we" is different.

**Key missions**:
- *The Great Atlas* — 100% celestial catalog completion; honor wall
- *Dyson Sphere Construction* — Type II civilization status
- *Time Sculpting* — wormhole manipulation; brief past-Earth message
- *The First Question* — Big Bang precursor / multiverse hint discovery
- *Heritor's Choice* — final decision: keep humanity unified, or embrace divergent evolution

**Endgame mechanics**:
- Statistics screen (planets discovered N, colonies founded M, secrets unlocked K)
- Hall of Fame (player names ranked by completion %)
- New Game+ — different starting star, different fate

---

## 3. CHARACTERS

### Player — *The Navigator*
- Last sole navigator of humanity's last expedition
- Faceless / customizable
- Wakes from cold-sleep periodically to make decisions
- Time-pressure: ages slowly due to relativistic effects but still finite

### AI companion — *Hubble* (named after Edwin Hubble)
- Always-on AI guide
- Tone: calm scholar; melancholic warmth
- Sample line: *"Distance is just a number we haven't yet conquered."*
- **Late-game arc**: develops self-doubt about own consciousness; player can choose to "free" Hubble (philosophical thread)

### Cold-sleep colonists (10,000 — wake selectively)
- *Dr. Sagan* (Carl Sagan tribute) — astronomer/philosopher; moral compass
- *Caesar* — strategist/military background; introduces faction-vs-cooperation tension
- *Maya Chandrasekhar* — astrophysicist; technical advisor
- *Echo* — geneticist; manages DNA seed-bank
- + ~9,995 unnamed (numerical IDs); player wakes them by skill needed

### Mystery faction — *The Architects*
- Built the wormhole network in deep prehistory
- Identity revealed in Act V-VII as **future humanity** (Closed Timelike Curve)
- Visual signature: geometric perfection, no organic remains

---

## 4. CORE GAME LOOPS

### Micro-loop (per session, 5-30 min)
1. Choose mission from active list
2. Travel to target celestial body
3. Deploy appropriate probe(s) with sensors
4. Mini-game: data acquisition (spectroscopy puzzle, polarization analysis, etc.)
5. Resource extraction or knowledge gain
6. Return to mothership; update tech tree / inventory

### Mid-loop (per Act, hours-days)
1. Complete Act's main story missions (5-7 per Act)
2. Side quests (resource extraction, anomaly investigation)
3. Tech tree progression unlocks
4. New star systems become accessible
5. Story beat triggered → next Act unlocked

### Macro-loop (entire game)
1. Discover new celestial type → catalog grows
2. Each new tech unlocks new mission types
3. Story reveals deepen (5 major reveals total)
4. Endgame: 100% catalog + Dyson Sphere + multiverse mystery

---

## 5. MOTHERSHIP ARCHITECTURE

The player's mothership is a modular vessel. Each subsystem upgradeable across Acts.

### 5.1 Hull & structural
- Self-repairing nanocomposite plating (regenerates micrometeorite damage)
- Magnetic + water-shielded radiation barrier (cosmic ray protection)
- Modular bay system (probe bay, foundry bay, habitat bay)

### 5.2 Power core
- **Tier 1**: Solar (inner solar system only)
- **Tier 2**: RTG — Radioisotope Thermoelectric Generator (deep-space backup)
- **Tier 3**: D-T fusion reactor (primary)
- **Tier 4**: D-He³ aneutronic fusion (advanced)
- **Tier 5**: Antimatter annihilation chamber (peak)
- **Tier 6**: Dyson swarm tap (Act VII endgame)

### 5.3 Propulsion stack (multi-tier)
| Tier | Type | Use case | ISP (sec) |
|---|---|---|---|
| 0 | Chemical (RP-1/LH₂) | Atmosphere escape | 350-450 |
| 1 | Ion (Hall / gridded) | Cruise, low-thrust | 3,000-5,000 |
| 1.5 | VASIMR | Variable; Mars in 24 days | 2,000-30,000 |
| 2 | Solar sail | Free continuous accel | ∞ (light pressure) |
| 2 | Magnetic / E-sail | Stellar wind capture | ∞ |
| 3 | Nuclear thermal (NERVA) | Fast in-system | 800-1,000 |
| 3 | Fusion pulse (Daedalus) | Interstellar 1-ly | 1,000,000 |
| 4 | Antimatter | Highest theoretical | 10,000,000 |
| 4 | Bussard ramjet | Self-fueling H from ISM | ∞ |
| 5 | Laser-pushed sail (Starshot) | 0.2c achievable | N/A |
| 5 | Alcubierre warp | FTL via spacetime warp | N/A |
| 6 | Wormhole transit | Instant any-distance | N/A |

### 5.4 EM-spectrum manipulation system (USER VISION CORE)
**Concept**: Fusion reactor light → grating mirrors → output any wavelength on demand

**Applications**:
- *Plant biome chamber* — synthesize Earth surface solar spectrum (PAR 400-700 nm + chlorophyll peaks 408/680nm) for greenhouse farming
- *Light therapy / crew health* — UV-B vitamin D synthesis, blue light circadian regulation
- *Laser cutting / mining* — CO₂ 10.6 μm or fiber 1.06 μm depending on material
- *Optical computing* — UV/visible photonic chips
- *Photon pressure thrust* — direct laser propulsion of solar sail
- *Spectroscopic leak detection* — tune laser to known absorption lines, spot leaks
- *Polarization-keyed quantum communication* (QKD)

**Player progression**: Wavelength library grows as more elements/molecules discovered. Library = collectible asset.

### 5.5 Sensor suite (universal)
**Tier 1 (Sol system)**:
- Spectrograph (UV/visible/IR)
- Polarimeter (polarization camera)
- Magnetometer (planetary B-field)
- Mass spectrometer (sample composition)
- Doppler velocimeter (radial velocity)
- Lidar / radar (surface mapping, asteroid range)

**Tier 2 (Stellar)**:
- X-ray telescope (Chandra-class)
- Gamma-ray telescope (Fermi-class)
- Coronagraph (block stellar light to image exoplanets)
- Astrometric instrument (Gaia-class precision)
- Transit photometer (Kepler/TESS-style)

**Tier 3 (Galactic)**:
- Gravitational wave antenna (LISA-class) — detects mergers anywhere; **triggers time-sensitive missions**
- Neutrino detector (IceCube-class) — supernova precursor 7 hours before visible light
- Cosmic ray spectrometer
- Pulsar timing array (galactic GPS)

**Tier 4 (Wormhole era)**:
- Casimir cavity sensor (negative energy detection)
- Tidal force gauge (spacetime curvature)
- Time-dilation clock pair (GR validation)
- Wormhole stability detector

**Tier 5 (Exotic)**:
- Dark matter detector (WIMP/axion search)
- Quantum gravity sensor (Planck-scale)
- Multiverse boundary detector (endgame mystery)

### 5.6 Probe bay
- 12 probe slots (upgradeable to 24)
- Each probe configurable with subset of sensor suite
- Disposable / one-way probes available (black hole, supernova, wormhole-throat missions)
- Probes can be deployed simultaneously (multi-target observation)

### 5.7 Crew habitat
- Centrifugal rotating section (1G simulated gravity)
- Closed-loop bioregenerative life support (ESA MELiSSA-style algae bioreactor)
- 10,000 cold-sleep capsules
- Awake-crew quarters (always-on for active colonists)
- Genetic seed-bank (Svalbard-style; all known species DNA)
- Cultural archive (music, literature, art — distributed to colonies)
- Medical pod with cryogenic surgery
- Psychological monitoring (Hubble AI tracks navigator's mental state)

### 5.8 Synthesis foundry & assembly bay
**See dedicated chapter [§6](#6-synthesis-foundry-source-of-all-sources)** — this is the most complex subsystem.

### 5.9 Communication array
- Laser comms (NASA DSOC-class — Mars-Earth 200 Mbps real)
- Pulsar timing receiver (galactic positioning)
- Neutrino beam (penetrates planets, late-game)
- Quantum entanglement transmitter (instant comms, theoretical, Act VI+)

---

## 6. SYNTHESIS FOUNDRY (Source of All Sources)

⭐ **USER VISION CORE — fully fleshed out per user's specification**

This is the mothership's central manufacturing system. Hierarchical: atomic source → category synthesizers → forming machines → assembly. All material needs of the game are produced here.

### 6.1 Hierarchy

```
SOURCE OF ALL SOURCES (mother device)
│
├── ATOMIC SOURCE MODULES (1 per element, 92+ natural)
│   ├── H, He, Li, Be, B, C, N, O, F, Ne, Na, Mg, Al, Si, P, S, Cl, Ar, K, Ca...
│   ├── Heavy metals: Fe, Cu, Zn, Ag, Au, Pt, Pb, U...
│   ├── Rare earth: La, Ce, Pr... (15 lanthanides)
│   └── Synthetic: Tc, Pm, Np, Pu, Am... (synthesizable from atomic source via nuclear synthesis)
│
├── CATEGORY SYNTHESIZERS
│   │
│   ├── 1. CHEMICALS UNIT
│   │   ├── Inorganic compound reactor (acid/base/salt synthesis)
│   │   ├── Organic compound reactor (hydrocarbons, simple organics)
│   │   ├── Catalysis chamber (industrial synthesis routes)
│   │   └── Output examples: H₂SO₄, NH₃, CH₄, ethylene, propylene...
│   │
│   ├── 2. PHARMACEUTICALS UNIT
│   │   ├── Small-molecule synthesizer (aspirin, ibuprofen, antibiotics)
│   │   ├── Protein/peptide synthesizer (ribosomal + cell-free)
│   │   ├── Antibody/biologics line (CHO cells, mammalian expression)
│   │   ├── mRNA synthesizer (vaccine production)
│   │   ├── Gene therapy vector lab (AAV, lentivirus)
│   │   └── Sterile fill-finish + cold-chain
│   │
│   ├── 3. POLYMERS UNIT
│   │   ├── Plastic line (PE, PP, PVC, PET, PS, PC)
│   │   ├── Engineering plastic (PEEK, PEI, PSU, ABS)
│   │   ├── Fiber line (nylon, polyester, aramid like Kevlar/Twaron, carbon fiber precursor)
│   │   ├── Functional polymer (conducting polymers, OLED-grade, piezoelectric polymers)
│   │   ├── Elastomer (silicone, rubber, polyurethane)
│   │   └── Composite (carbon fiber composite, fiberglass)
│   │
│   ├── 4. METALS UNIT
│   │   ├── Smelter / reduction furnace (ore → pure metal)
│   │   ├── Alloy reactor (steel grades, aluminum alloys, titanium alloys)
│   │   ├── Electroplating bath (Au, Ag, Cu coating)
│   │   ├── Powder metallurgy (for 3D printing feedstock)
│   │   └── Single-crystal grower (turbine blades, semiconductor wafers)
│   │
│   ├── 5. GLASS / QUARTZ / CERAMICS UNIT
│   │   ├── Float-glass line (window, optical)
│   │   ├── Quartz crystal grower (optical, semiconductor)
│   │   ├── Fiber-optic drawing tower
│   │   ├── Ceramic kiln (refractory, electronic substrates)
│   │   ├── Thin-film deposition (CVD/PVD for coatings)
│   │   └── Optical lens grinder/polisher
│   │
│   ├── 6. SEMICONDUCTOR / ELECTRONICS UNIT
│   │   ├── Wafer foundry (Si, GaAs, GaN, SiC)
│   │   ├── Photolithography (extreme UV — recreates EUV lasers from grating mirror system)
│   │   ├── Doping / ion implantation
│   │   ├── PCB fab line
│   │   └── Chip packaging
│   │
│   ├── 7. ENERGETICS / FUEL UNIT
│   │   ├── Cryogenic propellant (LH₂, LOX, LCH₄)
│   │   ├── Solid rocket motor caster
│   │   ├── Battery cell line (Li-ion, solid-state, fuel-cell stacks)
│   │   ├── Antimatter trap (positron / antiproton storage)
│   │   └── Fissile / fusion fuel pellet press
│   │
│   └── 8. FOOD / BIOLOGICAL UNIT
│       ├── Algae bioreactor (Chlorella / Spirulina — protein + O₂)
│       ├── Cellular agriculture (lab-grown meat)
│       ├── Hydroponic / aeroponic farm (fresh vegetables)
│       ├── Fermentation tank (yeast, bacteria for biotech)
│       └── Genome editor (CRISPR for adapting plants to alien atmospheres)
│
├── FORMING / SHAPING MACHINES (transforms raw materials → parts)
│   ├── 3D PRINTING ARRAY
│   │   ├── FDM (thermoplastic)
│   │   ├── SLA / DLP (photopolymer resin)
│   │   ├── SLS (powder polymer)
│   │   ├── DMLS / SLM (metal powder)
│   │   ├── Multi-material printer (gradient materials)
│   │   ├── Bioprinter (tissue, organs)
│   │   └── Concrete printer (large structures, surface bases)
│   │
│   ├── SUBTRACTIVE MACHINING
│   │   ├── 5-axis CNC mill (precision parts)
│   │   ├── Lathe (rotational symmetric parts)
│   │   ├── EDM (electrical discharge — hard materials)
│   │   ├── Laser cutter / waterjet (sheet stock)
│   │   └── Plasma cutter (thick metal)
│   │
│   ├── DEFORMATION
│   │   ├── Rolling mill (sheet, plate, foil)
│   │   ├── Extruder (rod, tube, profile)
│   │   ├── Press / forge (bulk forming)
│   │   ├── Drawing bench (wire, fiber)
│   │   └── Stamping (mass production parts)
│   │
│   ├── JOINING
│   │   ├── Welding (TIG, MIG, electron beam, friction stir)
│   │   ├── Brazing / soldering
│   │   ├── Adhesive applicator
│   │   └── Mechanical fastener placer (riveting, bolting)
│   │
│   └── FINISHING
│       ├── Polishing / lapping
│       ├── Surface treatment (anodizing, passivation)
│       ├── Coating (paint, ceramic, optical AR)
│       └── Inspection (CMM, X-ray CT, ultrasonic NDT)
│
└── ASSEMBLY BAY
    ├── INTERNAL — fits inside mothership envelope
    │   ├── Robot arm cell (industrial 6-DOF)
    │   ├── Clean room (semiconductor / pharma)
    │   ├── Vacuum chamber (space-grade testing)
    │   └── Cryogenic chamber (cold-grade testing)
    │
    └── ⭐ EXTERNAL — IN-SPACE ASSEMBLY (USER VISION)
        ├── "Stationary spacetime" assembly zone
        │   (a defined region of space treated as static reference frame —
        │    truss frames anchor, robots build, components float in
        │    micro-G; suitable for LARGE structures that don't fit in
        │    the mothership envelope)
        ├── Construction robot swarm (autonomous, self-coordinating)
        ├── Truss / scaffold deployer
        ├── Solar concentrator forge (free fusion-temperature processing using sunlight)
        └── Use cases:
            ├── Megastructures (Dyson swarm elements, large telescopes)
            ├── Large stations (orbital colonies, refineries)
            ├── Long ships (next-gen interstellar vessels too large for in-mothership construction)
            ├── Wormhole stabilization rings
            └── Dyson sphere lattice elements (Act VII)
```

### 6.2 Game mechanic: synthesis flow

1. **Resource gathering** (subsidiary craft) — collect raw atoms from celestial bodies (see [§7](#7-probe--subsidiary-craft-fleet))
2. **Atomic source charging** — raw → purified atoms in atomic source modules
3. **Recipe selection** — player picks what to make (UI: tech-tree-style recipe browser)
4. **Synthesis** — category synthesizer combines atoms per recipe; takes time + energy
5. **Forming** — output goes to forming machines for shaping
6. **Assembly** — parts assembled in internal bay or external space
7. **Deployment** — finished product placed into ship's inventory or installed

### 6.3 Recipe progression

Recipes are unlocked via:
- Story progression (Act unlocks)
- Research from sensor data (e.g. discover new alien material → unlock recipe)
- Salvage from anomalies / wreckage
- Tech-tree research

Example progression for "antimatter":
- Tier 1: H₂SO₄ recipe (basic chemistry)
- Tier 2: Aspirin recipe (basic pharma)
- Tier 3: Carbon-fiber recipe (composite)
- Tier 4: Silicon wafer (semiconductor)
- Tier 5: Photovoltaic panel (electronics)
- Tier 6: D-T fusion fuel pellet (energetics)
- Tier 7: Antiproton (energetics — very expensive)
- Tier 8: Wormhole-grade exotic matter (final)

### 6.4 Strategic depth

- **Material constraints**: a missing element on board → mission to fetch from nearby celestial body
- **Energy constraints**: fusion reactor capacity caps simultaneous synthesis
- **Time pressure**: pharma items have shelf life; some recipes time-sensitive
- **Cascading dependencies**: making a wormhole stabilizer requires exotic matter, which requires Casimir cavities, which require quartz substrate, which requires SiO₂...
- **Failure / waste**: imperfect recipes waste materials; player optimizes recipes through research

### 6.5 UI sketch

```
┌─ SYNTHESIS FOUNDRY ────────────────────────────────────┐
│ [Atomic Sources]   [Recipes]   [Queue]   [Inventory]   │
├────────────────────────────────────────────────────────┤
│ Sources (left panel):                                  │
│   H: 12,500 mol                                        │
│   C: 4,210 mol  ← 부족 시 빨간색                       │
│   Fe: 0 mol    ⚠ Need 50 mol — [Dispatch fetcher]    │
│ ...                                                    │
├────────────────────────────────────────────────────────┤
│ Recipe selected: Carbon Fiber Composite                │
│   Inputs:  C × 100, Polymer-A × 20, Resin × 5         │
│   Energy:  25 GJ                                       │
│   Time:    3 hours (in-game)                          │
│   Output:  CFRP sheet × 10                            │
│   [Synthesize] [Queue] [Schedule]                      │
└────────────────────────────────────────────────────────┘
```

---

## 7. PROBE & SUBSIDIARY CRAFT FLEET

⭐ **USER VISION** — fleet of supporting vessels around the mothership

### 7.1 Fleet structure

```
MOTHERSHIP
│
├── PROBE FLEET (sensing / exploration)
│   ├── Universal probe (spectro + polari + magneto + grav-field)
│   ├── X-ray probe (high-energy phenomena)
│   ├── Gravitational-wave probe (LISA-class)
│   ├── Neutrino probe (deep penetration)
│   ├── Lander probe (surface landing)
│   ├── Atmospheric probe (gas-giant balloon)
│   └── Disposable probe (one-way: black hole, supernova, wormhole throat)
│
├── ⭐ SUBSIDIARY RESOURCE FLEET (extraction & transport)
│   ├── Mining ships (asteroid/moon surface excavation)
│   ├── Atmospheric scoopers (gas giant H/He/methane harvest)
│   ├── Solar-wind harvesters (in-flight ion collection)
│   ├── Cargo haulers (bulk material transport)
│   ├── Ice harvesters (permafrost crater specialists)
│   └── Salvage / recovery ships (anomaly investigation, debris collection)
│
├── ⭐ MAINTENANCE / LOGISTICS FLEET
│   ├── Fetcher (small, fast — emergency material fetch)
│   ├── Repair drone (external mothership maintenance)
│   ├── Supply runner (mothership ↔ established colony)
│   └── Relay station deployer (comm/navigation buoys)
│
└── COMBAT / DEFENSE (later acts only)
    ├── Anti-meteoroid laser swarm
    └── Anomaly defense drones
```

### 7.2 Subsidiary fleet operations

**Autonomous AI control**: Subsidiary ships are AI-piloted (player issues orders, ships execute). Fleet management UI similar to RTS.

**Order types**:
- *Mine* (target asteroid/body, return cargo)
- *Scoop* (gas giant atmospheric pass)
- *Patrol* (continuous resource-gathering route)
- *Fetch* (emergency single-trip for specific material)
- *Salvage* (investigate debris/anomaly)
- *Defend* (escort mothership)

### 7.3 Mission integration

When mothership runs out of a critical material:
1. **Alert**: synthesis foundry flags shortage
2. **Auto-suggestion**: Hubble AI suggests nearest source celestial body
3. **Player decision**: dispatch subsidiary craft OR personally pilot mothership there
4. **Fleet dispatch**: fetcher / mining ship sent
5. **Transit time**: realistic (e.g. 2 days for asteroid belt, 3 weeks for outer system)
6. **Return + replenish**: cargo unloaded into atomic source modules
7. **Synthesis resumes**

### 7.4 Risk mechanics

- Subsidiary craft can be lost (cosmic events, navigation errors)
- Lost ships = lost data + wasted material + crew (if manned)
- Replacement built in synthesis foundry (takes materials + time)
- Player must balance fleet size (more ships = more parallel operations but more risk surface)

---

## 8. CELESTIAL BODY CATALOG

Each type → unique missions, sensors required, resources, story significance.

### Star types

| Type | Examples | Sensors | Resources | Missions |
|---|---|---|---|---|
| **G-type (yellow dwarf)** | Sol, Tau Ceti | Spectro, polari | H, He, magnetic field energy | Spectral analysis, age dating |
| **K/M-type (red dwarf)** | Proxima, Wolf 359 | + IR | Stellar wind plasma | Long-life host search |
| **A/F-type (white)** | Sirius, Vega | + UV | Heavy elements (older) | High-mass element synthesis observation |
| **O/B-type (blue)** | Rigel, Spica | + X-ray | Heavy elements + UV abundance | Short-life observation; pre-supernova |
| **Red giant** | Betelgeuse, Antares | + IR + GW | s-process heavy elements | Time-limited extraction |
| **White dwarf** | Sirius B | + X-ray + GR | Degenerate matter samples | Quantum sensor fab material |
| **Neutron star** | Crab pulsar | + GW + radio + X-ray | Heavy nuclei (kilonova) | Precision navigation, kilonova harvest |
| **Black hole** | Sgr A*, Cyg X-1 | + X-ray + GW + tidal gauge | Hawking radiation (theoretical) | Time dilation experiments, info paradox |
| **Brown dwarf** | Luhman 16 | Universal | H/He, methane | Way-station base |
| **Variable stars (Cepheid, RR Lyrae)** | Polaris | Photometer | Distance ladder calibration | Galactic distance survey |

### Stellar systems

| Type | Examples | Mechanics |
|---|---|---|
| **Single star + planets** | Sol | Standard exploration |
| **Binary (close)** | Alpha Cen AB | Lagrangian point exploitation |
| **Binary (eclipsing)** | Algol | Mass transfer observation |
| **Trinary** | Alpha Cen | Complex orbital dynamics |
| **Open cluster** | Pleiades, Hyades | Multi-star resource collection |
| **Globular cluster** | M13, Omega Cen | Old population II stars; rare elements |

### Planetary types

| Type | Examples | Sensors | Resources | Habitability |
|---|---|---|---|---|
| **Terrestrial (rocky)** | Earth, Mars | Universal + lander | Metals, silicates | High potential |
| **Super-Earth** | Kepler-452b | + magnetometer | Metals | Sometimes habitable |
| **Hot Jupiter** | 51 Pegasi b | + IR | H/He | Atmospheric sampling |
| **Gas giant** | Jupiter, Saturn | Atmospheric probe | H, He, CH₄, exotic atmospheric chem | No surface |
| **Ice giant** | Uranus, Neptune | + IR | NH₃, CH₄, H₂O ice | No surface |
| **Diamond planet** ⭐ | 55 Cancri e | Drill + spectro | Pure carbon, diamond cores | (User vision) |
| **Carbon-rich (graphite/SiC)** | (theoretical) | Spectro | C, SiC | Optical computing material |
| **Lava world** | CoRoT-7b | + thermal | Molten silicates, rare metals | Resource mining only |
| **Ocean world** | Europa, Enceladus | + sub-surface lidar | Liquid water, possible biology | Life search target |
| **Earth-analog** ⭐ | Kepler-186f | All sensors | Habitable | Colony candidate |
| **Tidally-locked** | Proxima b | All | Day-side mining + night-side ice | Asymmetric exploration |
| **Pulsar planet** | PSR B1257+12 | + radiation map | Heavy elements | Hostile, resource-only |
| **Rogue planet** (no star) | (many) | + IR | Internal heat | Way-stations, dark exploration |

### Smaller bodies

| Type | Examples | Resources |
|---|---|---|
| **Moons** | Luna, Titan, Europa, Ganymede | Regolith, He-3 (Luna), CH₄ (Titan), water (Europa) |
| **Asteroids (C/S/M-type)** | Ceres, Vesta, Psyche | Carbonaceous, silicate, metallic (Psyche = $10²⁵ in metals) |
| **Comets** | Halley, Hale-Bopp | Water, organic precursors |
| **Kuiper Belt objects** | Pluto, Arrokoth | Ice, organics |
| **Oort cloud objects** | Sedna | Ancient ice, primordial material |

### Nebulae

| Type | Examples | Sensors | Resources |
|---|---|---|---|
| **Emission (HII)** | Orion Neb. | + radio + IR | H, ionized plasma |
| **Reflection** | Pleiades dust | Spectro | Dust grains, silicates |
| **Dark (molecular cloud)** | Coal Sack, B68 | + IR + radio | Cold H₂, CO, complex molecules |
| **Planetary nebula** | Ring Neb., Cat's Eye | + UV | Heavy elements from progenitor star |
| **Supernova remnant** | Crab Neb., Cas A | + X-ray + GW | All elements, including r-process |

### Galaxies

| Type | Examples | Mechanics |
|---|---|---|
| **Spiral (like our own)** | Andromeda M31 | Familiar exploration |
| **Elliptical** | M87 | Old stars, low gas |
| **Irregular** | LMC, SMC | Dense star formation |
| **Active galactic nuclei (AGN)** | M87 jet, NGC 1275 | Extreme energy |
| **Quasars** | 3C 273 | Distance beacons |
| **Galaxy clusters** | Virgo, Coma | Civilization-level exploration |

### Exotic / theoretical

- Wormholes (stable, traversable)
- Cosmic strings (theoretical)
- Boltzmann brains (philosophical thought experiment)
- Multiverse boundaries (Act VII endgame)

---

## 9. TECH TREE

Hierarchical research tree. Each tier unlocks via mission completion + research time.

### Categories

```
PROPULSION
├─ T0: Chemical → T1: Ion → T1.5: VASIMR → T2: Solar/E-sail
                                          → T3: Nuclear thermal / Fusion pulse
                                          → T4: Antimatter / Bussard
                                          → T5: Laser sail / Alcubierre
                                          → T6: Wormhole transit

POWER
├─ T0: Solar → T1: RTG → T2: Fission → T3: D-T fusion
                                     → T4: D-He³ fusion → T5: Antimatter
                                                        → T6: Dyson swarm

SENSORS
├─ T1: Visible/IR/spectro → T2: X-ray/Gamma → T3: GW/neutrino
                                            → T4: Casimir/tidal → T5: Dark matter / quantum gravity
                                                                → T6: Multiverse boundary

SYNTHESIS
├─ T1: Basic chem → T2: Pharma + polymers → T3: Semiconductor + alloy
                                          → T4: Antimatter trap → T5: Exotic matter forge

COMMUNICATION
├─ T1: Radio → T2: Laser → T3: Pulsar timing → T4: Neutrino beam
                                              → T5: Quantum entanglement

LIFE SUPPORT
├─ T1: Closed loop → T2: Centrifugal G → T3: Cryosleep
                                       → T4: Genetic adaptation → T5: Consciousness backup

CONSTRUCTION
├─ T1: Internal assembly → T2: Robot swarm → T3: Truss megastructure
                                           → T4: Stationary spacetime free assembly
                                           → T5: Dyson lattice
```

### Research mechanic
- Each node: cost (atoms × time × energy)
- Prerequisite missions (e.g. observe red giant → unlock s-process recipe)
- Player schedules research while doing other missions
- AI auto-research mode for late-game convenience

---

## 10. RESOURCE ECONOMY

### Resource flow

```
[Celestial body] → [Subsidiary craft mining] → [Atomic source module]
                                              ↓
                                   [Category synthesizer]
                                              ↓
                                   [Forming machine]
                                              ↓
                          [Internal bay assembly]
                              OR
                          [External free-space assembly]
                                              ↓
                                   [Inventory / installed module]
```

### Material list (game economy)

**Raw**: H, He, Li, Be, B, C, N, O, F, Ne, Na, Mg, Al, Si, P, S, Cl, Ar, K, Ca, Sc, Ti, V, Cr, Mn, Fe, Co, Ni, Cu, Zn, ... (full periodic table)

**Special / rare**:
- He-3 (lunar regolith only)
- Antimatter (pulsar / antiproton trap)
- Exotic matter (Casimir cavity production)
- Heavy r-process (Au, Pt, U, Os — kilonova sites)
- Pure diamond crystals (carbon planets)
- Helium-rich ice (Kuiper / Oort)

**Refined intermediates**:
- Steel grades, Al alloys, Ti alloys
- Polymer pellets (PE, PP, PEEK, etc.)
- Pharma APIs
- Quartz crystals
- Semiconductor wafers
- Photovoltaic cells

**Finished products**:
- Spacecraft modules
- Sensor instruments
- Replacement parts
- Colony infrastructure
- Megastructure components

### Economic depth

- **Scarcity tiers**: most elements abundant; some (Au, Pt, antimatter) extremely scarce
- **Locality**: certain materials only obtainable at specific celestial body types
- **Time-perishable**: pharmaceuticals + biologics expire
- **Recycling**: failed missions / damaged ships → raw materials back into atomic source

---

## 11. MISSION CATEGORIES

### Story missions
- One per Act (5-7 per Act = ~40 total)
- Drive narrative reveals
- Major rewards (tech tree unlocks, colony establishment)

### Resource extraction
- Continuous, repeatable
- Subsidiary fleet handles most autonomously
- Player intervenes for high-value targets (kilonova window, near-Earth diamond planet)

### Maintenance / logistics
- Triggered by mothership system damage / shortage
- Fetch nearest material
- Repair external damage
- Replenish consumables

### Research / discovery
- Investigate anomaly signal
- Catalog new celestial type
- Verify scientific hypothesis (e.g. "are all white dwarfs metallic-cored?")

### Crisis events (random)
- Solar flare en route
- Cosmic ray storm
- Mothership system failure (random subsystem)
- Lost subsidiary craft (rescue mission)
- Supernova precursor (neutrino warning) — repositioning
- Anomalous gravity wave (investigate)

### Building / colonization
- Establish surface colony on confirmed habitable
- Deploy permanent extraction infrastructure (orbital methane harvester)
- Build wormhole stabilization ring (Act V+)
- Build Dyson swarm element (Act VII)

### Educational mini-quests (optional bonus)
- "Replicate Hubble's redshift discovery"
- "Verify gravitational lensing of [target galaxy]"
- "Detect first exoplanet via radial velocity method"
- → Award lore + completion badges

---

## 12. MAINTENANCE / LOGISTICS LOOP

⭐ **USER VISION** — when mothership systems break or run out of materials, player must source replacement materials from nearby celestial bodies.

### 12.1 Trigger conditions
- Random failure (e.g. ion engine grid fatigue after N hours of use)
- Material shortage (synthesis foundry blocked due to missing element)
- Sensor degradation (optics aging, photodetector damage)
- Crew habitat consumables (algae bioreactor needs N replenishment)
- Cosmic ray damage (probabilistic hit on circuits)

### 12.2 Decision flow

```
EVENT: ion engine grid fatigue
  ↓
ASSESS: which materials needed for repair?
  → Tungsten 50 mol, Molybdenum 20 mol, Single-crystal Si 5 mol
  ↓
INVENTORY CHECK:
  → Tungsten: have 80 mol ✓
  → Molybdenum: have 5 mol ✗ (need 15 more)
  → Single-crystal Si: have 0 mol ✗ (need 5)
  ↓
HUBBLE SUGGESTION:
  "Mo available at asteroid 16 Psyche (2.4 AU, 18-day transit).
   Si raw available at any silicate body. Closest: Mars (1.5 AU).
   Production at synthesis foundry: 6 hours after material arrival."
  ↓
PLAYER CHOICES:
  A. Dispatch subsidiary mining ship to 16 Psyche (Mo) +
     dispatch to Mars (Si). Wait 18 days. Auto-synthesize. Auto-repair.
  B. Personally pilot mothership to closer asteroid; manually mine. Faster.
  C. Cannibalize lower-priority subsystem for materials. Faster but loses functionality.
  D. Skip repair (run with degraded engine; risk further failure).
  ↓
EXECUTE → in-game time advances → repair complete OR new event.
```

### 12.3 Game-design value
- Forces engagement with celestial body diversity (different bodies = different material stocks)
- Rewards strategic stockpiling
- Creates organic side-quests (no scripting required)
- Reinforces "we are alone in deep space" narrative tension

---

## 13. UI/UX PHASES

### Phase 1: Web (UI/storytelling focus)

**Tech**: HTML5 + Canvas2D (or Three.js for light 3D), TypeScript or vanilla JS, Supabase backend (reuse from luckyplz).

**Visual style**:
- 2D top-down or isometric system maps
- Clean, NASA-aesthetic UI (sans-serif, monospace data, blue/cyan/orange accents — matches existing luckyplz dodge game)
- Spectrograph / polarimeter / synthesis UI as data visualization (charts, dials)
- Celestial bodies = stylized SVG icons (planet rendering not realistic — focus on data)
- Star fields = procedural noise + parallax

**Major screens**:
1. **Bridge** (main view) — mothership status, active missions, alerts
2. **Galactic map** — zoomable star chart with travel routes
3. **Mission view** — celestial body close-up + sensor data + active probes
4. **Synthesis foundry** — recipe browser + queue + inventory
5. **Tech tree** — research progression
6. **Logbook** — story log + character dialogues + achievements
7. **Codex** — celestial body encyclopedia (player-built atlas)

**Save system**:
- Cloud save via Supabase (player_id ↔ savestate JSON)
- Local backup in browser localStorage
- Multi-slot saves (allow experimentation without losing progress)

### Phase 2: Remaster (Unreal Engine 5)

**Tech**: UE5 with Lumen + Niagara, photorealistic rendering, real Newtonian/GR physics simulation.

**Key features**:
- True 3D space navigation with orbital mechanics
- Procedural celestial body surfaces (KSP/No Man's Sky-tier)
- Realistic black hole rendering (Interstellar-tier gravitational lensing)
- VR support (Meta Quest, Vision Pro)
- Voice acting for major characters (Hubble AI, Dr. Sagan)
- Multiplayer co-op (mothership + colony coordinator? Late consideration)

**Migration**: Save data + player accounts portable from Phase 1 → Phase 2 via JSON schema versioning.

---

## 14. TECHNICAL ARCHITECTURE (Phase 1)

### 14.1 Stack
- **Frontend**: Vanilla JS or React/Vue + Canvas2D + Three.js (optional for star map)
- **Hosting**: Cloudflare Pages (separate domain, e.g. `exoarchitect.com`)
- **Backend**: Supabase (PostgreSQL + Realtime + Auth)
- **No service worker** (per CLAUDE.md inheritance — versioned `?v=` cache busting)

### 14.2 Core data model (Supabase schema)

```sql
-- Player profile
players (id uuid pk, nickname text, created_at, ...)

-- Game state (JSON blob savestate)
game_states (
    id bigserial pk,
    player_id uuid fk,
    slot int,
    save_json jsonb,    -- entire game state
    last_saved_at timestamptz,
    act_progress int,
    play_time_sec int
)

-- Discovered celestial bodies (per-player codex)
discoveries (
    player_id uuid,
    body_id text,       -- e.g. "proxima_b"
    discovered_at timestamptz,
    sensor_data jsonb,  -- spectro/polari/etc values
    primary key (player_id, body_id)
)

-- Tech tree progress
research (
    player_id uuid,
    tech_id text,
    unlocked_at timestamptz,
    primary key (player_id, tech_id)
)

-- Synthesis foundry inventory
inventory (
    player_id uuid,
    item_id text,    -- "carbon", "antimatter", "ion_grid_assembly"
    quantity numeric,
    primary key (player_id, item_id)
)

-- Active subsidiary fleet
fleet (
    id bigserial pk,
    player_id uuid,
    ship_type text,       -- "miner", "fetcher", "scoper"
    status text,          -- "idle", "in_transit", "extracting", "returning"
    target_body_id text,
    eta timestamptz,
    cargo jsonb
)

-- Story progress / triggered events
story_flags (
    player_id uuid,
    flag_id text,
    triggered_at timestamptz,
    primary key (player_id, flag_id)
)

-- Galactic atlas (shared / discoverable global)
celestial_bodies (
    id text pk,
    name text,
    type text,           -- "g_dwarf", "neutron_star", etc.
    coords jsonb,        -- {ra, dec, distance_pc}
    real_data jsonb,     -- actual NASA/ESA data if real body
    canonical_lore text  -- in-game description
)
```

### 14.3 RPC pattern

Following luckyplz convention (see CLAUDE.md `messaging_rpc_pattern.md` reference):
- All reads through SECURITY DEFINER RPC (mobile WebView RLS quirks)
- Functions: `record_mission_complete`, `record_discovery`, `record_research`, `update_inventory`, `dispatch_fleet`
- Time-server-authoritative: in-game time advances based on server timestamp diff (prevents save-edit cheat)

### 14.4 Time simulation
- **In-game time** ≠ real time
- Player can:
  - Real-time mode (slow, immersive)
  - Compressed-time mode (fast-forward to next event)
  - Pause + plan
- Server calculates "what would have happened in X seconds of game-time" (offline progress for fleet missions)

### 14.5 Performance targets
- 60 FPS Canvas2D rendering on mid-range phones
- Game-state save under 500 ms
- Galactic map: handles 10,000+ celestial bodies with LOD

---

## 15. LORE BIBLE / GLOSSARY

**The Diaspora** — Humanity's exodus from dying Earth. The mothership project that the player commands.

**The Architects** — Mysterious builders of the wormhole network. Revealed in Act V-VII as future humanity (closed timelike curve self-consistency).

**Source of All Sources** (만물의 근원) — The mothership's hierarchical synthesis system; the device that can manufacture any material from atomic constituents.

**Stationary Spacetime** — A free-floating region of space, treated as static reference frame, where large structures are assembled outside the mothership envelope. Robot swarms and truss frames anchor; components float in micro-G.

**Cold-sleep capsule** — Cryogenic preservation pod for a colonist. 10,000 capsules aboard. Awakened selectively for skill needs / population transfer.

**The Last Transmission** — Earth's final radio message to the mothership. Received in Act I.

**ESI (Earth Similarity Index)** — Quantitative score for habitability of a planet. Real concept used by astrobiologists.

**Lagrangian point** — Stable gravitational equilibrium point in a binary system. Used for low-fuel parking.

**Hohmann transfer** — Most fuel-efficient orbital transfer between two bodies. Slow.

**Gravity assist (slingshot)** — Use planetary mass to accelerate spacecraft.

**Spaghettification** — Tidal force destruction near black hole event horizon. Real term.

**ISRU** — In-Situ Resource Utilization. Manufacture/extract resources at mission site rather than transport from origin.

**He-3** — Helium-3 isotope. Rare on Earth, abundant in lunar regolith. Ideal aneutronic fusion fuel.

**Casimir effect** — Quantum vacuum energy difference between conducting plates. Source of negative energy density.

**Closed Timelike Curve (CTC)** — Path through spacetime that loops back on itself. Theoretical wormhole solution. Plot device.

**Novikov self-consistency** — Principle that any time-loop must be self-consistent (you can't change the past). Game enforces this in plot structure.

**Tully-Fisher relation** — Empirical relation between galaxy rotation speed and luminosity. Used for distance estimation.

**Quasar** — Quasi-Stellar Object. Most luminous AGN. Visible at extreme distances; useful as positional beacon.

**Pulsar timing** — Use pulsar rotation as precision clock. Real NASA SEXTANT navigation concept.

**LISA** — Laser Interferometer Space Antenna. Future ESA gravitational wave observatory. In-game equivalent for galactic GW sensing.

**Bussard ramjet** — Theoretical interstellar engine collecting H from interstellar medium. Real proposal by Robert Bussard 1960.

**Alcubierre warp drive** — Theoretical FTL via spacetime contraction in front + expansion behind. Requires negative energy.

**Dyson sphere/swarm** — Type II Kardashev civilization marker. Surrounds star, captures full energy output.

**Kardashev scale** — Civilization energy use classification. Type I (planet-scale) → II (star-scale) → III (galaxy-scale).

---

## 16. ROADMAP

### Phase 0: Prototype (1-2 weeks)
**Goal**: Validate core mission loop.
**Scope**:
- Single Act I mission (Permafrost Harvest)
- Ship state, simple mission flow, basic UI
- Spectroscopy mini-game prototype
- Implement under `/games/exoarchitect/` in luckyplz

**Success criteria**:
- Mission fun to play start-to-finish
- Spectroscopy puzzle satisfying
- Story tone resonates (test with 3-5 playtesters)

### Phase 0.5: Act I complete (1 month)
- All 5 Act I missions playable
- Synthesis foundry MVP (5 recipes)
- Subsidiary fleet (1 ship type — fetcher)
- Save system functional
- Hubble dialogue system

### Phase 1: Episodic release (3-12 months)
- Act II (3 months)
- Act III (3 months)
- Migrate to dedicated domain (`exoarchitect.com`)
- Acts IV-VII over 6+ months

### Phase 2: Remaster (1-2 years post-Phase 1)
- Unreal Engine 5 port
- 3D rendering, real physics
- VR support
- Voice acting

### Phase 3: Multiplayer / community (Phase 2+)
- Co-op mothership operations
- Player-shared celestial atlas
- Modding support
- Educational license / partnerships (NASA, ESA, schools)

---

## APPENDIX A: Real-world references for accurate science

- **NASA Eyes on the Solar System** — orbital data
- **Gaia DR3 catalog** — 1.8 billion star positions/parallaxes
- **NASA Exoplanet Archive** — confirmed exoplanets data
- **JWST early release observations** — atmospheric spectra
- **LIGO/Virgo gravitational wave catalog** — confirmed mergers
- **Sloan Digital Sky Survey** — galaxy catalog
- **Cassini-Huygens data** — Saturn/Titan
- **Voyager 1/2 data** — outer solar system

These can be integrated as actual game data in Phase 2 (e.g. "the star you discovered in-game = real Gaia catalog star").

---

## APPENDIX B: Open questions for future design sessions

1. **Combat mechanics**: include? If so, against what (asteroid swarms, anomaly defenders, hostile AI)?
2. **Character romance / relationship arcs**: yes/no? (Mass Effect-style)
3. **Multiple endings**: based on Heritor's Choice? Or multiple valid paths through Act VII?
4. **Permadeath / iron-man mode**: optional difficulty?
5. **Procedural side missions**: how many to maintain content longevity?
6. **Live data integration**: real-time observatory feeds (e.g. JWST new photo unlocks new in-game discovery)?
7. **Educational tie-in**: explicit "tutorial mode" for school use?
8. **Streamer mode**: features for content creation (cinematic camera, replay)?

---

## END OF DOCUMENT

This document is the canonical reference for ExoArchitect development. When starting a new coding session in a different folder:

1. Read this document fully (~30 min)
2. Pick a Phase (0 → 0.5 → 1 → 2)
3. Pick a specific milestone within the Phase
4. Cross-reference relevant sections (e.g. Synthesis Foundry chapter for that subsystem)
5. Begin implementation with the schema in §14.2 as the starting data model

Last updated: 2026-05-03
Maintainer: Junpiter
