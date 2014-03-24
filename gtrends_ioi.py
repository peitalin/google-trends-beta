# /usr/bin/python3


import os
from random import shuffle

# python ~/Dropbox/gtrends-beta/gtrends_ioi.py


cat_codes = ['0-7', '0-7-107', '0-12-784', '0']
categories = ['finance' , 'investing', 'business-news', 'all']

# 0-7-finance
# 0-7-107-investing
# 0-12-784-business-news
# 0-7-37-banking
# 0-all
# 0-12-1138-1139-investment-banking


categories = list(zip(cat_codes, categories))
# shuffle(categories)


for ccode, category in categories:
    ## Firms names
    syscall = """python $base_dir/google_trends/trends.py \
        --username $GMAIL_USER \
        --password justfortesting! \
        --throttle "random" \
        --quiet-io "true" \
        --cik-file $base_dir/cik-ipo/cik-ipos.csv  \
        --output $base_dir/cik-ipo/{category} \
        --category {ccode}""".format(category=category, ccode=ccode)
    os.system(syscall)


# for ccode, category in categories:
#     # Underwriters
#     syscall = """python $base_dir/google_trends/trends.py \
#         --username $GMAIL_USER \
#         --password justfortesting! \
#         --throttle "random" \
#         --quiet-io "true" \
#         --cik-file $base_dir/ipo-uw/ipo-uw.csv  \
#         --output $base_dir/ipo-uw/{category} \
#         --category {ccode}""".format(category=category, ccode=ccode)
#     os.system(syscall)


"""
    python3 $base_dir/google_trends/trends.py \
        --username $GMAIL_USER \
        --password justfortesting! \
        --category 0 \
        --ipo-quarters "2011-07" \
        --keyword "Bankrate Inc" \
"""