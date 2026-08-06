"""Published plasma concentration reference data for external validation of yoshika.

Each record digitizes the summary pharmacokinetic parameters (peak plasma
concentration Cmax, time-to-peak Tmax) reported in a peer-reviewed clinical
study of local anesthetic administration by a regional / depot route. These
values are used to assess the face validity of the depot-augmented
three-compartment model against real, non-intravenous administration data.

All concentrations are total (protein-bound + free) plasma/serum concentrations
in mg/L (== microgram/mL). Times are in minutes. Doses are total administered
milligrams. `sampling` records whether the reported peak is venous or arterial,
because venous samples systematically under-read the true central-compartment
peak relative to arterial samples.

References (all verified against the primary source):

[V1] Behnke H, Worthmann F, Cornelissen J, Kahl M, Wulf H. Plasma concentration
     of ropivacaine after intercostal blocks for video-assisted thoracic
     surgery. Br J Anaesth 2002;89(2):251-253. doi:10.1093/bja/aef185
[V2] Kopacz DJ, Emanuelsson BM, Thompson GE, Carpenter RL, Stephenson CA.
     Pharmacokinetics of ropivacaine and bupivacaine for bilateral intercostal
     blockade in healthy male volunteers. Anesthesiology 1994;81(5):1139-1148.
     PMID:7978472
[V4] Murouchi T, Iwasaki S, Yamakage M. Chronological changes in ropivacaine
     concentration and analgesic effects between transversus abdominis plane
     block and rectus sheath block (arterial sampling). Reg Anesth Pain Med
     2015;40(5):568-571. doi:10.1097/AAP.0000000000000288
[V5] Hickey R, Blanchard J, Hoffman J, Sjovall J, Ramamurthy S. Plasma
     concentrations of ropivacaine given with or without epinephrine for
     brachial plexus block. Can J Anaesth 1990;37(8):878-882. doi:10.1007/BF03006624
[V6] Vainionpaa VA, Haavisto ET, Huha TM, Korpi K, Nuutinen LS, Hollmen AI. A
     clinical and pharmacokinetic comparison of ropivacaine and bupivacaine in
     axillary plexus block. Anesth Analg 1995;81(3):534-538.
     doi:10.1097/00000539-199509000-00019
[V7] Inoue R, Suganuma T, Echizen H, Ishizaki T, Kushida K, Tomono Y. Plasma
     concentrations of lidocaine and its principal metabolites during
     intermittent epidural anesthesia. Anesthesiology 1985;63(3):304-310.
     doi:10.1097/00000542-198509000-00011
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ValidationRecord:
    """A single published Cmax/Tmax observation for a depot-route LA study."""

    label: str
    drug: str          # matches yoshika DrugLibrary key
    route: str         # clinical technique
    dose_mg: float
    weight_kg: float
    obs_cmax_mg_l: float
    obs_cmax_sd: float
    obs_tmax_min: float
    obs_tmax_sd: float
    sampling: str      # "venous" | "arterial"
    reference: str


# Digitized reference dataset. Where a study reported several doses, the
# clinically representative dose group is used. Weight defaults to 70 kg when a
# study did not report a group mean (noted in the manuscript limitations).
VALIDATION_DATA: list[ValidationRecord] = [
    ValidationRecord(
        label="Intercostal 0.75% (150 mg)",
        drug="ropivacaine", route="Intercostal block", dose_mg=150.0,
        weight_kg=70.0, obs_cmax_mg_l=2.4, obs_cmax_sd=1.0,
        obs_tmax_min=11.3, obs_tmax_sd=5.0, sampling="venous", reference="V1",
    ),
    ValidationRecord(
        label="Intercostal 1.0% (200 mg)",
        drug="ropivacaine", route="Intercostal block", dose_mg=200.0,
        weight_kg=70.0, obs_cmax_mg_l=2.5, obs_cmax_sd=0.9,
        obs_tmax_min=12.2, obs_tmax_sd=8.0, sampling="venous", reference="V1",
    ),
    ValidationRecord(
        label="Bilateral intercostal (140 mg)",
        drug="ropivacaine", route="Intercostal block", dose_mg=140.0,
        weight_kg=75.0, obs_cmax_mg_l=1.1, obs_cmax_sd=0.4,
        obs_tmax_min=21.0, obs_tmax_sd=9.0, sampling="venous", reference="V2",
    ),
    ValidationRecord(
        label="Bilateral intercostal bupiv (140 mg)",
        drug="bupivacaine", route="Intercostal block", dose_mg=140.0,
        weight_kg=75.0, obs_cmax_mg_l=0.9, obs_cmax_sd=0.2,
        obs_tmax_min=30.0, obs_tmax_sd=8.0, sampling="venous", reference="V2",
    ),
    ValidationRecord(
        label="TAP block (arterial, 150 mg)",
        drug="ropivacaine", route="Fascial plane block", dose_mg=150.0,
        weight_kg=55.0, obs_cmax_mg_l=1.83, obs_cmax_sd=0.41,
        obs_tmax_min=35.0, obs_tmax_sd=12.0, sampling="arterial", reference="V4",
    ),
    ValidationRecord(
        label="Rectus sheath block (arterial, 150 mg)",
        drug="ropivacaine", route="Fascial plane block", dose_mg=150.0,
        weight_kg=55.0, obs_cmax_mg_l=1.79, obs_cmax_sd=0.33,
        obs_tmax_min=53.0, obs_tmax_sd=16.0, sampling="arterial", reference="V4",
    ),
    ValidationRecord(
        label="Subclavian brachial plexus (190 mg)",
        drug="ropivacaine", route="Peripheral nerve block", dose_mg=190.0,
        weight_kg=70.0, obs_cmax_mg_l=1.3, obs_cmax_sd=0.4,
        obs_tmax_min=53.0, obs_tmax_sd=15.0, sampling="venous", reference="V5",
    ),
    ValidationRecord(
        label="Axillary plexus ropiv (~175 mg)",
        drug="ropivacaine", route="Peripheral nerve block", dose_mg=175.0,
        weight_kg=70.0, obs_cmax_mg_l=1.28, obs_cmax_sd=0.21,
        obs_tmax_min=52.0, obs_tmax_sd=15.0, sampling="venous", reference="V6",
    ),
    ValidationRecord(
        label="Axillary plexus bupiv (~175 mg)",
        drug="bupivacaine", route="Peripheral nerve block", dose_mg=175.0,
        weight_kg=70.0, obs_cmax_mg_l=1.28, obs_cmax_sd=0.47,
        obs_tmax_min=58.0, obs_tmax_sd=18.0, sampling="venous", reference="V6",
    ),
    ValidationRecord(
        label="Epidural lidocaine 2% (~350 mg)",
        drug="lidocaine", route="Epidural", dose_mg=350.0,
        weight_kg=60.0, obs_cmax_mg_l=2.3, obs_cmax_sd=0.46,
        obs_tmax_min=20.0, obs_tmax_sd=6.0, sampling="venous", reference="V7",
    ),
]
