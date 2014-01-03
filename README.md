
## Gtrends-beta

Pulls investment banking queries and utilizes new word disambiguation features of Gtrends Beta.
Matches on financial firms, investment firms etc then by fuzzy string matching.

### INSTRUCTIONS:
pip install -r requirements.txt
- Requires a Google account
- The program skips queries/files that already exist in the output directory.
- The program READS the files in the input-file folder for keywords to query.
- input-files: ./input-files/*.txt


#### EXAMPLE COMMANDS TO EXECUTE
export GMAIL_USER="dgtesting12@gmail.com"
export base_dir="$HOME/Dropbox/gtrends-beta"


#####Single Keyword to stdout
    python $base_dir/google_trends/trends.py \
        --username $GMAIL_USER \
        --password justfortesting! \
        --keyword "Woori Investment Securities"  \
        --start-date 2012-01 --end-date 2013-01 \

    python ./google_trends/trends.py \
        --username $GMAIL_USER \
        --password justfortesting! \
        --keyword "Woori Investment Securities"  \
        --start-date 2012-01 --end-date 2013-01 \


#####Batch input from a text file
    python $base_dir/google_trends/trends.py \
        --username $GMAIL_USER \
        --password justfortesting! --throttle "random" \
        --file $base_dir/input-files/underwriter_set.txt  \
        --start-date 2013-01 --end-date 2013-6 \
        --category 0-7-107

#####Batch input/output to a set directory, names files according to date ranges and categories
    python $base_dir/google_trends/trends.py \
        --username $GMAIL_USER \
        --password justfortesting! --throttle "random"
        --file $base_dir/input-files/underwriter_set.txt  \
        --output $base_dir/underwriters/0-12-784-business-news \
        --category 0-7-784 \
        --start-date "2004-01" --end-date "2013-12" \

#####Disambiguation features: "BofA Merrill Lynch" -> Bank of America (Finance)
    python $base_dir/google_trends/trends.py \
        --username $GMAIL_USER \
        --password justfortesting! \
        --keyword "BofA Merrill Lynch" \
        --all-quarters "2013-01"   \
        --throttle "random" \
        --category 0-7

########
    python ./google_trends/trends.py \
        --username $GMAIL_USER \
        --password justfortesting! \
        --file $base_dir/input-files/underwriter_set.txt  \
        --all-quarters "2013-01"   \
        --category 0-7



#$#!#!#!#!#!#!#!#!
!#!#!#!#!# I SHOULD SPLIT ISSUERS BY YEAR BECAUSE THEY DONT EXIST IN PREVIOUS YEARS, WASTING QUERIES.
!#!#!#!#!# Find out how to append google context to output
######!#!#! up to 331 in issuers.txt


#### UNDERWRITERS
###### QUARTERLY + FULL QUERIES

export base_dir="$HOME/Dropbox/gtrends-beta"
export GMAIL_USER="dgtesting12@gmail.com"

#### 0-16-784: Business News
    python $base_dir/google_trends/trends.py \
        --username $GMAIL_USER \
        --password justfortesting! \
        --throttle "random" \
        --file $base_dir/input-files/underwriter_set.txt  \
        --output $base_dir/underwriter_set/0-12-784-business-news \
        --category 0-12-784 \
        --all-years "2004-01"


    python $base_dir/google_trends/trends.py \
        --username $GMAIL_USER \
        --password justfortesting! \
        --throttle "random" \
        --file $base_dir/input-files/underwriter_set.txt  \
        --output $base_dir/underwriter_set/0-12-784-business-news \
        --category 0-12-784 \
        --start-date "2004-01" --end-date "2013-12"



#### 0-7-37: Banking
    python $base_dir/google_trends/trends.py \
        --username $GMAIL_USER \
        --password justfortesting! \
        --throttle "random" \
        --file $base_dir/input-files/underwriter_set.txt  \
        --output $base_dir/underwriter_set/0-7-37-banking \
        --category 0-7-37 \
        --all-years "2004-01"

    python $base_dir/google_trends/trends.py \
        --username $GMAIL_USER \
        --password justfortesting! \
        --throttle "random" \
        --file $base_dir/input-files/underwriter_set.txt  \
        --output $base_dir/underwriter_set/0-7-37-banking \
        --category 0-7-37 \
        --start-date "2004-01" --end-date "2013-12"


#### 0-7: Finance
    python $base_dir/google_trends/trends.py \
        --username $GMAIL_USER \
        --password justfortesting! \
        --throttle "random" \
        --file $base_dir/input-files/underwriter_set.txt  \
        --output $base_dir/underwriter_set/0-7-finance \
        --category 0-7 \
        --all-years "2004-01"

    python $base_dir/google_trends/trends.py \
        --username $GMAIL_USER \
        --password justfortesting! \
        --throttle "random" \
        --file $base_dir/input-files/underwriter_set.txt  \
        --output $base_dir/underwriter_set/0-7-finance \
        --category 0-7 \
        --start-date "2004-01" --end-date "2013-12"






#####0: All categories

    0-12: Business & Industrial
        0-12-1138: Business Finance
            0-12-1138-1160: Commercial Lending
            0-12-1138-1139: Investment Banking
            0-12-1138-620: Risk Management
            0-12-1138-905: Venture Capital
        0-12-784: Business News
            0-12-784-1179: Company News
                0-12-784-1179-1240: Company Earnings
                0-12-784-1179-1241: Mergers & Acquisitions
            0-12-784-1164: Economy News
            0-12-784-1163: Financial Markets
            0-12-784-1165: Fiscal Policy News
    0-7: Finance
        0-7-278: Accounting & Auditing
            0-7-278-1341: Accounting & Financial Software
            0-7-278-1283: Tax Preparation & Planning
        0-7-37: Banking
        0-7-279: Credit & Lending
            0-7-279-468: Auto Financing
            0-7-279-813: College Financing
            0-7-279-811: Credit Cards
            0-7-279-812: Debt Management
            0-7-279-466: Home Financing
        0-7-814: Currencies & Foreign Exchange
        0-7-903: Financial Planning
        0-7-1282: Grants & Financial Assistance
            0-7-1282-813: College Financing
        0-7-38: Insurance
            0-7-38-467: Auto Insurance
            0-7-38-249: Health Insurance
            0-7-38-465: Home Insurance
        0-7-107: Investing
            0-7-107-904: Commodities & Futures Trading
        0-7-619: Retirement & Pension








#### IPO-CYCLES
###### QUARTERLY + FULL QUERIES

#### 0-16-784: Business News
    python google_trends/trends.py \
        --username dgtesting12 --password justfortesting! --throttle "random" \
        --file input-files/ipo-cycles.txt  \
        --output ipo-cycles/0-12-784-business-news \
        --category 0-12-784 \
        --all-quarters "2004-01" \

    python google_trends/trends.py \
        --username dgtesting12 --password justfortesting! --throttle "random" \
        --file input-files/ipo-cycles.txt  \
        --output ipo-cycles/0-12-784-business-news \
        --category 0-12-784 \
        --start-date "2004-01" --end-date "2013-12" \

#### 0-7-107: Investing
    python google_trends/trends.py \
        --username dgtesting12 --password justfortesting! --throttle "random" \
        --file input-files/ipo-cycles.txt  \
        --output ipo-cycles/0-7-107-investing \
        --category 0-7-107 \
        --all-quarters "2004-01" \

    python google_trends/trends.py \
        --username dgtesting12 --password justfortesting! --throttle "random" \
        --file input-files/ipo-cycles.txt  \
        --output ipo-cycles/0-7-107-investing \
        --category 0-7-107 \
        --start-date "2004-01" --end-date "2013-12" \

#### 0-7-37: Banking
    python google_trends/trends.py
        --username dgtesting12 --password justfortesting! --throttle "random" \
        --file input-files/ipo-cycles.txt  \
        --output ipo-cycles/0-7-37-banking \
        --category 0-7-37 \
        --all-quarters "2004-01" \

    python google_trends/trends.py
        --username dgtesting12 --password justfortesting! --throttle "random" \
        --file input-files/ipo-cycles.txt  \
        --output ipo-cycles/0-7-37-banking \
        --category 0-7-37 \
        --start-date "2004-01" --end-date "2013-12"
