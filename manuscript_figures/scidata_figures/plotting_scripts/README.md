# Publication plotting scripts

This directory contains the current generators for the final 208-system publication figures.

Run commands from `scidata_figures/`:

```bash
# Main Figures 1–6: split entry points
python plotting_scripts/figure1_plot.py
python plotting_scripts/figure2_plot.py
python plotting_scripts/figure3_plot.py
python plotting_scripts/figure4_plot.py
python plotting_scripts/figure5_plot.py
python plotting_scripts/figure6_plot.py

# Equivalent shared generator interface
python plotting_scripts/final208_figures.py 1  # replace 1 with 2–6 as needed

# Supplementary figures
python plotting_scripts/supplementary_s1_plot.py
./plotting_scripts/supplementary_s2_plot.py
```

All outputs are written to `publication_figures_final208/`. Superseded plotting pipelines are retained in `legacy/plotting_scripts/`.
