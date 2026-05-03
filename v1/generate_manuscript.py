#!/usr/bin/env python3
"""Generate CMPB Update manuscript as .docx with inline figures and .pptx with editable figures."""

import re
from pathlib import Path
from docx import Document
from docx.shared import Inches, Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from pptx import Presentation
from pptx.util import Inches as PptxInches, Pt as PptxPt, Emu
from pptx.enum.text import PP_ALIGN
from PIL import Image

SCRIPT_DIR = Path(__file__).resolve().parent
FIG_DIR = SCRIPT_DIR / "figures"
OUTPUT_DIR = SCRIPT_DIR / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

# Reference list in order of appearance (Vancouver style)
REFERENCES = [
    # [1] eleveld2018
    "Eleveld DJ, Colin P, Absalom AR, Struys MMRF. Pharmacokinetic-pharmacodynamic model for propofol for broad application in anaesthesia and sedation. Br J Anaesth. 2018;120(5):942-959.",
    # [2] strichartz1990
    "Strichartz GR, Sanchez V, Arthur GR, Chafetz R, Martiny D. Fundamental properties of local anesthetics. II. Measured octanol buffer partition coefficients and pKa values of clinically used drugs. Anesth Analg. 1990;71(2):158-170.",
    # [3] kavcic2021
    u"Kav\u010di\u010d H, Umek N, Vintar N, Mavri J. Local anesthetics transfer relies on pH differences and affinities toward lipophilic compartments. J Phys Org Chem. 2021;34(12):e4275.",
    # [4] rosenberg2004
    "Rosenberg PH, Veering BT, Urmey WF. Maximum recommended doses of local anesthetics: a multifactorial concept. Reg Anesth Pain Med. 2004;29(6):564-575.",
    # [5] decassai2025
    "De Cassai A, Pasin L, Boscolo A, et al. Local anaesthetic toxicity: moving beyond maximum recommended doses. Br J Anaesth. 2025.",
    # [6] hughes1992
    "Hughes MA, Glass PSA, Jacobs JR. Context-sensitive half-time in multicompartment pharmacokinetic models for intravenous anesthetic drugs. Anesthesiology. 1992;76(3):334-341.",
    # [7] tucker1979
    "Tucker GT, Mather LE. Clinical pharmacokinetics of local anaesthetics. Clin Pharmacokinet. 1979;4(4):241-278.",
    # [8] burm1989
    "Burm AGL. Clinical pharmacokinetics of epidural and spinal anaesthesia. Clin Pharmacokinet. 1989;16(5):283-311.",
    # [9] virtanen2020
    "Virtanen P, Gommers R, Oliphant TE, et al. SciPy 1.0: fundamental algorithms for scientific computing in Python. Nat Methods. 2020;17(3):261-272.",
    # [10] aubouin2023
    "Aubouin-Pairault B, Fiacchini M, Dang T. PAS: a Python Anesthesia Simulator for drug control. J Open Source Softw. 2023;8(88):5480.",
    # [11] hosseinirad2025
    "Hosseinirad S, Merlo M, Trovo F, Tognoli E, Metelli AM, Dumont GA. AReS: a patient simulator to facilitate testing of automated anesthesia. Comput Methods Programs Biomed. 2025;108901.",
    # [12] ionescu2021
    "Ionescu CM, Neckebroek M, Ghita M, Copot D. An open source patient simulator for design and evaluation of computer based multiple drug dosing control for anesthetic and hemodynamic variables. IEEE Access. 2021;9:8680-8694.",
]

# Map citation keys to numbers
CITE_MAP = {
    "eleveld2018": "1",
    "strichartz1990": "2",
    "kavcic2021": "3",
    "rosenberg2004": "4",
    "decassai2025": "5",
    "hughes1992": "6",
    "tucker1979": "7",
    "burm1989": "8",
    "virtanen2020": "9",
    "aubouin2023": "10",
    "hosseinirad2025": "11",
    "ionescu2021": "12",
}

FIGURE_FILES = {
    "fig1": ("fig1_compartment_diagram_plasma.png", "Figure 1", "Three-compartment model with selectable initial compartment (plasma highlighted)."),
    "fig2": ("fig2_bupivacaine_comparison.png", "Figure 2", "Bupivacaine 150 mg -- Plasma concentration by initial compartment with toxicity thresholds."),
    "fig3": ("fig3_all_drugs_comparison.png", "Figure 3", "Plasma concentration comparison for all four local anesthetics by initial compartment."),
    "fig4": ("fig4_bupivacaine_effect.png", "Figure 4", "Bupivacaine -- Effect-site response by initial compartment."),
    "fig5": ("fig5_bupivacaine_bpt_full.png", "Figure 5", "Bupivacaine 150 mg from BPT -- Full compartment concentration profile."),
    "fig6": ("fig6_summary_table.png", "Figure 6", "Bupivacaine 150 mg -- PK/PD summary by initial compartment."),
}


def add_superscript_citations(paragraph, text):
    """Parse text with {N} or {N-M} citation markers and add superscript runs."""
    parts = re.split(r'(\{[^}]+\})', text)
    for part in parts:
        if part.startswith('{') and part.endswith('}'):
            run = paragraph.add_run(part[1:-1])
            run.font.superscript = True
            run.font.size = Pt(8)
        else:
            run = paragraph.add_run(part)
            run.font.size = Pt(11)
            run.font.name = 'Times New Roman'


def convert_pandoc_citations(text):
    """Convert [@key1; @key2] to {1,2} superscript markers."""
    def replace_cite(match):
        keys_str = match.group(1)
        keys = [k.strip().lstrip('@') for k in keys_str.split(';')]
        nums = []
        for k in keys:
            if k in CITE_MAP:
                nums.append(CITE_MAP[k])
            else:
                nums.append("?")
        # Compress consecutive numbers: 1,2,3 -> 1-3
        int_nums = sorted(set(int(n) for n in nums if n != "?"))
        ranges = []
        i = 0
        while i < len(int_nums):
            start = int_nums[i]
            end = start
            while i + 1 < len(int_nums) and int_nums[i + 1] == end + 1:
                i += 1
                end = int_nums[i]
            if start == end:
                ranges.append(str(start))
            elif end == start + 1:
                ranges.append(f"{start},{end}")
            else:
                ranges.append(f"{start}-{end}")
            i += 1
        return "{" + ",".join(ranges) + "}"
    return re.sub(r'\[@([^]]+)\]', replace_cite, text)


def add_table_to_doc(doc, headers, rows, label=""):
    """Add a formatted table to the document."""
    table = doc.add_table(rows=1 + len(rows), cols=len(headers))
    table.style = 'Table Grid'
    table.alignment = WD_TABLE_ALIGNMENT.CENTER

    # Headers
    for i, h in enumerate(headers):
        cell = table.rows[0].cells[i]
        cell.text = h
        for p in cell.paragraphs:
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            for run in p.runs:
                run.bold = True
                run.font.size = Pt(9)
                run.font.name = 'Times New Roman'

    # Data rows
    for r_idx, row_data in enumerate(rows):
        for c_idx, cell_data in enumerate(row_data):
            cell = table.rows[r_idx + 1].cells[c_idx]
            cell.text = cell_data
            for p in cell.paragraphs:
                for run in p.runs:
                    run.font.size = Pt(9)
                    run.font.name = 'Times New Roman'
    return table


def add_figure_to_doc(doc, fig_key):
    """Add a figure with caption to the document."""
    filename, label, caption = FIGURE_FILES[fig_key]
    filepath = FIG_DIR / filename
    if not filepath.exists():
        p = doc.add_paragraph(f"[{label}: {filename} not found]")
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        return

    # Add figure
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run()
    run.add_picture(str(filepath), width=Inches(5.5))

    # Add caption with spacing
    cap_p = doc.add_paragraph()
    cap_p.paragraph_format.space_before = Pt(14)
    cap_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = cap_p.add_run(f"{label}. ")
    run.bold = True
    run.font.size = Pt(10)
    run.font.name = 'Times New Roman'
    run = cap_p.add_run(caption)
    run.font.size = Pt(10)
    run.font.name = 'Times New Roman'


def generate_docx():
    """Generate the full manuscript .docx file."""
    doc = Document()

    # Set default font
    style = doc.styles['Normal']
    font = style.font
    font.name = 'Times New Roman'
    font.size = Pt(11)

    # ===== TITLE =====
    title_p = doc.add_paragraph()
    title_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    title_p.paragraph_format.space_after = Pt(6)
    run = title_p.add_run("yoshika: A Python Package for Pharmacokinetic-Pharmacodynamic Simulation of Local Anesthetics with Selectable Initial Compartment")
    run.bold = True
    run.font.size = Pt(14)
    run.font.name = 'Times New Roman'

    # ===== AUTHORS =====
    auth_p = doc.add_paragraph()
    auth_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = auth_p.add_run("Tatsuki Onishi")
    run.font.size = Pt(12)
    run.font.name = 'Times New Roman'

    # ===== AFFILIATION =====
    aff_p = doc.add_paragraph()
    aff_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = aff_p.add_run("Data Science and AI Innovation Research Promotion Center, Shiga University")
    run.font.size = Pt(10)
    run.font.name = 'Times New Roman'
    run.italic = True

    # ===== CORRESPONDING AUTHOR =====
    cor_p = doc.add_paragraph()
    cor_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    cor_p.paragraph_format.space_after = Pt(12)
    run = cor_p.add_run("Corresponding author: bougtoir@gmail.com")
    run.font.size = Pt(10)
    run.font.name = 'Times New Roman'

    # ===== HIGHLIGHTS =====
    doc.add_heading('Highlights', level=1)
    highlights = [
        "First open-source PKPD simulator with selectable initial compartment for local anesthetics",
        "Simulates clinically distinct scenarios: successful block, failed block, IV, and depot",
        "Supports context-sensitive maximum dose framework for regional anesthesia safety",
        "Built-in parameters for lidocaine, bupivacaine, ropivacaine, and levobupivacaine",
        "Demonstrates route-adaptive PKPD integration feasibility for anesthesia information systems",
    ]
    for h in highlights:
        p = doc.add_paragraph(h, style='List Bullet')
        for run in p.runs:
            run.font.size = Pt(11)
            run.font.name = 'Times New Roman'

    # ===== ABSTRACT =====
    doc.add_heading('Abstract', level=1)
    abstract_text = (
        "yoshika (Yielding Open Simulation of Hybrid Inter-disciplinary Kinetic Absorption) "
        "is an open-source Python package for pharmacokinetic-pharmacodynamic (PKPD) simulation "
        "of local anesthetics with a selectable initial compartment. Traditional three-compartment "
        "pharmacokinetic models assume intravenous administration where drug enters the central "
        "plasma compartment first. In regional anesthesia, however, drug is deposited directly into "
        "tissues: a successful peripheral nerve block deposits drug into vessel-poor tissue, while a "
        "failed block may deposit drug into vessel-rich tissue or directly into plasma. yoshika enables "
        "researchers and clinicians to simulate these clinically distinct scenarios by selecting the "
        "initial compartment of drug deposition and comparing the resulting concentration-time profiles "
        "and pharmacodynamic effects. The package includes built-in parameters for four local "
        "anesthetics (lidocaine, bupivacaine, ropivacaine, levobupivacaine), an effect-site compartment "
        "with sigmoid Emax pharmacodynamic model, and visualization utilities. By quantifying how the "
        "initial compartment determines peak plasma concentration and time-to-toxicity, yoshika supports "
        "the concept of context-sensitive maximum dose recommendations and route-adaptive PKPD simulation "
        "in anesthesia information management systems."
    )
    p = doc.add_paragraph(abstract_text)
    for run in p.runs:
        run.font.size = Pt(11)
        run.font.name = 'Times New Roman'

    kw_p = doc.add_paragraph()
    run = kw_p.add_run("Keywords: ")
    run.bold = True
    run.font.size = Pt(11)
    run.font.name = 'Times New Roman'
    run = kw_p.add_run("pharmacokinetics; pharmacodynamics; local anesthetics; regional anesthesia; compartment model; simulation; Python; systemic toxicity")
    run.font.size = Pt(11)
    run.font.name = 'Times New Roman'

    # ===== 1. INTRODUCTION =====
    doc.add_heading('1. Introduction', level=1)

    # 1.1
    doc.add_heading('1.1. The initial compartment problem in regional anesthesia', level=2)
    p = doc.add_paragraph()
    add_superscript_citations(p,
        "In regional anesthesia and pain medicine, local anesthetics (LAs) are injected near nerves and "
        "fascial planes rather than intravenously. The pharmacokinetic behavior of these drugs "
        "depends critically on the injection site and block success. Existing PK simulation tools "
        "(e.g., STANPUMP, Tivatrainer, Eleveld models) uniformly assume intravenous administration, "
        "where drug enters the central (plasma) compartment at time zero.{1} This "
        "assumption does not hold for regional anesthesia, where:"
    )
    bullets_11 = [
        "A successful peripheral nerve block deposits the drug bolus into vessel-poor tissue (V3/BPT), resulting in slow absorption into plasma with a delayed, attenuated peak plasma concentration.",
        "A failed block with intravascular injection deposits the drug into vessel-rich tissue (V2/BRT) or directly into plasma, resulting in rapid systemic exposure and potentially toxic concentrations.",
        u"Fascial plane blocks and depot injections involve absorption through a depot compartment with first-order absorption kinetics (k\u2090).",
    ]
    for b in bullets_11:
        p = doc.add_paragraph(b, style='List Bullet')
        for run in p.runs:
            run.font.size = Pt(11)
            run.font.name = 'Times New Roman'
    p = doc.add_paragraph("To our knowledge, no existing open-source PKPD simulation package explicitly supports selectable initial compartment for local anesthetics.")

    # 1.2
    doc.add_heading('1.2. Physicochemical basis of compartmental drug distribution', level=2)
    p = doc.add_paragraph()
    add_superscript_citations(p,
        "The pharmacokinetic behavior of LAs across tissue compartments is fundamentally governed by "
        "their physicochemical properties, particularly lipophilicity and ionization state. Strichartz "
        "et al. systematically measured octanol/buffer partition coefficients and pKa values for "
        "clinically used LAs, demonstrating that lipophilicity\u2014as quantified by the partition "
        "coefficient\u2014and temperature-dependent ionization are primary determinants of tissue "
        "distribution and nerve-blocking potency.{2} Their finding that the protonated "
        "species concentration in lipid remains nearly constant upon cooling, while the neutral species "
        "concentration decreases substantially, provided a physicochemical explanation for the increased "
        "blocking potency of LAs at lower temperatures."
    )
    p = doc.add_paragraph()
    add_superscript_citations(p,
        "Building on these fundamental properties, Kav\u010di\u010d et al. applied quantum chemical calculations "
        "to model the transfer energetics of seven LAs from extracellular fluid across the biological "
        "membrane to the axoplasm, demonstrating that LA transfer between compartments relies on pH "
        "differences and affinities toward lipophilic compartments.{3} Their computational "
        "analysis showed that LAs are stored in Schwann cell membranes, adipose tissue, and other "
        "lipophilic compartments, from which they are slowly released\u2014a process directly relevant "
        "to the vessel-poor tissue (BPT) compartment in pharmacokinetic models. Furthermore, local "
        "acidosis reduces LA storage in lipophilic compartments, decreasing the duration of action, "
        "while more lipophilic LAs (e.g., bupivacaine) exhibit greater storage capacity and longer "
        "duration."
    )
    p = doc.add_paragraph(
        "These physicochemical principles provide the theoretical foundation for the compartmental "
        "modeling approach implemented in yoshika: the initial compartment of drug deposition "
        "determines the subsequent absorption kinetics because tissue-specific lipophilicity and pH "
        "govern the rate of drug transfer between compartments."
    )

    # 1.3
    doc.add_heading('1.3. Clinical significance: systemic toxicity risk and context-sensitive dosing', level=2)
    p = doc.add_paragraph()
    add_superscript_citations(p,
        "The clinical significance of selectable initial compartment modeling lies in its "
        "direct implications for local anesthetic systemic toxicity (LAST) risk assessment. "
        "Traditional maximum recommended doses for LAs (e.g., bupivacaine "
        "2 mg/kg, lidocaine 4.5 mg/kg without epinephrine) are derived from intravenous "
        "pharmacokinetic studies, where the entire dose enters the central plasma compartment "
        "instantaneously.{4,5} This assumption produces the highest possible peak plasma "
        "concentration (Cmax) for a given dose."
    )
    p = doc.add_paragraph("However, in regional anesthesia, the initial compartment of drug deposition fundamentally alters the concentration-time profile:")
    scenarios = [
        "Successful block (BPT start): Drug deposited in vessel-poor tissue is absorbed slowly into plasma, producing a delayed and attenuated Cmax. The block is effective, the duration is long, and systemic exposure is low.",
        "Failed block (BRT start): Drug deposited near vessel-rich tissue is absorbed rapidly, producing an earlier and higher Cmax. The block effect is short, and systemic exposure approaches IV-like kinetics.",
        "Intravascular injection (Plasma start): Equivalent to IV bolus with immediate high Cmax and maximum toxicity risk.",
    ]
    for s in scenarios:
        p = doc.add_paragraph(s, style='List Bullet')
        for run in p.runs:
            run.font.size = Pt(11)
            run.font.name = 'Times New Roman'

    p = doc.add_paragraph(
        'Importantly, "successful/vessel-poor/long-duration/slow-removal" and '
        '"failed/vessel-rich/short-duration/rapid-removal" are pharmacokinetically '
        'synonymous descriptions without positive or negative connotations\u2014they '
        'represent neutral descriptions of drug disposition based on the anatomical '
        'site of deposition.'
    )

    p = doc.add_paragraph()
    add_superscript_citations(p,
        "We propose the concept of context-sensitive maximum dose for LAs, analogous "
        "to the context-sensitive half-time that transformed understanding of intravenous "
        "drug offset.{6} Under this framework, the effective maximum safe dose "
        "is not a single fixed value but varies with the clinical scenario (Table 1)."
    )

    # Table 1: Context-sensitive maximum dose framework
    add_table_to_doc(doc,
        ["Scenario", "Initial Compartment", "Expected Cmax", "Dose Implication"],
        [
            ["Successful block", "BPT (V3)", "Low, delayed", "Higher dose may be safe"],
            ["Partial block", "Mixed (BPT + BRT)", "Intermediate", "Standard limit applies"],
            ["Failed block", "BRT (V2)", "Moderate-high, early", "Lower dose may be needed"],
            ["Intravascular injection", "Plasma (V1)", "Very high, immediate", "Traditional IV limits apply"],
            ["Epidural", "Depot (multi-pathway)", "Intermediate, delayed", "Depot model approximation"],
        ],
    )
    cap = doc.add_paragraph()
    cap.paragraph_format.space_before = Pt(14)
    cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = cap.add_run("Table 1. ")
    run.bold = True
    run.font.size = Pt(10)
    run.font.name = 'Times New Roman'
    run = cap.add_run("Proposed context-sensitive maximum dose framework.")
    run.font.size = Pt(10)
    run.font.name = 'Times New Roman'

    p = doc.add_paragraph()
    add_superscript_citations(p,
        "This framework provides a pharmacokinetic rationale for the empirical observation "
        "that LAST is rare despite frequent exceeding of traditional mg/kg dose limits in "
        "regional anesthesia practice.{4} When the block is successful, the "
        "drug is sequestered in vessel-poor tissue with slow systemic release\u2014precisely "
        "the scenario where doses above traditional limits are routinely administered safely."
    )

    # 1.4
    doc.add_heading('1.4. Existing anesthesia simulators and positioning of yoshika', level=2)
    p = doc.add_paragraph(
        "Several open-source anesthesia simulation tools exist, but none address the specific "
        "problem of initial compartment selection for local anesthetics in regional anesthesia."
    )
    p = doc.add_paragraph()
    add_superscript_citations(p,
        "The Python Anesthesia Simulator (PAS){10} provides a general framework for "
        "simulating the effects of propofol, remifentanil, and norepinephrine during total "
        "intravenous anesthesia (TIVA). PAS is designed as a benchmark for the control community "
        "to design multidrug controllers, with pharmacokinetic models (Schnider, Marsh, Eleveld) "
        "that uniformly assume central compartment input."
    )
    p = doc.add_paragraph()
    add_superscript_citations(p,
        "The Anesthesia Response Simulator (AReS){11} extends TIVA simulation "
        "to propofol, remifentanil, norepinephrine, and rocuronium, with target-controlled "
        "infusion modules and surgical stimulus profiles. AReS is available in both Python "
        "and MATLAB and focuses on automated anesthesia control testing."
    )
    p = doc.add_paragraph()
    add_superscript_citations(p,
        "The AMICAS simulator{12} provides a MATLAB/Simulink-based patient "
        "simulator for multi-drug dosing control during general anesthesia, incorporating "
        "complex synergistic and antagonistic interactions between hypnosis, analgesia, and "
        "hemodynamic variables."
    )
    p = doc.add_paragraph(
        "All three simulators focus exclusively on intravenous general anesthetics and assume "
        "drug administration into the central (plasma) compartment. None addresses local "
        "anesthetics or the problem of route-dependent initial compartment selection that is "
        "central to regional anesthesia pharmacokinetics. yoshika fills this gap by providing "
        "a simulation tool specifically designed for local anesthetics with selectable initial "
        "compartment."
    )

    # 1.5
    doc.add_heading('1.5. Aim', level=2)
    p = doc.add_paragraph(
        "The aim of this study is to present yoshika, an open-source Python package for "
        "PKPD simulation of local anesthetics with selectable initial compartment, and to "
        "demonstrate how the choice of initial compartment affects predicted plasma "
        "concentration profiles and toxicity risk across clinically relevant scenarios."
    )

    # ===== 2. METHODS =====
    doc.add_heading('2. Methods', level=1)

    # 2.1
    doc.add_heading('2.1. Software architecture', level=2)
    p = doc.add_paragraph(
        "yoshika is structured as a modular Python package with the following components:"
    )
    components = [
        "compartments: Compartment definitions (PLASMA, BRT, BPT, DEPOT) and initial condition logic.",
        "drugs: Drug parameter database with four built-in local anesthetics (lidocaine, bupivacaine, ropivacaine, levobupivacaine) and custom drug support.",
        "model: Three-compartment PK ODE model solved with SciPy's solve_ivp (RK45 method).",
        "pd: Pharmacodynamic models (Emax, sigmoid Emax, effect-site equilibration).",
        "simulator: High-level API for single simulations and multi-scenario comparison.",
        "plotting: Matplotlib-based visualization utilities for concentration-time curves, effect profiles, and comparison plots.",
        "utils: Utility functions for AUC calculation, half-life estimation, and unit conversion.",
    ]
    for c in components:
        p = doc.add_paragraph(c, style='List Bullet')
        for run in p.runs:
            run.font.size = Pt(11)
            run.font.name = 'Times New Roman'
    p = doc.add_paragraph(
        "The package follows a clean separation of concerns: the PK model (ODE system) is independent "
        "of the PD model, and both are independent of the drug parameter database. This design allows "
        "users to substitute custom drug parameters, modify the PD model, or extend the compartment "
        "structure without affecting other components."
    )

    # 2.2
    doc.add_heading('2.2. Pharmacokinetic model', level=2)
    p = doc.add_paragraph()
    add_superscript_citations(p,
        "yoshika implements a standard three-compartment mammillary PK model with an optional "
        "depot compartment. The system of ordinary differential equations (ODEs) describes drug "
        "transfer between the central plasma compartment (V1), vessel-rich tissue (V2/BRT), "
        "vessel-poor tissue (V3/BPT), and an optional depot compartment with absorption rate "
        "constant ka. The ODEs are solved numerically using scipy.integrate.solve_ivp with the "
        "RK45 method (explicit Runge-Kutta of order 5(4), Dormand-Prince).{9}"
    )

    # Table 2: Initial conditions
    add_table_to_doc(doc,
        ["Initial Compartment", "A_depot(0)", "A1(0)", "A2(0)", "A3(0)"],
        [
            ["Plasma (IV)", "0", "Dose", "0", "0"],
            ["BRT (failed block)", "0", "0", "Dose", "0"],
            ["BPT (successful block)", "0", "0", "0", "Dose"],
            ["Depot (fascial plane)", "Dose", "0", "0", "0"],
        ],
    )
    cap = doc.add_paragraph()
    cap.paragraph_format.space_before = Pt(14)
    cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = cap.add_run("Table 2. ")
    run.bold = True
    run.font.size = Pt(10)
    run.font.name = 'Times New Roman'
    run = cap.add_run("Initial conditions for each selectable compartment.")
    run.font.size = Pt(10)
    run.font.name = 'Times New Roman'

    # 2.3
    doc.add_heading('2.3. Pharmacodynamic model', level=2)
    p = doc.add_paragraph(
        u"yoshika includes an effect-site compartment linked to the central compartment via a "
        u"first-order rate constant k\u2091\u2080. The drug effect is computed using a sigmoid Emax model: "
        u"E = E_max \u00d7 C\u2091\u1d5e / (EC\u2085\u2080\u1d5e + C\u2091\u1d5e), where C\u2091 is the "
        u"effect-site concentration, \u03b3 is the Hill coefficient, and EC\u2085\u2080 is the concentration "
        u"producing 50% of maximum effect."
    )

    # 2.4
    doc.add_heading('2.4. Drug parameter database', level=2)
    p = doc.add_paragraph()
    add_superscript_citations(p,
        "The package includes pharmacokinetic parameters for four commonly used local anesthetics: "
        "lidocaine, bupivacaine, ropivacaine, and levobupivacaine.{7,8} Parameters "
        "include compartment volumes (V1, V2, V3), clearances (CL, Q2, Q3), effect-site "
        u"equilibration rate (k\u2091\u2080), EC\u2085\u2080, Hill coefficient (\u03b3), protein binding fraction, "
        "and toxicity thresholds for CNS and cardiovascular systems. Users can also define custom drug "
        "parameters via the DrugLibrary.add_custom() API."
    )

    # 2.5
    doc.add_heading('2.5. Epidural administration approximation', level=2)
    p = doc.add_paragraph()
    add_superscript_citations(p,
        "Epidural administration can be approximated using the Depot compartment in yoshika. "
        "In epidural anesthesia, the drug is injected into the epidural space and is absorbed "
        "into the systemic circulation primarily through epidural venous plexus uptake, with "
        "concurrent diffusion across the dura into the cerebrospinal fluid (CSF). This absorption "
        "process follows approximately first-order kinetics, which is modeled by the depot "
        u"compartment's absorption rate constant (k\u2090).{8} While the actual epidural "
        "pharmacokinetics involves parallel pathways (vascular absorption, dural penetration, "
        "and epidural fat sequestration), the depot model provides a reasonable first-order "
        "approximation of the systemic absorption phase."
    )
    p = doc.add_paragraph(
        u"Users can adjust the k\u2090 parameter to match published epidural absorption rates for "
        u"specific local anesthetics. For example, epidural lidocaine has a reported systemic "
        u"absorption half-life of approximately 10\u201320 minutes, corresponding to k\u2090 values of "
        u"0.035\u20130.069 min\u207b\u00b9."
    )

    # ===== 3. RESULTS =====
    doc.add_heading('3. Results', level=1)

    # 3.1
    doc.add_heading('3.1. Comparison of plasma concentration profiles by initial compartment', level=2)
    p = doc.add_paragraph(
        "Figure 1 shows the three-compartment model with selectable initial compartment. "
        "To demonstrate the core functionality, bupivacaine 150 mg administered to a 70 kg patient "
        "was simulated across three initial compartment scenarios."
    )

    # Figure 1 inline
    add_figure_to_doc(doc, "fig1")

    p = doc.add_paragraph(
        "Figure 2 demonstrates the dramatic differences in plasma concentration-time "
        "profiles when bupivacaine 150 mg is administered to the same patient but with different initial "
        "compartments. The plasma-start scenario (equivalent to IV bolus) produces the highest and earliest "
        "Cmax, exceeding the CNS toxicity threshold. The BRT-start scenario (failed block) shows intermediate "
        "kinetics, while the BPT-start scenario (successful block) produces the lowest and most delayed Cmax, "
        "remaining below toxicity thresholds throughout."
    )

    # Figure 2 inline
    add_figure_to_doc(doc, "fig2")

    # 3.2
    doc.add_heading('3.2. Cross-drug comparison', level=2)
    p = doc.add_paragraph(
        "Figure 3 extends the comparison to all four local anesthetics (lidocaine, bupivacaine, "
        "ropivacaine, levobupivacaine), showing that the effect of initial compartment selection on "
        "plasma concentration profiles is consistent across drugs with different pharmacokinetic "
        "parameters."
    )

    # Figure 3 inline
    add_figure_to_doc(doc, "fig3")

    # 3.3
    doc.add_heading('3.3. Pharmacodynamic response', level=2)
    p = doc.add_paragraph(
        "Figure 4 shows the effect-site concentration and pharmacodynamic response for "
        "bupivacaine across initial compartments. Figure 5 shows the full "
        "compartment concentration profile for bupivacaine from BPT. Figure 6 provides "
        "a PK/PD summary comparing key parameters across initial compartments."
    )

    # Figure 4
    add_figure_to_doc(doc, "fig4")
    # Figure 5
    add_figure_to_doc(doc, "fig5")
    # Figure 6
    add_figure_to_doc(doc, "fig6")

    # ===== 4. DISCUSSION =====
    doc.add_heading('4. Discussion', level=1)

    # 4.1
    doc.add_heading('4.1. Clinical implications', level=2)
    p = doc.add_paragraph(
        "yoshika addresses a gap in the pharmacokinetic simulation landscape by providing the first "
        "open-source tool that allows users to select the initial compartment of drug deposition for "
        "local anesthetics."
    )
    p = doc.add_paragraph()
    add_superscript_citations(p,
        "In clinical pharmacology and toxicology, by quantifying how the initial compartment "
        "determines peak plasma concentration and time-to-toxicity, yoshika provides a computational "
        "basis for reconsidering maximum recommended doses of local anesthetics. The context-sensitive "
        "maximum dose framework (Table 1) challenges the longstanding practice of "
        "applying IV-derived mg/kg limits to regional anesthesia, where absorption kinetics differ "
        "fundamentally from intravenous administration."
    )
    p = doc.add_paragraph()
    add_superscript_citations(p,
        "In anesthesia information management systems (AIMS), yoshika demonstrates that route-adaptive "
        "PKPD simulation is computationally feasible with standard ODE solvers and can be integrated "
        "into existing AIMS infrastructure.{1} Modern AIMS increasingly "
        "incorporate real-time PKPD displays for intravenous agents (e.g., propofol, remifentanil) using "
        "standard three-compartment models that assume central compartment input. When the "
        "same AIMS tracks local anesthetic doses administered via regional techniques, the underlying PK "
        "model remains unchanged, producing predictions based on IV kinetics that may significantly "
        "overestimate peak plasma concentrations after successful regional blocks."
    )
    p = doc.add_paragraph(
        "Block success can serve as a real-time pharmacokinetic risk indicator. If block success is "
        "inferred from clinical assessment (e.g., onset of sensory block within expected timeframes), "
        "clinicians could update their toxicity risk assessment in real time using yoshika's simulation "
        "framework."
    )

    # 4.2
    doc.add_heading('4.2. Comparison with existing anesthesia simulators', level=2)

    add_table_to_doc(doc,
        ["Feature", "PAS", "AReS", "AMICAS", "yoshika"],
        [
            ["Drug class", "General (propofol, remifentanil)", "General (propofol, remifentanil, rocuronium)", "General (propofol, remifentanil)", "Local anesthetics"],
            ["Administration route", "IV only", "IV only", "IV only", "Selectable (IV, BRT, BPT, Depot)"],
            ["Language", "Python", "Python/MATLAB", "MATLAB/Simulink", "Python"],
            ["PD model", "BIS, MAP, CO", "BIS, MAP, CO, NMB", "BIS, MAP, CO", "Sigmoid Emax (nerve block)"],
            ["Target application", "TIVA drug control", "Automated anesthesia testing", "Multi-drug dosing control", "Regional anesthesia PKPD"],
            ["License", "Open source", "MIT", "Open source", "MIT"],
        ],
    )
    cap = doc.add_paragraph()
    cap.paragraph_format.space_before = Pt(14)
    cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = cap.add_run("Table 3. ")
    run.bold = True
    run.font.size = Pt(10)
    run.font.name = 'Times New Roman'
    run = cap.add_run("Comparison of open-source anesthesia simulators.")
    run.font.size = Pt(10)
    run.font.name = 'Times New Roman'

    p = doc.add_paragraph(
        "The key differentiator of yoshika is its focus on local anesthetics and the selectable initial "
        "compartment, which addresses a fundamentally different clinical scenario (regional anesthesia) "
        "from the IV general anesthesia focus of existing tools."
    )

    # 4.3
    doc.add_heading('4.3. Limitations', level=2)
    p = doc.add_paragraph("Several limitations should be acknowledged.")
    p = doc.add_paragraph()
    add_superscript_citations(p,
        "First, the pharmacokinetic parameters used in yoshika are derived from intravenous "
        "pharmacokinetic studies.{7} When these parameters are applied to non-IV routes "
        "(BRT, BPT, Depot), the intercompartmental transfer rate constants are assumed to remain "
        "unchanged regardless of the initial compartment. This assumption has not been validated "
        "with clinical data from regional anesthesia and represents a simplification of the "
        "underlying pharmacokinetics."
    )
    p = doc.add_paragraph()
    add_superscript_citations(p,
        "Second, the three-compartment model does not capture the full complexity of LA tissue "
        "pharmacokinetics. In reality, LA distribution involves pH-dependent ionization equilibria,{2,3} "
        "binding to tissue proteins and lipids, and site-specific absorption pathways that vary with "
        "anatomical location. The compartmental model provides a macroscopic approximation of these processes."
    )
    p = doc.add_paragraph(
        "Third, spinal (subarachnoid/intrathecal) administration is not modeled in the current version. "
        "Intrathecal injection delivers drug directly into the cerebrospinal fluid (CSF), involving "
        "unique pharmacokinetics (CSF spread, direct spinal cord uptake, and subsequent systemic "
        "absorption) that differ fundamentally from the peripheral compartment model."
    )
    p = doc.add_paragraph(
        "Fourth, the current version does not implement population pharmacokinetic variability or "
        "covariate models (e.g., age, hepatic function, cardiac output). Individual patient parameters "
        "can be customized through the API, but systematic population modeling is not yet supported."
    )

    # 4.4
    doc.add_heading('4.4. Future directions', level=2)
    p = doc.add_paragraph(
        "Future development directions include systematic measurement of plasma concentration profiles "
        "after various regional block types with concurrent documentation of block success, to "
        "parameterize compartment-specific absorption models. Prospective validation of the "
        "context-sensitive maximum dose framework would require clinical studies correlating block "
        "success, administered dose, and measured plasma concentrations. Integration of population "
        "pharmacokinetic models and covariate-based parameter adjustment would enhance clinical "
        "applicability."
    )

    # ===== 5. CONCLUSIONS =====
    doc.add_heading('5. Conclusions', level=1)
    p = doc.add_paragraph(
        "yoshika is an open-source Python package that fills a specific gap in pharmacokinetic "
        "simulation tools: the ability to select the initial compartment of drug deposition for "
        "local anesthetics in regional anesthesia. By enabling simulation of clinically distinct "
        u"scenarios\u2014successful block (BPT start), failed block (BRT start), intravascular injection "
        u"(Plasma start), and depot absorption (fascial plane/epidural)\u2014yoshika provides a "
        "computational framework for exploring context-sensitive maximum dose recommendations and "
        "route-adaptive PKPD simulation."
    )
    p = doc.add_paragraph(
        "The clinical significance of this approach is substantial: traditional mg/kg dose limits "
        "derived from IV pharmacokinetics do not account for the fundamentally different absorption "
        "kinetics of regional anesthesia. yoshika quantifies these differences and supports the "
        "development of evidence-based, route-specific dose guidelines. The software is freely "
        "available under the MIT license at https://github.com/bougtoir/yoshika-pkpd and can be "
        "installed via pip."
    )

    # ===== SOFTWARE AVAILABILITY =====
    doc.add_heading('Software availability', level=1)
    p = doc.add_paragraph(
        "The source code for yoshika is publicly available at https://github.com/bougtoir/yoshika-pkpd "
        "under the MIT license. The package requires Python >= 3.9 with NumPy, SciPy, Matplotlib, and "
        "Pandas as dependencies. Installation is available via pip install yoshika or from source. "
        "Documentation and usage examples are provided in the repository README."
    )

    # ===== DECLARATIONS =====
    doc.add_heading('Declaration of competing interest', level=1)
    p = doc.add_paragraph(
        "The authors declare that they have no known competing financial interests or personal "
        "relationships that could have appeared to influence the work reported in this paper."
    )

    doc.add_heading('CRediT authorship contribution statement', level=1)
    p = doc.add_paragraph()
    run = p.add_run("Tatsuki Onishi: ")
    run.bold = True
    run.font.size = Pt(11)
    run.font.name = 'Times New Roman'
    run = p.add_run("Conceptualization, Methodology, Software, Validation, Writing \u2013 Original Draft, Writing \u2013 Review & Editing.")
    run.font.size = Pt(11)
    run.font.name = 'Times New Roman'

    doc.add_heading('Acknowledgements', level=1)
    p = doc.add_paragraph("None.")

    # ===== REFERENCES =====
    doc.add_heading('References', level=1)
    for i, ref in enumerate(REFERENCES, 1):
        p = doc.add_paragraph()
        p.paragraph_format.space_after = Pt(4)
        run = p.add_run(f"[{i}] ")
        run.bold = True
        run.font.size = Pt(10)
        run.font.name = 'Times New Roman'
        run = p.add_run(ref)
        run.font.size = Pt(10)
        run.font.name = 'Times New Roman'

    # Save
    output_path = OUTPUT_DIR / "yoshika_CMPB_Update_manuscript.docx"
    doc.save(str(output_path))
    print(f"Saved: {output_path}")
    return output_path


def generate_pptx():
    """Generate editable .pptx with all figures (one per slide)."""
    prs = Presentation()
    prs.slide_width = PptxInches(13.333)
    prs.slide_height = PptxInches(7.5)

    for fig_key in ["fig1", "fig2", "fig3", "fig4", "fig5", "fig6"]:
        filename, label, caption = FIGURE_FILES[fig_key]
        filepath = FIG_DIR / filename
        if not filepath.exists():
            continue

        # Add blank slide
        slide_layout = prs.slide_layouts[6]  # Blank
        slide = prs.slides.add_slide(slide_layout)

        # Title at top
        from pptx.util import Inches as PI
        title_box = slide.shapes.add_textbox(PI(0.5), PI(0.2), PI(12.333), PI(0.6))
        tf = title_box.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.text = label
        p.font.size = PptxPt(24)
        p.font.bold = True
        p.alignment = PP_ALIGN.CENTER

        # Image centered
        img = Image.open(filepath)
        img_w, img_h = img.size
        max_w = PptxInches(11.0)
        max_h = PptxInches(5.0)
        scale = min(max_w / PptxInches(img_w / 96.0), max_h / PptxInches(img_h / 96.0))
        actual_w = int(PptxInches(img_w / 96.0) * scale)
        actual_h = int(PptxInches(img_h / 96.0) * scale)

        # Center horizontally and vertically
        left = (prs.slide_width - actual_w) // 2
        top = PptxInches(1.0)
        slide.shapes.add_picture(str(filepath), left, top, actual_w, actual_h)

        # Caption at bottom
        cap_box = slide.shapes.add_textbox(PI(0.5), PI(6.5), PI(12.333), PI(0.8))
        tf = cap_box.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.text = f"{label}. {caption}"
        p.font.size = PptxPt(14)
        p.alignment = PP_ALIGN.CENTER

    output_path = OUTPUT_DIR / "yoshika_CMPB_Update_figures.pptx"
    prs.save(str(output_path))
    print(f"Saved: {output_path}")
    return output_path


if __name__ == "__main__":
    docx_path = generate_docx()
    pptx_path = generate_pptx()
    print("Done!")
