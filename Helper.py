from datetime import datetime
import json
import os
import random
import requests
import shutil
import string
from fpdf import FPDF
from io import BytesIO
from PIL import Image
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait as wait
from time import sleep

import Config

from PdfHelper import PdfHelper

def Log(msg):
    now = datetime.now()
    print('{0} ===> {1}'.format(now.strftime('%Y-%m-%d 5H:5M:%S'), msg))
    pass

def randomString(stringLength=10):
    """Generate a random string of fixed length """
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for i in range(stringLength))

def dateStr2TwitterApiType(dateStr):
    return datetime.strptime(dateStr, '%Y-%m-%d %H:%M').strftime('%Y%m%d%H%M')

def getTweetsIds(username, fromDate, toDate):
    data = {
      'grant_type': 'client_credentials'
    }

    response = requests.post(Config.twitter_token_url, data=data,
                             auth=(Config.twitter_api_key, Config.twitter_api_secret_key))

    result_as_json = json.loads(response.text)
    token = '{0} {1}'.format(result_as_json['token_type'], result_as_json['access_token'])

    headers = {
        'authorization': token,
        'content-type': 'application/json',
    }

    data = '{ "query":"from:' + username + '",  "maxResults": "100", "fromDate":"' \
           + dateStr2TwitterApiType(fromDate + ' 00:00') + '", "toDate":"' \
           + dateStr2TwitterApiType(toDate + ' 23:59') + '" }'

    response = requests.post(Config.twitter_search_url, headers=headers, data=data)

    result_as_json = json.loads(response.text)
    tweets = result_as_json['results']

    tweet_ids = []
    index = 0
    while index < len(tweets):
        tweet_ids.append(tweets[index]['id_str'])
        index += 1

    return tweet_ids

def element2Image(browser, element):
    location = element.location
    size = element.size
    png = browser.get_screenshot_as_png()  # saves screenshot of entire page
    im = Image.open(BytesIO(png))  # uses PIL library to open image in memory

    left = location['x']
    top = location['y']
    right = location['x'] + size['width']
    bottom = location['y'] + size['height']

    im = im.crop((left, top, right, bottom))  # defines crop points
    return im

def getExtraImagesFromTweet(baseurl, element):
    extra_images = []
    a_tags = element.find_elements_by_xpath('.//a[@aria-haspopup="false" and @role="link" and @data-focusable="true"]')
    for a_tag in a_tags:
        href = a_tag.get_attribute('href')
        if baseurl in href:
            img_tag = a_tag.find_element_by_xpath('.//img[@draggable="true"]')
            img_src = img_tag.get_attribute('src')
            resp = requests.get(img_src)
            img = Image.open(BytesIO(resp.content))
            extra_images.append(img)
    return extra_images

def makeTweetScreenshot(browser, url):
    images = []
    try:
        browser.get(url)
        # Wait until page is loaded
        wait(browser, 10).until(EC.presence_of_element_located(
            (By.XPATH, '//div[@data-testid="primaryColumn"]')))
        wait(browser, 10).until(EC.presence_of_element_located(
            (By.XPATH, '//article[@aria-haspopup="false" and @role="article"]')))

        # Wait a few for the contents loading correctly
        sleep(0.5)
        # Start screenshot
        primary_column = browser.find_element_by_xpath('//div[@data-testid="primaryColumn"]')
        articles = primary_column.find_elements_by_xpath('.//article[@aria-haspopup="false" and @role="article"]')
        if len(articles) > 0:
            parent_of_articles = articles[0].find_element_by_xpath('..').find_element_by_xpath('..').find_element_by_xpath('..')
            images.append(element2Image(browser, parent_of_articles))
            extra_images = getExtraImagesFromTweet(url, parent_of_articles)
            images.extend(extra_images)

    except Exception as e:
        Log('Exception in makeTweetScreenshot function {0}'.format(e))
    return images


def mergeEach4Images(images):
    merged_images = []
    for index in range(0, len(images), 4):
        im_1 = images[index]
        im_2 = None
        im_3 = None
        im_4 = None
        if index >= len(images) - 1:
            im_2 = im_1
            im_3 = im_1
            im_4 = im_1
        elif index >= len(images) - 2:
            im_2 = images[index + 1]
            im_3 = im_2
            im_4 = im_2
        elif index >= len(images) - 3:
            im_2 = images[index + 1]
            im_3 = images[index + 2]
            im_4 = im_3
        else:
            im_2 = images[index + 1]
            im_3 = images[index + 2]
            im_4 = images[index + 3]

        width_1, height_1 = im_1.size
        width_2, height_2 = im_2.size
        width_3, height_3 = im_3.size
        width_4, height_4 = im_4.size

        hgap = 80
        ygap = 60
        common_width = max(width_1, width_2, width_3, width_4)
        common_height = int(max(height_1 * width_1 / common_width, height_2 * width_2 / common_width,
                                    height_3 * width_3 / common_width, height_4 * width_4 / common_width))

        # Scale image to fit space
        max_size = (common_width, common_height)
        im_1.thumbnail(max_size, Image.ANTIALIAS)
        im_2.thumbnail(max_size, Image.ANTIALIAS)
        im_3.thumbnail(max_size, Image.ANTIALIAS)
        im_4.thumbnail(max_size, Image.ANTIALIAS)

        total_width = 2 * common_width + hgap
        total_height = 2 * common_height + ygap

        new_im = Image.new('RGBA', (total_width, total_height), (255, 255, 255, 0))

        x_offset = 0
        y_offset = 0

        new_im.paste(im_1, (x_offset, y_offset))
        x_offset += common_width + hgap

        if index < len(images) - 1:
            new_im.paste(im_2, (x_offset, y_offset))
            x_offset = 0
            y_offset += common_height + ygap

        if index < len(images) - 2:
            new_im.paste(im_3, (x_offset, y_offset))
            x_offset += common_width + hgap

        if index < len(images) - 3:
            new_im.paste(im_4, (x_offset, y_offset))

        merged_images.append(new_im)
    return merged_images

def screenshots2Pdf(images, pdf_path):
    # Save images to temp path
    fileNames = []
    for image in images:
        tempName = './temp/{0}.png'.format(randomString(20))
        image.save(tempName)
        fileNames.append(tempName)

    pdf = FPDF(orientation='P', unit='mm', format=(210, 297))
    helper = PdfHelper()
    for fileName in fileNames:
        pdf.add_page('P')
        helper.centreImage(pdf, fileName)

    pdf.output(pdf_path, "F")
    for fileName in fileNames:
        try:
            if os.path.exists(fileName):
                os.remove(fileName)
        except Exception as e:
            Log('Exception in screenshots2Pdf function {0}'.format(e))
