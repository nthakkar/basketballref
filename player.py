""" player.py

Functionality to load player histories by pulling data from HTML queries of 
basketball_reference.com. 

NB: This script actually uses the structure of the HTML to help it more - its
a better example of how this ought to be done."""
import numpy as np
import pandas as pd
from pyquery import PyQuery as pq

## Base URLs for queries
PLAYER_LIST_URL = "https://www.basketball-reference.com/players/{0:s}/"
GAMELOG_URL = "https://www.basketball-reference.com/players/{0:.1s}/{0:s}/gamelog/{1:d}"
ADV_GAMELOG_URL = "https://www.basketball-reference.com/players/{0:.1s}/{0:s}/gamelog-advanced/{1:d}"

### String processing functions and regular expresions (internal methods)
######################################################################################
replace = {"":np.nan}
def _process_webpage(webpage):

	""" Process regular and advanced gamelog webpages to extract player stat lines
	from games in a particular season. 

	This is done somewhat strangely because the playoff table is hidden in a comment (why?) """

	## Get the tables from the webpage (filtered to be row summable
	## tables which are actual data tables, as opposed to tables used
	## throughout the page just for organization).
	tables = webpage("table").filter(".row_summable")

	## Catch pages with no data (i.e. seasons where the player didn't play)
	## in that case, pass an empty dataframe back.
	if tables.size() == 0:
		return pd.DataFrame([],columns=["date"])
	
	## Process the tables into data frames
	dfs = []
	for table in tables.items():

		## Get the column headings, changing some
		## empty entries to more meaningful labels
		columns = {i.attr("data-stat"):i.text() for i in table("thead")("th").items()}
		columns["game_location"] = "away_game"
		columns["game_result"] = "game_result"
		columns["date_game"] = "date"
		columns["gs"] = "started"

		## Loop through the table body and collect rows
		rows = []
		for row in table("tbody")("tr").items():

			## Skip any subheadings
			if row.attr("class") == "thead":
				continue

			## Extract data from valid rows
			this_row = {i.attr("data-stat"):replace.get(i.text(),i.text()) for i in row("td").items()}
			rows.append(this_row)

		## Make a dataframe and store it
		df = pd.DataFrame(rows)
		dfs.append(df)

	## Concatenate the dataframes
	df = pd.concat(dfs,axis=0,sort=False,ignore_index=True)

	## Some light clean-up and type conversion
	df.rename(columns=columns,inplace=True)
	df["away_game"] = df["away_game"].apply(lambda x: x == "@")
	df = df.apply(lambda x: pd.to_numeric(x,errors="ignore"))
	df["date"] = pd.to_datetime(df.date)

	return df

### Player object and method for list retreival
######################################################################################
def GetPlayerList(letters="abcdefghijklmnopqrstuvwyz"):

	""" Get a list of all players with basic info (when they were active, weight, height, and
	position). Notice the default letters don't include x, since basketball_reference.com has no
	x page (i.e. no players ever have a list name that starts with x). 

	This method returns a dataframe with players as indices, information as columns. The key info here
	is the abbreviation associated with their player profile URL. """

	## Loop over letters for each webpage and collect
	## names one-by-one
	dfs = []
	for letter in letters:

		## Get the webpage and slice it and use pyquery
		## to extract the table object on it.
		webpage = pq(PLAYER_LIST_URL.format(letter))("table")
		
		## Rip the header off of the table object to get the
		## column names (from the aria-label attribute). This is a dictionary
		## keeping track of how they're referenced in the table body.
		columns = {entry.attr("data-stat"):entry.attr("aria-label").lower().replace(" ","_") for entry in webpage("thead")("th").items()}

		## Get the rest of the table by looping through rows in
		## the body and retreiving entries
		table = []
		for tr in webpage("tbody")("tr").items():
				
			## Initialize the row
			this_row = {}

			## Get the URI and player name from the row index
			this_row["uri"] = tr("th").attr("data-append-csv")
			this_row["player"] = tr("th").text()

			## Append whatever data remains in the following
			## columns.
			for entry in tr("td").items():
				this_row[entry.attr("data-stat")] = entry.text()

			## Store the row
			table.append(this_row)

		## Make it a dataframe
		df = pd.DataFrame(table)

		## Clean up the column names, etc.
		df = df.rename(columns=columns)
		df["player"] = df.player.str.replace("*","")
		df = df.apply(lambda x: pd.to_numeric(x,errors="ignore"))

		## Store it
		dfs.append(df)

	return pd.concat(dfs,axis=0)

class Player(object):

	""" Basic player object, which encapsulates player information and a dataframe of
	the player's game log. """

	def __init__(self,uri,seasons,advanced=True):

		""" uri = URL specific look up associated with the player. See the full player list for details.
		An example is jordami01 for Jordan, etc. """

		## Store the URI for reference
		self._uri = uri
		if advanced:
			base_urls = [GAMELOG_URL,ADV_GAMELOG_URL]
		else:
			base_urls = [GAMELOG_URL]
		
		## Loop over seasons to collect game logs for each -
		## seasons can be found in the full player list. This is 
		## encased in loop over URLs, since advanced stats are on
		## a seperate page
		to_merge = []
		for base_url in base_urls:
			
			## Initialize storage for all the data from
			## this base url (basic/advanced)
			dfs = []
			for season in seasons:

				## Get the webpage
				url = base_url.format(self._uri,season)
				webpage = pq(url)

				## In this case, some tables (particularly the playoff tables)
				## are hidden in the HTML comments (I don't understand this),
				## so I have to forcibly uncomment that section.
				webpage = str(webpage).replace("\n<!--\n","\n").replace("\n-->\n","\n")
				webpage = pq(webpage)

				## Extract the table from the webpage
				## as a dataframe.
				df = _process_webpage(webpage)

				## And append it to the list
				dfs.append(df)

			## Put it all together, index by date,
			## and save it to be merged.
			to_merge.append(pd.concat(dfs,ignore_index=True,sort=False).set_index("date"))

		## Merge if needed by finding new columns in the
		## advanced page and adding them to the basic page.
		if advanced:
			columns_to_add = to_merge[1].columns.difference(to_merge[0].columns)
			self.df = pd.concat([to_merge[0],to_merge[1][columns_to_add]],axis=1)
		else:
			self.df = to_merge[0]

		## Create a title based on the seasons selected.
		if len(seasons) == 1:
			self.title = uri+", {} game-log".format(seasons[0])
		else:
			self.title = uri+", {}-{} game-log".format(seasons[0],seasons[-1])
		self.title += (1-advanced)*" (basic only)"

	def __repr__(self):
		return self.title


if __name__ == "__main__":

	## Get the player list and pickle it
	#df = GetPlayerList()
	#df.to_pickle("..\\pickle_jar\\player_list.pkl")
	#print(df)

	## Get a specific player
	#p = Player("jordami01",[2017],advanced=True)
	#p = Player("bookede01",[2016,2017,2018])
	p = Player("jamesle01",[1999,2018])
	#p = Player("yuesu01",[2009])
	#p = Player("wagnemo01",[2018,2019])
	print(p)
	print(p.df.started)