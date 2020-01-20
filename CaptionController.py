import json
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait as wait
import threading
from time import sleep

import Config
import Global
import Helper

class CaptionController():
    def __init__(self):
        self.browser = None
        self.waitThread = None
        self.isWaitOn = False
        self.isCapturingNow = False
        self.waitInterval = 1
        self.initVariables()
        pass

    def initVariables(self):
        self.curKey = ''
        self.curId = ''
        self.curUserName = ''
        self.curFrom = ''
        self.curTo = ''

    def waitTask(self):
        self.isWaitOn = True
        self.waitThread = threading.Thread(target=self.waitFunc)
        self.waitThread.start()

    def waitFunc(self):
        while self.isWaitOn:
            firstKey = None
            firstTask = None

            Global.todoSync.acquire()
            if len(Global.todoQueue) > 0:
                firstKey = next(iter(Global.todoQueue))
                firstTask = Global.todoQueue[firstKey]
            Global.todoSync.release()

            if firstKey != None and self.isCapturingNow == False:
                self.isCapturingNow = True
                self.curKey = firstKey
                self.curId = firstTask['id']
                self.curUserName = firstTask['user_name']
                self.curFrom = firstTask['from_date']
                self.curTo = firstTask['to_date']
                self.doCaption()
            sleep(self.waitInterval)

    def doCaption(self):
        try:
            Helper.Log('Starting caption... {0}, {1}, {2}'.format(self.curUserName, self.curFrom, self.curTo))
            self.runBrowser()
            if not self.twitterLogin():
                sleep(4)
            else:
                self.browser.get('https://twitter.com/search?q=from%3A{0}%20since%3A{1}%20until%3A{2}&src=typed_query&f=live'
                                 .format(self.curUserName, self.curFrom, self.curTo))

                tweet_ids = {}
                try:
                    # Wait until page is loaded
                    wait(self.browser, 10).until(EC.presence_of_element_located(
                                        (By.XPATH, '//a[@dir="auto" and @data-focusable="true" and @role="link"]')))
                    # '//section[@role="region" and @class="css-1dbjc4n"]'
                    Helper.Log('Capturing tweet ids...')

                    ######## Start extracting link ############
                    while True:
                        index = 0
                        appended_count = 0
                        link_tags = self.browser.find_elements_by_xpath(
                            '//a[@dir="auto" and @data-focusable="true" and @role="link"]')
                        # class="css-4rbku5 css-18t94o4 css-901oao r-1re7ezh r-1loqt21 r-1q142lx r-gwet1z r-a023e6 r-16dba41 r-ad9z0x r-bcqeeo r-3s2u2q r-qvutc0"
                        while index < len(link_tags):
                            a_tag = link_tags[index]
                            href_attribute = a_tag.get_attribute('href')
                            index += 1
                            if href_attribute in tweet_ids:
                                continue
                            tweet_ids[href_attribute] = href_attribute
                            appended_count += 1

                        self.browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                        Helper.Log('Scroll down to bottom...')
                        sleep(1)
                        if appended_count == 0:
                            break
                except Exception as e:
                    Helper.Log('Exception when capturing images {0}'.format(e))

                Helper.Log('Tweet ids captured {0}'.format(tweet_ids.keys()))
                ################## Making screenshots of tweets ###############
                index = 0
                images = []
                Helper.Log('Making screenshots of tweets...')
                for tweet_id in tweet_ids:
                    ims = Helper.makeTweetScreenshot(self.browser, tweet_id)
                    images.extend(ims)
                    index += 1
                    sleep(0.01)

                ################## Merge 4 images into one image ################
                Helper.Log('Merging each 4 screenshots into one image...')
                merged_images = Helper.mergeEach4Images(images)

                ################## Create pdf file #####################
                Helper.Log('Creating pdf file C:/xampp/htdocs/tweet/{0}.pdf ...'.format(self.curId))
                Helper.screenshots2Pdf(merged_images, 'C:/xampp/htdocs/tweet/{0}.pdf'.format(self.curId))
                Helper.Log('Created pdf file C:/xampp/htdocs/tweet/{0}.pdf ...'.format(self.curId))

                Global.doneSync.acquire()
                Global.doneQueue.append({'id': self.curId, 'pdf_name': self.curId + '.pdf'})
                Global.doneSync.release()

                Global.todoSync.acquire()
                Global.todoQueue.pop(self.curKey)
                Global.todoSync.release()
        except Exception as e:
            Helper.Log('Exception in doCaption function {0}'.format(str(e)))
            sleep(4)
        finally:
            if self.browser is not None:
                self.browser.quit()
            self.isCapturingNow = False
            self.initVariables()

    def runBrowser(self):
        chrome_options = webdriver.ChromeOptions()
        chrome_path = os.path.join(os.path.dirname(__file__), '../drivers', 'chromedriver')
        chrome_options.add_argument("--incognito")
        # chrome_options.add_argument("--headless")
        self.browser = webdriver.Chrome(executable_path=chrome_path, options=chrome_options)
        self.browser.get('https://twitter.com')

    def twitterLogin(self):
        try:
            Helper.Log('Loggin in twitter...')

            # Wait until login button is located
            wait(self.browser, 10).until(EC.presence_of_element_located(
                (By.CLASS_NAME, 'StaticLoggedOutHomePage-buttonLogin')))

            # Go to login step
            login_step_button = self.browser.find_element_by_class_name('StaticLoggedOutHomePage-buttonLogin')
            login_step_button.click()

            # Wait until username input is located
            wait(self.browser, 10).until(EC.presence_of_element_located(
                (By.XPATH, '//input[@class="js-username-field email-input js-initial-focus"]')))

            # Input login credential
            username_input = self.browser.find_element_by_xpath('//input[@class="js-username-field email-input js-initial-focus"]')
            password_input = self.browser.find_element_by_class_name('js-password-field')
            self.browser.execute_script("arguments[0].setAttribute('value','" + Config.twitter_username + "')", username_input)
            self.browser.execute_script("arguments[0].setAttribute('value','" + Config.twitter_password + "')", password_input)
            login_button = self.browser.find_element_by_css_selector('.submit.EdgeButton.EdgeButton--primary.EdgeButtom--medium')
            login_button.click()

            # Wait until home page is displayed
            wait(self.browser, 10).until(EC.presence_of_element_located(
                (By.XPATH, '//div[@data-testid="primaryColumn"]')))
            return True
        except Exception as e:
            Helper.Log('Exception in twitterLogin function {0}'.format(e))
            return False
