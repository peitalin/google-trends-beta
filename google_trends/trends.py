#!/usr/bin/python3
# encoding: latin-1

#############################################################
# Google Trends Query Utility
# Authors:
# Peita Lin (peita_lin@hotmail.com)
# Dan Garant (dgarant@cs.umass.edu)
# Updated 05/3/14
#
# Can be used with command-line invocation or as a call from another package.
# Non-standard dependencies: argparse, requests, arrow, fuzzywuzzy
#############################################################


from __future__     import print_function, absolute_import
from time           import sleep
import os, sys, csv, random, math
import requests, arrow, argparse

from google_auth    import authenticate_with_google
from google_class   import FormatException, QuotaException, KeywordData
from disambiguate   import disambiguate_keywords
from interpolate    import interpolate_ioi, conform_interest_over_time, change_in_ioi
from entity_types   import PRIMARY_TYPES, BACKUP_TYPES


PY3 = sys.version_info[0] == 3
DEFAULT_LOGIN_URL = "https://accounts.google.com.au/ServiceLogin"
DEFAULT_AUTH_URL = "https://accounts.{domain}/ServiceLoginAuth"
DEFAULT_TRENDS_URL = "http://www.{domain}/trends/trendsReport"
# okay to leave domain off here since it's a GET request, redirects are no problem
INTEREST_OVER_TIME_HEADER = "Interest over time"
EXPECTED_CONTENT_TYPE = "text/csv; charset=UTF-8"
NOW = arrow.utcnow()
BASEDIR = os.path.join(os.path.expanduser("~"), "Dropbox", "gtrends-beta")



def main():
	"""Parses arguments and initiates the trend querying process."""

	help_docs = {
		# Group 1: mutually exclusive arguments
		'--keywords': "A comma-separated list of phrases to query. Replaces --batch-input.",
		'--file': "filepath containing newline-separated trends query terms.",
		'--cik-file': "File with rows [cik|keyword|date]. Cik: is an arbitrary id number (filename). Input is a pipe delimited csv file.",
		# Group 2: mutually exclusive arguments
		'--quarterly': "Loops keyword through multiple quarters from a " \
						+ "-6 months and +18 months from a specific date",
		# General Arguments
		'--start-date': "Start date for the query in the form yyyy-mm",
		'--end-date': "End date for the query in the form yyyy-mm",
		'--output': "Directory to write CSV files to, otherwise writes results to std out.",
		'--username': "Username of Google account to use when querying trends.",
		'--password': "Password of Google account to use when querying trends.",
		'--login-url': "Address of Google's login service.",
		'--auth-url': "Authenticate URL: Address of Google's login service.",
		'--trends-url': "Address of Google's trends querying URL.",
		'--throttle': "Number of seconds to space out requests, this is to avoid rate limiting.",
		'--category': "Category for queries, e.g 0-7-107 for finance->investing. See categories.txt",
		'--ggplot': "Plots merged data series, requires ggplot"
	}


	command_line_args = (
		#[0]flag            [1]arg-name(dest)    [2]default
		# Group 1: mutually exclusive arguments
		('--keywords',      "keywords",          None),
		('--file',          "batch_input_path",  None),
		('--cik-file',      "cik_file",          None),
		# Group 2: mutually exclusive arguments
		('--quarterly',     "quarterly",         None),
		('--start-date',    "start_date",        NOW.replace(months=-2)),
		# General Arguments
		('--end-date',      "end_date",          NOW),
		('--output',        "output_path",       "terminal"),
		('--username',      "username",          None),
		('--password',      "password",          None),
		('--login-url',     "login_url",         DEFAULT_LOGIN_URL),
		('--auth-url',      "auth_url",          DEFAULT_AUTH_URL),
		('--trends-url',    "trends_url",        DEFAULT_TRENDS_URL),
		('--throttle',      "throttle",          0),
		('--category',      "category",          None),
		('--ggplot',        "ggplot",            None)
	)

	parser = argparse.ArgumentParser(prog="trends.py")
	# Mutually exclusive arguments
	arg_group1 = parser.add_mutually_exclusive_group()
	arg_group2 = parser.add_mutually_exclusive_group()

	[arg_group1.add_argument(A[0], help=help_docs[A[0]], dest=A[1], default=A[2])
		for A in command_line_args[:3]]

	[arg_group2.add_argument(A[0], help=help_docs[A[0]], dest=A[1], default=A[2])
		for A in command_line_args[3:5]]

	# General Arguments
	[parser.add_argument(A[0], help=help_docs[A[0]], dest=A[1], default=A[2])
		for A in command_line_args[5:]]


	def missing_args(args):
		"Make sure essential arguments are supplied."
		if not (args.password or args.username):
			sys.stderr.write("ERROR: Use --username and --password flags.\n")
			sys.exit(5)
		elif not (args.keywords or args.batch_input_path or args.cik_file):
			sys.stderr.write("ERROR: Use --keywords or --file, try --help for details.\n")
			sys.exit(5)
		elif args.quarterly and not args.start_date and not args.end_date:
			sys.stderr.write("ERROR: --quarterly requires a starting date." +
				" Try: --quarterly 2012-01 (day insensitive)")
		if args.cik_file and (args.start_date == NOW):
			print('Mixing --cik-file and --start-date, ignoring --start-date.')
		else:
			return None

	def csv_name(keyword, start_date=NOW.replace(months=-2), category=''):
		""" Converts keyword into filenames:
				'keyword_date_category_quarter.csv'
		If --cik-file is specified, filename becomes: cik.csv
		"""
		if isinstance(keyword, str):
			filename = keyword + " - "
			if args.category:
				filename += "[" + args.category + "] "
			elif args.quarterly:
				filename += args.quarterly
			else:
				filename += YYYY_MM(args.start_date).format("YYYY-MMM") \
						+ "~" + YYYY_MM(args.end_date).format("YYYY-MMM") + " full"
		elif isinstance(keyword, KeywordData):
			filename = keyword.cik
			if filename is None:
				filename = keyword.orig_keyword
		else:
			filename = keyword[0] # keyword: [cik, keyword, date]

		return filename.rstrip() + ".csv"

	def keyword_generator(keywords):
		"Shuffles keywords to avoid concurrent processes working on the same keyword."
		keywords = list(keywords)
		random.shuffle(keywords)
		for keyword in keywords:
			if os.path.exists(os.path.join(args.output_path, csv_name(keyword))):
				continue
			yield keyword

	def output_results(IO_out, kw):
		writer = csv.writer(IO_out)
		# Headers
		writer.writerow(["Date", kw.keyword, kw.desc, kw.title])
		# Write IoT Data
		[writer.writerow([str(s) for s in interest]) for interest in kw.interest]


	args = parser.parse_args()
	if not missing_args(args):
		if args.keywords: # Single input
			keywords = {k.strip() for k in args.keywords.split(",")}

		elif args.batch_input_path:
			with open(args.batch_input_path) as source:
				keywords = [l.strip() for l in source.readlines() if l.strip() != ""]
				keywords = [s.replace(',','') for s in keywords]

		elif args.cik_file:
			with open(args.cik_file) as source:
				keywords = [f.strip().split('|') for f in source.readlines()]
				try:
					assert all([len(k)==3 for k in keywords])
				except AssertionError:
					print('--cik-file: Bad format, try using pipe delimited (|) data.')
					sys.exit(1)

		if not PY3:
			try:
				keywords = [k.decode('latin-1') for k in keywords]
			except AttributeError:
				pass

	start_date = YYYY_MM(args.start_date)
	end_date   = YYYY_MM(args.end_date)
	trend_generator = get_trends(
						keyword_generator(keywords),
						trends_url=args.trends_url,
						quarterly=args.quarterly,
						start_date=start_date,
						end_date=end_date,
						username=args.username,
						password=args.password,
						throttle=args.throttle,
						category=args.category,
						ggplot=args.ggplot)


	for keyword_data in trend_generator:
		if args.output_path == "terminal":
			output_results(sys.stdout, keyword_data)
		else:
			if not os.path.exists(args.output_path):
				os.makedirs(args.output_path)

			output_filename = os.path.join(args.output_path, csv_name(keyword_data))

			with open(output_filename, 'w+') as f:
				output_results(f, keyword_data)

		if keyword_data.cik and keyword_data.querycounts:

			qpath = os.path.join(BASEDIR, 'cik-ipo/query_counts', args.category)
			if not os.path.exists(qpath):
				# print("Making dir: {}".format(qpath))
				os.makedirs(qpath)

			qcount_path = os.path.join(qpath, csv_name(keyword_data))
			with open(qcount_path, 'w+') as f:
				# print("Writing querycounts to: {}".format(qcount_path))
				writer = csv.writer(f)
				writer.writerow(['Missing Quarters, '+ args.category])
				[writer.writerow([str(q) for q in qcount]) for qcount in keyword_data.querycounts]

		else:
			raise(Exception("DEBUG: no keyword_data.cik or keyword_data.querycounts"))





def get_trends(keyword_gen, username=None, password=None,
			start_date=arrow.utcnow().replace(months=-2),
			end_date=arrow.utcnow(),
			throttle=1,
			quarterly=None,
			category=None,
			ggplot=None,
			trends_url=DEFAULT_TRENDS_URL,
			login_url=DEFAULT_LOGIN_URL,
			auth_url=DEFAULT_AUTH_URL,
			primary_types=PRIMARY_TYPES,
			backup_types=BACKUP_TYPES):
	""" Gets a collection of trends. Requires --keywords, --username and --password flags.

		Arguments:
			--keywords: The sequence of keywords to query trends on
			--trends_url: The address at which we can obtain trends
			--username: Username to provide when authenticating with Google
			--password: Password to provide when authenticating with Google
			--throttle: Number of seconds to wait between requests
			--categories: A category specification such as 0-7-37 for banking
			--start_date: The earliest records to include in the query
			--end_date: The oldest records to include in the query

		Returns a generator of KeywordData
	"""


	session, cookies, domain = authenticate_with_google(username, password,
													 login_url=login_url,
													 auth_url=auth_url)


	while True: # For each keyword:
		try:	# try to get correct keywords [KeywordData object(s)].
			keywords = disambiguate_keywords(keyword_gen, session, cookies,
											primary_types=primary_types,
											backup_types=backup_types)
		except StopIteration:
			break

		for keyword in keywords:
			print("="*60, "\n{k}: {c}".format(k=keyword.__unicode__(), c=category))
			if keyword.cik:
				print('cik:', keyword.cik, '\nfiling date: ', keyword.filing_date)


		# from IPython import embed; embed()
		fn_args = {'keywords': keywords, 'category':category, 'ggplot':ggplot,
				   'cookies': cookies, 'session': session,
				   'domain': domain, 'throttle': throttle }

		if quarterly:
			# Rolling quarterly period queries within start and end dates
			fn_args['filing_date'] = quarterly[:7]
			all_data = quarterly_queries(**fn_args)
		elif keywords[0].cik:
			# dates obtained from --cik-filing
			fn_args['filing_date'] = keywords[0].filing_date
			all_data = quarterly_queries(**fn_args)
			# querycounts: number of all-zero quarterly queries
		else:
			# Single keyword query
			fn_args['start_date'] = start_date
			fn_args['end_date'] = end_date
			all_data = single_query(**fn_args)
			# querycounts = None # for rolling queries only


		# from IPython import embed; embed()
		# assign (date, counts) to each KeywordData object
		for row in all_data[1:]:
			date, counts = parse_ioi_row(row)
			for i in range(len(keywords)):
				keywords[i].add_interest_data(date, counts[i])

		for kw in keywords:
			yield kw	# yield KeywordData objects



def _query_parameters(start_date, end_date, keywords, category):
	"Formats query parameters into a dictionary and passes to session.get()"

	days_in_month = 30 if start_date.month != 2 else 28
	# February bugfix, rounds number of months down by 1
	months = int(max((end_date - start_date).days, days_in_month)/days_in_month)
	# print('=> query_param months: {}' . format(months))
	# Sets number of months back for query
	params = {"export": 1, "content": 1}
	params["date"] = "{0} {1}m".format(start_date.strftime("%m/%Y"), months)
	# combine topics into a joint query -> q: query
	params["q"] = ", ".join([k.topic for k in keywords])
	if category:
		params["cat"] = category
	return params


def _get_response(url, params, cookies, session):
	"Calls GET and returns a list of the reponse data."
	response = session.get(url, params=params, cookies=cookies,
							 allow_redirects=True,
							 stream=True)

	if response.headers["content-type"] == 'text/csv; charset=UTF-8':
		if sys.version_info.major==3:
			return [x.decode('utf-8') for x in response.iter_lines()]
		else:
			return list(response.iter_lines())

	elif 'text/html' in response.headers["content-type"]:
		if "quota" in response.text.strip().lower():
			raise QuotaException("\n\nThe request quota has been reached. " +
					"This may be either the daily quota (~500 queries?) or the rate limiting quota. " +
					"Try adding the --throttle argument to avoid rate limiting problems.")

		elif "currently unavailable" in response.text.strip().lower():
			print('\n', response.text.strip())
			print("\nNo interest for this category--'currently unavailable' " +
				"\n==> content type: {}... returning 0\n\n".format(
					response.headers["content-type"]))

			qdate = params["date"].split(' ')[0]
			qdate = arrow.get(qdate, 'MM/YYYY').strftime('%b %Y')
			topic = params["q"].split(',')[0]
			return [topic, "Worldwide; " + qdate, ""]

		else:
			print('\n', response.text.strip().lower(), '\n')
			raise FormatException(("\n\nUnexpected content type {0}. " +
				"Maybe an invalid category or date was supplied".format(
					response.headers["content-type"])))
	else:
		from IPython import embed
		embed()


def _process_response(response_data):
	"Filters raw response.get data for dates and interest over time counts."
	try:
		start_row = response_data.index(INTEREST_OVER_TIME_HEADER)
	except (AttributeError, ValueError) as e:
		return response_data # handle in check_no_data()

	formatted_data = []
	for line in response_data[start_row+1:]:
		if line.strip() == "":
			break # reached end of interest over time
		else:
			formatted_data.append(line.strip().split(','))
	return formatted_data


def _check_data(keywords, formatted_data):
	"Check if query is empty. If so, format data accordingly."
	if 'Worldwide; ' in formatted_data[1] and formatted_data[2]=="":
		try:
			date = formatted_data[1][-8:]
			date = arrow.get(date, 'MMM YYYY')
			no_data = [date, 0]
		except:
			date = formatted_data[1][-4:]
			date = arrow.get(date, 'YYYY')
			no_data = [date, 0]
			pass
		print("Zero interest for '{0}'".format(keywords[0].title))
		return [no_data]
	else:
		return formatted_data[1:]


def quarterly_queries(keywords, category, cookies, session, domain, throttle, filing_date, ggplot, month_offset=[-9,18], trends_url=DEFAULT_TRENDS_URL):
	"""Gets interest data (quarterly) for the 9 months before and 18 months after specified date, then gets interest data for the whole period and merges this data.

		month_offset: [no. month back, no. months forward] to query
	Returns daily data over the period.
	"""

	aw_range = arrow.Arrow.range
	begin_period = arrow.get(filing_date, 'M-D-YYYY').replace(months=month_offset[0])
	ended_period = arrow.get(filing_date, 'M-D-YYYY').replace(months=month_offset[1])

	# Set up date ranges to iterate queries across
	start_range = aw_range('month', YYYY_MM(begin_period),
									YYYY_MM(ended_period))
	ended_range = aw_range('month', YYYY_MM(begin_period).replace(months=3),
									YYYY_MM(ended_period).replace(months=3))

	start_range = [r.datetime for r in start_range][::3]
	ended_range = [r.datetime for r in ended_range][::3]

	# Fix last date if incomplete quarter (offset -1 week from today)
	last_week = arrow.utcnow().replace(weeks=-1).datetime
	start_range = [d for d in start_range if d < last_week]
	ended_range = [d for d in ended_range if d < last_week]
	if len(ended_range) < len(start_range):
		ended_range += [last_week]

	# Iterate attention queries through each quarter
	all_data = []
	missing_queries = [] 	# use this to scale IoT later.
	for start, end in zip(start_range, ended_range):
		if start > last_week:
			break

		print("Querying period: {s} ~ {e}".format(s=start.date(),
												  e=end.date()))
		throttle_rate(throttle)

		response_args = {'url': trends_url.format(domain=domain),
						'params': _query_parameters(start, end, keywords, category),
						'cookies': cookies,
						'session': session}

		query_data = _check_data(keywords,
						_process_response(
							_get_response(**response_args)))

		if all([vals==0 for date,vals in query_data]):
			query_data = [[date, 0] for date in arrow.Arrow.range('month', start, end)]
			missing_queries.append(1)
		else:
			missing_queries.append(0)
		all_data.append(query_data)


	# Get overall long-term trend data across entire queried period
	s = begin_period.replace(weeks=-2).datetime
	e1 = arrow.get(ended_range[-1]).replace(months=+1).datetime
	e2 = arrow.utcnow().replace(weeks=-1).datetime
	e = min(e1,e2)
	print("\n=> Merging with overall period: {s} ~ {e}".format(s=s.date(), e=e.date()))

	response_args = {
		'url': trends_url.format(domain=domain),
		'params': _query_parameters(s, e, keywords, category),
		'cookies': cookies,
		'session': session
		}

	query_data = _check_data(keywords,
					_process_response(
						_get_response(**response_args)))

	if len(query_data) > 1:
		# compute changes in IoI (interest over time) per quarter
		# and merged quarters together after interpolating data
		# with daily data.
		# We cannot mix quarters as Google normalizes each query
		all_ioi_delta = []
		qdat_interp = []
		for quarter_data in all_data:
			if quarter_data != []:
				quarter_data = [x for x in quarter_data if x[1] != '']
				all_ioi_delta += list(zip(*change_in_ioi(*zip(*quarter_data))))

				if ggplot:
					qdat_interp += interpolate_ioi(*zip(*quarter_data))[1]
					# for plotting only

		qdate = [date for date, delta_ioi in all_ioi_delta]
		delta_ioi = [delta_ioi for date, delta_ioi in all_ioi_delta]
		ydate = [date[-10:] if len(date) > 10 else date for date,ioi in query_data]
		yIoI  = [float(ioi) for date,ioi in query_data]
		ydate, yIoI = interpolate_ioi(ydate, yIoI)

		# match quarterly and yearly dates and get correct delta IoI
		# common_date = [x for x in ydate+qdate if x in ydate and x in qdate]
		common_date = sorted(set(ydate) & set(qdate))

		delta_ioi = [delta_ioi for date,delta_ioi in zip(qdate, delta_ioi)
					if date in common_date]
		y_ioi = [y for x,y in zip(ydate, yIoI) if x in common_date]

		# calculate daily %change in IoI and adjust weekly values
		adj_IoI = [ioi*mult for ioi,mult in zip(y_ioi, delta_ioi)]

		adj_all_data = [[str(date.date()), round(ioi, 2)] for date,ioi in zip(common_date, adj_IoI)]
	else:
		# from IPython import embed; embed()
		adj_all_data = [[str(date.date()), int(zero)] for date, zero in zip(*interpolate_ioi(*zip(*sum(all_data,[]))))]

	from IPython import embed; embed()
	heading = ["Date", keywords[0].title]
	querycounts = list(zip((d.date() for d in start_range), missing_queries))
	keywords[0].querycounts = querycounts

	if not ggplot:
		return [heading] + adj_all_data

	## GGplot Only
	else:
		# GGPLOT MERGED GTRENDS PLOTS:
		import pandas as pd
		from ggplot import ggplot, geom_line, ggtitle, ggsave, scale_colour_manual, ylab, xlab, aes
		try:
			ydat = pd.DataFrame(list(zip(common_date, y_ioi)), columns=["Date", 'Weekly series'])
			mdat = pd.DataFrame(list(zip(common_date, adj_IoI)), columns=['Date', 'Merged series'])
			qdat = pd.DataFrame(list(zip(common_date, qdat_interp)), columns=['Date', 'Daily series'])
			ddat = ydat.merge(mdat, on='Date').merge(qdat,on='Date')
			ddat['Date'] = list(map(pd.to_datetime, ddat['Date']))

			ydat['Date'] = list(map(pd.to_datetime, ydat['Date']))
			mdat['Date'] = list(map(pd.to_datetime, mdat['Date']))
			qdat['Date'] = list(map(pd.to_datetime, qdat['Date']))
		except UnboundLocalError as e:
			raise(UnboundLocalError("No Interest-over-time to plot"))

		# meltkeys = ['Date','Weekly series','Merged series','Daily series']
		# melt = pd.melt(ddat[meltkeys], id_vars='Date')

		colors = [
				'#77bde0', # blue
				'#b47bc6',   # purple
				'#d55f5f'    # red
				]

		entity_type = keywords[0].desc

		g = ggplot(aes(x='Date', y='Daily series' ), data=ddat) + \
			geom_line(aes(x='Date', y='Daily series'), data=qdat, alpha=0.5, color=colors[0]) + \
			geom_line(aes(x='Date', y='Merged series'), data=mdat, alpha=0.9, color=colors[1]) + \
			geom_line(aes(x='Date', y='Weekly series'), data=ydat, alpha=0.5, color=colors[2], size=1.5) + \
			ggtitle("Interest over time for '{}' ({})".format(keywords[0].keyword, entity_type)) + \
			ylab("Interest Over Time") + xlab("Date")

		# from IPython import embed; embed()

		print(g)
		# ggsave(BASEDIR + "/iot_{}.png".format(keywords[0].keyword), width=15, height=5)
		return [heading] + adj_all_data





def single_query(keywords, category, cookies, session, domain, throttle,
			start_date, end_date, trends_url=DEFAULT_TRENDS_URL, ggplot=False):
	"Single period queries"

	try:
		response_args = {
			'url': trends_url.format(domain=domain),
			'params': _query_parameters(start_date, end_date, keywords, category),
			'cookies': cookies,
			'session': session
			}

		query_data = _check_data(keywords,
						_process_response(
							_get_response(**response_args)))

	except (FormatException, AttributeError, ValueError):
		query_data = [[arrow.get(str(x), 'YYYY'), 0] for x in range(2004,2015)]

	heading  = ["Date", keywords[0].title]
	query_data = [heading] + query_data

	return query_data





def parse_ioi_row(row):
	""" Formats a row of interest-over-time data (ioi).
		Arguments: row -- A list of strings

		Returns a 2-tuple (date, [counts1, counts2, ..., countsn])
		representing a date and associated counts for that date
	"""
	date, *counts = row
	if isinstance(date, str):
		date = arrow.get(date[:10]).date() # len>10 => date range (not yyyy-mm-dd format)
		# date = date.strftime('%Y-%m-%d')
	return (date, counts)


def throttle_rate(seconds):
	"""Throttles query speed in seconds. Try --throttle "random" (1~2 seconds)"""
	if str(seconds).isdigit() and seconds > 0:
		sleep(float(seconds))
	elif seconds=="random":
		sleep(float(random.randint(2,3)))


def YYYY_MM(date_obj):
	"""Removes day. Formats dates from YYYY-MM-DD to YYYY-MM. Also turns date objects into Arrow objects."""
	date_obj = arrow.get(date_obj)
	return arrow.get(date_obj.format("YYYY-MM"))





if __name__ == "__main__":
	main()
	print("="*60)
	print("OK. Done.")

