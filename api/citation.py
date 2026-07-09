"""
Citation and provenance stamping for CoupledMD.

Provides:
  - Citation text for UI and API responses
  - Provenance headers for CSV/JSON/PDB file downloads
  - CITATION.cff content
"""

# Pre-publication: DOI / Zenodo / repository URL are pending. Use a single
# constant so the wording stays consistent everywhere it is shown to users.
PENDING_DOI = "DOI pending (pre-publication)"
PENDING_ZENODO = "Zenodo DOI pending (pre-publication)"
PENDING_REPO = "repository URL pending (pre-publication)"

CITATION_TEXT = (
    "Huang J et al., CoupledMD: a web resource for GPCR–G-protein molecular dynamics. "
    "Citation details to be confirmed (pre-publication)."
)

ZENODO_DOI = PENDING_ZENODO

DATA_LICENSE = "CC-BY-4.0"
CODE_LICENSE = "MIT"

CITATION_CFF = """\
cff-version: 1.2.0
message: "If you use CoupledMD data or software, please cite:"
type: software
title: CoupledMD
version: 1.0.0
authors:
  - family-names: Huang
    given-names: Jianxiang
repository-code: https://github.com/coupledmd/coupledmd
license: MIT
keywords:
  - GPCR
  - G-protein
  - molecular dynamics
  - web server
identifiers:
  - type: doi
    value: 10.0000/placeholder
    description: "Zenodo archive of the CoupledMD dataset (DOI pending pre-publication)"
"""

# Provenance header lines for different file formats
CSV_PROVENANCE_HEADER = [
    f"# CoupledMD — GPCR-G-protein MD web resource",
    f"# Citation: {CITATION_TEXT}",
    f"# Data licence: {DATA_LICENSE}",
    f"# Code licence: {CODE_LICENSE}",
    f"# Zenodo DOI: {ZENODO_DOI}",
    f"# Generated: {PENDING_DOI}",
]

JSON_PROVENANCE = {
    "_provenance": {
        "source": "CoupledMD",
        "citation": CITATION_TEXT,
        "data_licence": DATA_LICENSE,
        "code_licence": CODE_LICENSE,
        "zenodo_doi": ZENODO_DOI,
    }
}

PDB_REMARK_LINES = [
    f"REMARK   1 COUPLEDMD — GPCR-G-protein MD web resource",
    f"REMARK   2 Citation: {CITATION_TEXT}",
    f"REMARK   3 Data licence: {DATA_LICENSE}",
    f"REMARK   4 Zenodo DOI: {ZENODO_DOI}",
]


def get_citation_block() -> dict:
    """Return citation info for API/UI consumption."""
    return {
        "text": CITATION_TEXT,
        "data_licence": DATA_LICENSE,
        "code_licence": CODE_LICENSE,
        "zenodo_doi": ZENODO_DOI,
        "bibtex": (
            "@article{huang2026coupledmd,\n"
            "  title={CoupledMD: a web resource for GPCR--G-protein molecular dynamics},\n"
            "  author={Huang, Jianxiang},\n"
            "  journal={TBD (pre-publication)},\\n"
            "  year={2026},\n"
            "  note={" + PENDING_DOI + "}\n"
            "}"
        ),
    }
