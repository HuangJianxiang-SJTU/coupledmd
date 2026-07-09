#!/usr/bin/env python3
"""Generate Scientific Data Figure 4 only."""

from generate_scidata_main_figures import build_qc, load_tables


def main() -> None:
    build_qc(load_tables())


if __name__ == "__main__":
    main()
