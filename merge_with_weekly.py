

import shutil as sh
import glob

names = [
"./Advest",
"./Anderson & Strudwick",
"./Brean Murray",
"./Burnham Securities",
"./C & Co Corporate",
"./CL King & Associates",
"./CRT Capital Group",
"./Casimir Capital",
"./Chardan Capital Markets",
"./Clarkson Capital Markets",
"./Dahlman Rose",
"./FIG Partners",
"./Feltl & Company",
"./Ferris Baker Watts",
"./Gilford Securities",
"./Global Hunter Securities",
"./GunnAllen Financial",
"./Home Credit & Finance Bank",
"./JMP Securities",
"./Jefferies Broadview",
"./Jesup & Lamont Securities",
"./KKR & Co",
"./Keefe Bruyette & Woods",
"./Ladenburg Thalmann",
"./Merriman Curhan Ford",
"./Needham & Company",
"./Pacific Crest Securities",
"./Pali Capital",
"./Panmure Gordon",
"./PrinceRidge",
"./Sanders Morris Harris",
"./Sterne Agee & Leach",
"./Stifel Nicolaus",
"./Sunrise Securities",
"./ThinkEquity",
"./WR Hambrecht + Co",
"./WestPark Capital",
"./William Blair & Company",
"./Woori Investment & Securities",
"./Wunderlich Securities"
]



ddir = '/home/peita/Dropbox/gtrends-beta/underwriter_set/0-all'
files = glob.glob(ddir + '/*.csv')
srcfiles = [x for x in files if not any(name in x for name in names)]
dest = [ddir + "./yearly/" + x.replace("./",'') for x in srcfiles]



base_dir = './underwriter_set/0-all'
# Because iterated data is not scaled properly, we need to combine with full query
# this allows daily data acoss the entire 2004-2014 period
iter_dats = glob.glob(base_dir + '/*.csv') # iteratated queries
# full_dat = full query
full_dats = [base_dir + '/full/' + x.replace('./','') + ' - 2004-Jan~2013-Dec full.csv' for x in names]


# for i, f in zip(iter_dats, full_dats):
# 	idat = pd.read_csv(i)
# 	fdat = pd.read_csv(f)
# 	idat["Date"] = list(map(lambda x: arrow.get(x), idat["Date"]))
# 	fdat["Date"] = list(map(lambda x: arrow.get(x), fdat["Date"]))


idat = pd.read_csv(iter_dats[0])
fdat = pd.read_csv(full_dats[0])


def trends(df):
	return df[df.keys()[1]]


def pct_trends(df):
	"Apply to iterated queries only"
	return df[df.keys()[1]].pct_change().fillna(0) + 1


import matplotlib.pyplot as plt


### Put in thesis data section.
plt.plot(trends(idat), label="iterated queries")
plt.plot(trends(fdat), label="full queries")
plt.legend()




yearly=True
import arrow

start="2004-01"
end="2014-01"

if yearly:
    date_range = arrow.Arrow.range('year', arrow.get(start), arrow.get(end))
if quarterly:
    date_range = arrow.Arrow.range('month', arrow.get(start), arrow.get(end))
    date_range = [r.datetime for r in date_range][::3][1:]


idat["Date"] = list(map(lambda x: arrow.get(x), idat["Date"]))

adj_idat = [idat[(idat.Date >= s) & (idat.Date < e)] for s,e in zip(date_range[:-1], date_range[1:])]
adj_fdat = [fdat[(fdat.Date >= s) & (fdat.Date < e)] for s,e in zip(date_range[:-1], date_range[1:])]


for i,f in zip(adj_idat, adj_fdat):
	if len(i) > len(f):
		print(1)


##HOW TO DEAL WITH INF
