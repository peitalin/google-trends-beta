# /usr/bin/python3


import os

# python ~/Dropbox/gtrends-beta/gtrends_ioi.py


cat_codes = ['0-7', '0-7-107', '0-12-784', '0', '0-12']
categories = ['finance' , 'investing', 'business-news', 'all', 'business_industrial']

# 0-7 -> finance
# 0-7-107 -> investing
# 0-12-784 -> business-news
# 0-7-37 -> banking
# 0 -> all
# 0-12-1138-1139 -> investment-banking
# 0-12: Business & Industrial


categories = list(zip(cat_codes, categories))


for ccode, category in categories:
    # Firms names
    syscall = """python3 $base_dir/google_trends/trends.py \
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





######################################################

"""
    python3 $base_dir/google_trends/trends.py \
        --username $GMAIL_USER \
        --password justfortesting! \
        --category 0 \
        --ipo-quarters "2013-12" \
        --keyword "SolarCity"
"""


"""python3 $base_dir/google_trends/trends.py \
        --username dgtesting12@gmail.com \
        --password justfortesting! \
        --throttle "random" \
        --quiet-io "true" \
        --cik-file $base_dir/ipo-uw/ipo-uw.csv  \
        --output $base_dir/ipo-uw2/all \
        --category 0"""






def selenium_reset_IP():
    """Emulates browser login with selenium bindings to phantom.js.
    Gives you SID (Google User ID) cookies."""

    from selenium import webdriver

    driver = webdriver.PhantomJS()
    # driver = webdriver.Firefox()
    driver.get('http://10.0.0.138/')
    driver.find_elements_by_xpath("//td/input")[0].click()
    driver.find_elements_by_xpath("//td/input")[0].click()

