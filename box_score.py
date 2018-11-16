"""box_score.py

Functionality to create box score objects by pulling data from HTML queries of 
basketball_reference.com. """
import numpy as np
import pandas as pd
from pyquery import PyQuery as pq

## Base URL for queries
BOXSCORE_URL = "https://www.basketball-reference.com/boxscores/{0:s}.html"

### String processing functions and regular expresions
######################################################################################
def _title_process(title):
	away_team = title[:title.find(" at ")]
	home_team = title[title.find(" at ")+len(" at "):title.find(" Box Score,")]
	date = pd.to_datetime(title[title.find("Box Score,")+len("Box Score, "):])
	return home_team, away_team, date

def _process_webpage(webpage):

	""" HTML processing function for the PQ webpage object. This is a refactor of the 
	original string based processing function which uses the HTML traversing methods from PyQuery
	to simplify the processing. """

	## Extract the webpage title, which contains the
	## away team, home team, and date
	title = webpage("div")("h1").eq(0).text()
	home_team, away_team, date = _title_process(title)

	## Loop over table objects in the main body of the webpage
	## and collect information from each
	tables = []
	titles = []
	for table in webpage("table").items():

		## Grab the table title
		titles.append(table("caption").text())

		## Use the header to extract the mapping between
		## column labels and column tags within the HTML. Lastly, we
		## correct the players columns to drop the disctinction between
		## starters and reserves.
		header = table("thead")("tr").eq(1)("th")
		columns = {c.attr("data-stat"):c.text() for c in header.items()}

		## Extract the data from the table body, replacing
		## blank entries with nans
		body = table("tbody")
		rows = {}
		replace = {"":np.nan}
		for row in body("tr").items():

			## Skip any subheadings
			if row.attr("class") == "thead":
				continue

			## Get the player name from the index
			player = row("th").text()
			
			## And the data from the remaining columns
			data = {entry.attr("data-stat"):replace.get(entry.text(),entry.text()) for entry in row("td").items()}

			## Store the row
			rows[player] = data

		## Construct a dataframe for this table and
		## drop players that didn't play
		df = pd.DataFrame(rows).T
		df.rename(columns=columns,inplace=True)
		if "reason" in df.columns:
			df = df.loc[df.reason.isnull()].drop(columns=["reason"])

		## Store the dataframe
		tables.append(df)

	## Finally put all the dataframes together by
	## a multistep concatenation/merger.
	away_df = pd.concat([tables[0],tables[1].drop(columns=["MP"])],axis=1,sort=False)
	home_df = pd.concat([tables[2],tables[3].drop(columns=["MP"])],axis=1,sort=False)

	## Add the relevant columns to each df and then
	## concatenate again and clean up.
	away_df["Team"] = len(away_df)*[away_team]
	home_df["Team"] = len(home_df)*[home_team]
	df = pd.concat([away_df,home_df],axis=0)
	df.index.rename("Player",inplace=True)
	
	return title, home_team, away_team, date, df

def _type_convert(df):

	""" Take the output from the webpage processing, which is a df filled with strings,
	and type convert appropriately. """

	## Type convert the numeric columns, ignoring the 
	## columns that don't obviously convert and explicitly
	## ignoring the minutes column, which needs some special care
	cols = [c for c in df.columns if c != "MP"]
	df[cols] = df[cols].apply(lambda x: pd.to_numeric(x,errors="ignore"))

	## Convert the minutes played column (MP) by force
	minutes = df.MP.apply(lambda s: s[:s.find(":")]).astype(int)
	seconds = df.MP.apply(lambda s: s[s.find(":")+1:]).astype(int)
	df["MP"] = minutes+seconds/60.

	return df


### Base object
######################################################################################
class BoxScore(object):

	""" Basic boxscore object, which encapsulates game information into a dataframe
	and some additional attributes. """

	def __init__(self, uri):

		""" uri = The relative link to the boxscore HTML page, such as "201806080CLE". Over time,
		I'll write functions to make this look up process a little easier. """

		## Store the uri and the URL for reference
		self._uri = uri
		self.url = BOXSCORE_URL.format(self._uri)

		## Retrieve the HTML text via pyquery 
		webpage = pq(self.url)

		## Process the HTML text to scrape the data and 
		## store some useful things.
		self.title, self.home_team, self.away_team, self.date, self.df = _process_webpage(webpage)

		## Convert data types in the dataframe
		self.df = _type_convert(self.df)

		## Add a date column to the dataframe
		self.df["date"] = len(self.df)*[self.date]

		## Compute the final score
		self.final_score = self.df.groupby("Team")["PTS"].sum()

	def __repr__(self):
		return self.title

if __name__ == "__main__":

	boxscore = BoxScore("201805190CLE")
	#boxscore = BoxScore("200212020PHO")
	print(boxscore)
	print(boxscore.final_score)
	print(boxscore.df)

