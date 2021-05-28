
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
import csv
import datetime


# TODO: main function to initialize script with driver selection CBB v UNTAPPD
# the driver selected should drive which part of the code executes
# TODO: functions to run the appropriate driver code 

DRIVER_PATH = 'chromedriver'
driver_selection = input('Select a driver: cbb or untappd')

if driver_selection == 'cbb':
    cbb_driver = webdriver.Chrome(executable_path=DRIVER_PATH)
untappd_driver = webdriver.Chrome(executable_path=DRIVER_PATH)
all_beers ='https://untappd.com/beer/top_rated?country=united-states'
untappd_driver.get(all_beers)
untappd_main_window = untappd_driver.current_window_handle
results = 1
pages = 0
cbb_driver.get(f'https://beerandbrewing.com/beer-reviews?q=&hPP={results}&idx=cbb_web_review_search&p={pages}')

cbb_main_reviews_window = cbb_driver.current_window_handle

# Functions to handle data processing for Craft Beer & Brewing driver
def get_item_text(item):
    return item.text or ''

def parse_review_meta(review_meta):
    meta_keys = ['Style', 'ABV', 'IBU']
    meta_items = []

    for i in review_meta:
        if get_item_text(i) is not None and get_item_text(i) != '':
            if 'Style' in get_item_text(i):
                item = get_item_text(i).split(': ')
            else:
                item = get_item_text(i).replace(':','').split()
            meta_items.append(item)

    for i in meta_items:
        if 'Style' not in i:
            first_pair = ' '.join(i[:2])
            second_pair = ' '.join(i[-2:])
        else:
            first_pair = None
            second_pair = None

    transformed_meta_items = [i for i in meta_items if 'Style' in i]
    if first_pair is not None:
        transformed_meta_items.append(first_pair.split())
    if second_pair is not None:
        transformed_meta_items.append(second_pair.split())

    meta_items_dict = {x: y.strip() for x, y in transformed_meta_items}
    return tuple([meta_items_dict.get(key, None) for key in meta_keys])

def parse_scores(scores):
    split_scores = scores.split()
    score = split_scores[0].split('/')[0]
    aroma = split_scores[2]
    appearance = split_scores[4]
    flavor = split_scores[6]
    mouthfeel = split_scores[8]
    return score, aroma, appearance, flavor, mouthfeel

def parse_reviews(reviews):
    total_review = []
    for review in reviews:
        review_text = get_item_text(review)
        if 'Print Shelf Talker' not in review_text and 'How We Review' not in review_text:
            total_review.append(review_text.strip('\"').strip('\n'))
    return ' '.join(total_review)

beer_styles = [get_item_text(i).split('\n') for i in cbb_driver.find_elements_by_class_name('ais-refinement-list')][0]

beer_hits = cbb_driver.find_elements_by_class_name('hit-content')
tabs = []
cbb_beers_data = []

for hits in beer_hits:
    for beer in hits.find_elements_by_tag_name('a'):
        beer.send_keys(Keys.CONTROL + Keys.RETURN)
        tabs.append(cbb_driver.window_handles[-1])

for tab in tabs:
    cbb_driver.switch_to.window(tab)

    review_meta = cbb_driver.find_element_by_class_name('review-meta-holder').find_elements_by_tag_name('p')
    style, abv, ibu = parse_review_meta(review_meta)

    scores = cbb_driver.find_element_by_class_name('main-score-overall-container').text
    score, aroma, appearance, flavor, mouthfeel = parse_scores(scores)

    beer = cbb_driver.find_element_by_id('article-body').find_element_by_tag_name('h1').text

    reviews = cbb_driver.find_element_by_id('article-body').find_elements_by_tag_name('p')
    total_review = parse_reviews(reviews)

    beer_data = {
                'beer': beer,
                'style': style,
                'abv': abv,
                'ibu': ibu,
                'total_score': score,
                 'aroma_score': aroma,
                 'appearance_score': appearance,
                 'flavor_score': flavor,
                 'mouthfeel_score': mouthfeel,
                'total_review': total_review
                }
    cbb_beers_data.append(beer_data)

today = datetime.datetime.today()
now = str(today).replace(' ','_').replace(':','')

# TODO: elegantly handle encoding
keys = cbb_beers_data[0].keys()
with open(f'beer_data_scrape_{now}.csv', 'w', newline='',encoding='UTF-8')  as output_file:
    dict_writer = csv.DictWriter(output_file, keys)
    dict_writer.writeheader()
    dict_writer.writerows(cbb_beers_data)

cbb_driver.quit()

untappd_driver.switch_to.window(untappd_main_window)


# In[181]:


# Get the beer details for all beers then open each beer onto a new tab
beer_details = untappd_driver.find_elements_by_class_name('beer-details')
beer_tabs = []
for detail in beer_details:
    link = detail.find_element_by_tag_name('a')
    link.send_keys(Keys.CONTROL + Keys.RETURN)
    beer_tabs.append(untappd_driver.window_handles[-1])


# In[182]:


# For each beer tab go get all the data
beer_data = []
for tab in beer_tabs:
    untappd_driver.switch_to.window(tab)

    beer_elements = untappd_driver.find_element_by_class_name('content')
    beer = beer_elements.find_element_by_tag_name('h1').text
    score = beer_elements.find_element_by_class_name('num').text.replace('(','').replace(')','')
    bid = beer_elements.find_element_by_class_name('label').get_attribute('href').split('/')[-1]

    dict_data = {
                'bid': bid,
                'beer': beer,
                'score': score
                }

    p_tags = beer_elements.find_elements_by_tag_name('p')
    p_tags_list = []
    for tag in p_tags:
        tag_value = tag.text
        tag_attribute = tag.get_attribute('class')
        p_tags_list.append({tag_attribute:tag_value})

    for dicts in p_tags_list:
        for k,v in dicts.items():
            if k:
                dict_data[k] = v

    untappd_driver.find_element_by_css_selector('div.beer-descrption-read-more').click()
    description = untappd_driver.find_element_by_class_name('beer-descrption-read-less').text

    dict_data['description'] = description

    beer_data.append(dict_data)


# In[188]:


def get_beer_data():
    beer_elements = untappd_driver.find_element_by_class_name('content')
    beer = beer_elements.find_element_by_tag_name('h1').text
    score = beer_elements.find_element_by_class_name('num').text.replace('(','').replace(')','')
    bid = beer_elements.find_element_by_class_name('label').get_attribute('href').split('/')[-1]

    dict_data = {
                'bid': bid,
                'beer': beer,
                'score': score
                }

    p_tags = beer_elements.find_elements_by_tag_name('p')
    p_tags_list = []
    for tag in p_tags:
        tag_value = tag.text
        tag_attribute = tag.get_attribute('class')
        p_tags_list.append({tag_attribute:tag_value})

    for dicts in p_tags_list:
        for k,v in dicts.items():
            if k:
                dict_data[k] = v

    try:
        untappd_driver.find_element_by_css_selector('div.beer-descrption-read-more').click()
        description = untappd_driver.find_element_by_class_name('beer-descrption-read-less').text
    except:
        description = ''

    dict_data['description'] = description

    return dict_data


# In[191]:


untappd_driver.switch_to.window(untappd_main_window)
beer_details = untappd_driver.find_elements_by_class_name('beer-details')
beer_data = []
for detail in beer_details:
    beer_page_link = detail.find_element_by_tag_name('a')
    beer_page_link.send_keys(Keys.CONTROL + Keys.RETURN)

    new_beer_tab = untappd_driver.window_handles[-1]
    untappd_driver.switch_to.window(new_beer_tab)

    dict_data = get_beer_data()
    beer_data.append(dict_data)

    untappd_driver.close()

    untappd_driver.switch_to.window(untappd_main_window)

untappd_driver.quit()


# In[205]:


today = datetime.datetime.today()
now = str(today).replace(' ','_').replace(':','')

# TODO: elegantly handle encoding
keys = beer_data[10].keys()
with open(f'untappd_beer_data_scrape_{now}.csv', 'w', newline='', encoding='UTF-8')  as output_file:
    dict_writer = csv.DictWriter(output_file, keys)
    dict_writer.writeheader()
    dict_writer.writerows(beer_data)


# In[183]:


untappd_driver.quit()
