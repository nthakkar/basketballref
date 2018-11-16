"""plot_env.py

A default plotting environment. """

import matplotlib.pyplot as plt

## Custom global matplotlib parameters
## see http://matplotlib.org/users/customizing.html for details.
plt.rcParams["font.size"] = 22.
plt.rcParams["font.family"] = "serif"
plt.rcParams["font.sans-serif"] = "DejaVu Sans"
plt.rcParams["font.serif"] = "Garamond"
plt.rcParams["xtick.labelsize"] = "medium"
plt.rcParams["ytick.labelsize"] = "medium"
plt.rcParams["legend.fontsize"] = "medium"
plt.rcParams["axes.linewidth"] = 1.0
plt.rcParams["axes.formatter.use_mathtext"] = True
plt.rcParams["mathtext.fontset"] = "cm"