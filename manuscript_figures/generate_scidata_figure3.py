#!/usr/bin/env python3
"""Generate Scientific Data Figure 3 only."""

from generate_scidata_main_figures import build_validation, load_tables


def main() -> None:
    build_validation(load_tables())


if __name__ == "__main__":
    main()
