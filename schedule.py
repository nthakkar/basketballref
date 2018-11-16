""" schedule.py

Functionality to retrieve season schedules from basketball-reference.com 
HTML queries. """
import numpy as np
import pandas as pd
from pyquery import PyQuery as pq

## For 404 errors
from urllib.error import HTTPError

## Base URL for queries and month options for the season (in order).
SCHEDULE_URL = "https://www.basketball-reference.com/leagues/NBA_{0:d}_games-{1:s}.html"

## Useful global utilities
all_months = ("october","november","december","january","february","march","april","may","june")

### String processing functions and regular expresions
######################################################################################
def _process_webpage(webpage):

	""" Process PQ object webpage to extract the schedule table with the game URI included
	so that the table can be used to easily look up box scores. """

	## Extract the page's table from the main
	## body of the webpage.
	table = webpage("table")

	## Get the rows from the table body
	body = table("tbody")
	#print(body)
	rows = []
	for row in body("tr").items(): 

		## Get all the columns
		this_row = {entry.attr("data-stat"):entry.text() for entry in row("td").items()}

		## Get the date and URI from the index
		this_row["date"] = row("th").eq(0).text()
		this_row["uri"] = row("th").eq(0).attr("csk")

		## Store the row as long as the date
		## isn't the playoffs line (which intersects the
		## tables in April).
		if this_row["date"] == "Playoffs":
			continue
		rows.append(this_row)

	## Make a dataframe, keeping specific columns
	## and renaming them to specific preferences.
	df = pd.DataFrame(rows)
	df = df[["date","visitor_team_name","home_team_name","home_pts","visitor_pts","attendance","uri"]]
	df.columns = ["date","away","home","home_PTS","away_PTS","attendance","uri"]

	return df

### Work-horse class
######################################################################################
class SeasonSchedule(object):

	""" Basic object for the schedule dataframe and meta-data from a particular season. """

	def __init__(self,season,months=all_months):
		
		""" This function encapsulates the queary and processing to turn the table on
		bball-ref.com (see schedule URL above) into a pandas df. 

		season: int, year of the january in the season (i.e. season that starts October 2017 is the
		2018 season since it goes till June 2018).
		months: option iterable containing strings of months of the season to retrieve (since the pages are
		monthly on the website)."""

		## Store the meta data.
		self.season = season
		self.months = months

		## Loop over months to retrieve individual dataframes
		dfs = []
		for month in self.months:

			## Get the webpage text via PyQuery
			## This is done with an exception catch to get shortened seasons
			## like the 2011-12 season.
			try:
				webpage = pq(SCHEDULE_URL.format(self.season,month.lower()))
			except HTTPError:
				continue

			## Extract the table as a dataframe
			df = _process_webpage(webpage)

			## Add this month's to the total
			dfs.append(df)

		## Create the full df
		self.df = pd.concat(dfs,axis=0,ignore_index=True)

		## Change the date series to datetime
		self.df["date"] = pd.to_datetime(self.df["date"])
		
		## And the title string
		self.name = "{}-{} season schedule".format(season-1,season)

	def __repr__(self):
		return self.name


if __name__ == "__main__":

	schedule = SeasonSchedule(1988)
	print(schedule)
	print(schedule.df)
