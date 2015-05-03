
## Google Trends Beta

This script pulls 'interest-over-time' queries from Google Trends and uses the entity disambiguation features introduced in Google Trends Beta. Matches on specified entity types and category.


The program inputs the original search term and disambiguates between various
entity types, then returns the correct company/corporate type matched by phrase similarity. In case there are multiple company types (e.g. Wachovia Securities, Wachovia Group). Default entity types are firms and investment banks.

![alt tag](https://raw.githubusercontent.com/peitalin/gtrends-beta/master/input-files/iot_gif.gif)




### INSTRUCTIONS:
pip install -r requirements.txt

Requires:
- Google account


#### EXAMPLE COMMANDS
    export GMAIL_USER="username@gmail.com"
    export base_dir="$HOME/gtrends-beta"


#####Single keyword to std out

    python3 $base_dir/google_trends/trends.py \
        --username $GMAIL_USER \
        --password justfortesting! \
        --keyword "Tesla"  \
        --start-date 2012-03 --end-date 2012-06


######Disambiguation features:
This query returns "Tesla Motors" queries rather than "Nikola Tesla" or "tesla coils" for example.

To get different entity types, define entity types in __entity_types.py__. Currently filters for companies and investment banking firms.


#####Category filters: JP Morgan -> Category 0-7 (Finance)

    python3 $base_dir/google_trends/trends.py \
        --username $GMAIL_USER \
        --password justfortesting! \
        --keyword "JP Morgan" \
        --category 0-7



##### Merged daily + monthly series

    python3 $base_dir/google_trends/trends.py \
        --username $GMAIL_USER \
        --password justfortesting! \
        --quarterly "2012-05" \
        --keyword "Facebook" \
        --category 0-7


![alt tag](https://raw.githubusercontent.com/peitalin/gtrends-beta/master/input-files/merged_Facebook2.png)

This iterates quarterly queries (for daily data) then merges with long term trends data through interpolation (log10 changes in daily interest).


##### Quarterly queries -12 +12 months around a date.

    python3 $base_dir/google_trends/trends.py \
        --username $GMAIL_USER \
        --password justfortesting! \
        --quarterly "2014-05" \
        --keyword "Alibaba" \
        --category 0-12



__Data Format__:
Date, Entity Name, Entity Type, Original Search Term


##### Example Categories

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


### License

Copyright (C) 2014 P. Lin, D. Garant

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.
