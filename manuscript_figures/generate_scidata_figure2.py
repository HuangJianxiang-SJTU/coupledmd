#!/usr/bin/env python3
"""Generate Scientific Data Figure 2 only."""

from generate_scidata_main_figures import build_figure2, load_tables


def main() -> None:
    build_figure2(load_tables())


if __name__ == "__main__":
    main()
