""" player_compare.py

Compare game-by-game statistics for players using the basketballref.player module. """
## Add the basketball reference repository to your path
import sys
sys.path.insert(0,"..\\")

## Data manipulation
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

## From the bball lib
from basketballref.player import Player, GetPlayerList
import basketballref.plot_env 

## For progress bars
from tqdm import tqdm

def ProcessPlayers(players,player_list,advanced=True):

	""" Function to create a dictionary of Player object inputs for
	each player in players. """

	## Subset the player list and type convert
	## into a list of dictionaries for each
	player_info = player_list.loc[player_list.player.isin(players)].to_dict("records")

	## Reframe that into the appropiate dictionary of 
	## tuples.	
	output = {d["player"]:(d["uri"],range(d["first_year"],d["last_year"]+1),advanced) for d in player_info}
	return output

if __name__ == "__main__":

	## Choose the players you want to compare
	players = ["Michael Jordan","James Harden","Devin Booker"]

	## Get the lookup table to find their active years
	## and their URIs
	player_list = GetPlayerList(letters="bhj")
	
	## Scrape their stats
	p_inputs = ProcessPlayers(players,player_list,advanced=False)
	print("\nScraping player statistics...")
	data = {player:Player(*inputs).df for player, inputs in tqdm(p_inputs.items())}

	## Plot their career time series
	to_plot = ["PTS","AST","TRB","GmSc"]
	fig, axes = plt.subplots(len(players),1,figsize=(16,12),sharey=True,sharex=True)

	## Loop and plot
	for p, player in enumerate(players):
		
		## Get the data
		df = data[player]

		## Plot the timeseries
		axes[p].grid(color="grey",alpha=0.2)
		for i, c in enumerate(to_plot):
			axes[p].plot(df.index,df[c].values,ls="None",marker="o",color="C"+str(i))
		
		## Label the plot
		axes[p].text(0.025,0.95,player,fontsize="28",color="k",
					horizontalalignment="left",verticalalignment="top",transform=axes[p].transAxes)

	## Make the legend
	for i,c in enumerate(to_plot):
		axes[-1].plot([],marker="o",ls="None",label=c,color="C"+str(i))
	axes[-1].legend(loc=3)

	## Finish up
	plt.tight_layout()
	plt.show()






