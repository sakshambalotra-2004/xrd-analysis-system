"""
utils/constants.py
==================
Application-wide constants for the XRD Analysis System.

All values here are fixed physical/domain constants.
Tuneable runtime parameters belong in config.py.
"""

# ---------------------------------------------------------------------------
# X-ray source wavelengths (Ångströms)
# ---------------------------------------------------------------------------
WAVELENGTH_CU_KA1 = 1.54056   # Cu Kα₁  (most common laboratory source)
WAVELENGTH_CU_KA2 = 1.54439   # Cu Kα₂
WAVELENGTH_CU_KA  = 1.54184   # Cu Kα average (weighted)
WAVELENGTH_MO_KA  = 0.71073   # Mo Kα  (common for single-crystal)
WAVELENGTH_CO_KA  = 1.78897   # Co Kα
WAVELENGTH_CR_KA  = 2.29100   # Cr Kα

# ---------------------------------------------------------------------------
# Scherrer shape factors
# ---------------------------------------------------------------------------
SCHERRER_K_SPHERICAL   = 0.89   # Spherical crystallites (most common)
SCHERRER_K_CUBIC       = 0.94   # Cubic crystallites
SCHERRER_K_GENERAL     = 1.00   # Upper bound / unknown shape

# ---------------------------------------------------------------------------
# Crystal systems
# ---------------------------------------------------------------------------
CRYSTAL_SYSTEMS = [
    "Cubic",
    "Tetragonal",
    "Orthorhombic",
    "Hexagonal",
    "Trigonal",
    "Monoclinic",
    "Triclinic",
]

# ---------------------------------------------------------------------------
# XRD angle range limits
# ---------------------------------------------------------------------------
TWO_THETA_MIN_DEG = 0.0
TWO_THETA_MAX_DEG = 180.0

# Typical laboratory scan range
TYPICAL_SCAN_MIN = 10.0
TYPICAL_SCAN_MAX = 90.0

# ---------------------------------------------------------------------------
# Database field names (used as keys in JSON standard files)
# ---------------------------------------------------------------------------
DB_FIELD_COMPOUND   = "compound_name"
DB_FIELD_FORMULA    = "formula"
DB_FIELD_CRYSTAL    = "crystal_system"
DB_FIELD_SPACE_GRP  = "space_group"
DB_FIELD_PEAKS      = "peaks"
DB_FIELD_2THETA     = "two_theta"
DB_FIELD_D          = "d"
DB_FIELD_INTENSITY  = "intensity"
DB_FIELD_H          = "h"
DB_FIELD_K          = "k"
DB_FIELD_L          = "l"

# ---------------------------------------------------------------------------
# Report constants
# ---------------------------------------------------------------------------
REPORT_TITLE = "XRD Compound Identification and Analysis Report"
REPORT_AUTHOR = "XRD Analysis System"
REPORT_VERSION = "1.0"

# ---------------------------------------------------------------------------
# SQLite table names
# ---------------------------------------------------------------------------
TABLE_EXPERIMENTS       = "experiments"
TABLE_ANALYSIS_RESULTS  = "analysis_results"
TABLE_PEAKS             = "peaks"
TABLE_COMPOUNDS         = "compounds"