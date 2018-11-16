"""roster.py

Methods to scrape active roster information from team pages on 
basketball-ref.com. """
import numpy as np
import pandas as pd
from pyquery import PyQuery as pq

## Base URL for queries
ROSTER_URL = "https://www.basketball-reference.com/teams/{0:s}/{1:d}.html"

### String processing functions and regular expresions
######################################################################################
def _process_webpage(webpage):

	""" HTML processing function for the PQ webpage object. This is a refactor of the 
	original string based processing function which uses the HTML traversing methods from PyQuery
	to simplify the processing. """

	## Get the description string for the page (done here
	## in kind of a janky way).
	header = webpage.text()
	header = header[:header.find("\nMore Team Info")]
	header = header[header.find("About logos")+len("About logos\n"):]

	## Process the table into a dataframe
	table = webpage("table")

	## Extract the data from the table body, replacing
	## blank entries with nans
	body = table("tbody")
	rows = []
	replace = {"":np.nan}
	for row in body("tr").items():

		## Get the player number
		number = row("th").text()
		number = replace.get(number,number)

		## Get the player name
		name = row("td").eq(0).text()

		## Get the player's bball ref URI
		uri = row("td").eq(0)("a").attr("href")
		uri = uri[uri.rfind("/")+1:uri.find(".")]
	
		## Store this row
		rows.append([number,name,uri])

	## Construct a dataframe for this table
	df = pd.DataFrame(rows,columns=["number","player","uri"])

	## Process the column types and handle
	## duplicate rows (which appear sometimes)
	df = df.apply(lambda x: pd.to_numeric(x,errors="ignore"))
	df = df.drop_duplicates()
	
	return header, df

### Base object
######################################################################################
class Roster(object):

	"""Basic roster object, which encapsulates some basic team information and a dataframe
	with the roster for a given season."""

	def __init__(self,team,season,dropna=False):

		""" team = 3 letter team abrieviation, which can be found in a number of places (e.g. box scores). 
		season is an integer for the year of the allstar weekend in a give season."""

		## Store the team, year, and the URL for reference
		self._team = team
		self._season = season
		self.url = ROSTER_URL.format(self._team,self._season)

		## Retrieve the HTML text via pyquery 
		webpage = pq(self.url)

		## Process the webpage to extract the roster table
		self.description, self.df = _process_webpage(webpage)

		## Drop na in the dataframe if specified
		if dropna:
			self.df = self.df.dropna()

	def __repr__(self):
		return self.description


if __name__ == "__main__":

	r = Roster("PHO",2019)
	#r = Roster("LAL",2019)
	#r = Roster("CHI",2018)
	print(r)
	print(r.df)
