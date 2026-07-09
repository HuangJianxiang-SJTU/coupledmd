#!/usr/bin/env python3
"""Generate Scientific Data Figure 1 only."""

from generate_scidata_main_figures import build_circos, load_tables


def main() -> None:
    build_circos(load_tables())


if __name__ == "__main__":
    main()
