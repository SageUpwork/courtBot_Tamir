#!/usr/bin/env python
# -*- coding: ascii -*-

# ------------------------------------------------------------
import logging
import json
import multiprocessing
import os
import time
import platform
from concurrent.futures import ThreadPoolExecutor
from random import randint

import pandas as pd
import requests
from bs4 import BeautifulSoup
# from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.firefox.options import Options
from xvfbwrapper import Xvfb

def loggerInit(logFileName):
    try:
        os.makedirs("logs")
    except:
        pass
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter("%(asctime)s:%(name)s:%(message)s")
    file_handler = logging.FileHandler(f"logs/{logFileName}")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)
    return logger


logger = loggerInit(logFileName="allCourt.bot.log")


def seleniumLiteTrigger(headlessFlag):
    from seleniumwire import webdriver
    with open("vpn.config.json") as json_data_file:
        configs = json.load(json_data_file)

    atmpt = 0
    while atmpt < 10:
        try:
            VPN_User = configs['VPN_User']
            VPN_Pass = configs['VPN_Pass']
            VPN_IP_PORT = configs['VPN_IP_US'][randint(0, len(configs['VPN_IP_US']) - 1)]+":"+configs['VPN_Port']
            proxies = {
                "http": f"http://{VPN_User}:{VPN_Pass}@{VPN_IP_PORT}",
                "https": f"http://{VPN_User}:{VPN_Pass}@{VPN_IP_PORT}",
            }
            options = {'proxy': proxies}
            if "Windows" in str(platform.system()):
                # WINDOWS
                geckoPath = r"driver\\geckodriver.exe"
            elif "Linux" in str(platform.system()):
                # Linux
                geckoPath = r"driver/geckodriver"
            else:
                # Mac
                geckoPath = r"driver/geckodriver"


            theaders = {
                'authority': 'ifconfig.me',
                'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
                'accept-language': 'en-US,en;q=0.9',
                'cache-control': 'max-age=0',
                # 'cookie': 'ext_name=ojplmecpdpgccookcobabopnaifgidhf',
                'dnt': '1',
                'sec-ch-ua': '"Not?A_Brand";v="8", "Chromium";v="108", "Google Chrome";v="108"',
                'sec-ch-ua-mobile': '?0',
                'sec-ch-ua-platform': '"Linux"',
                'sec-fetch-dest': 'document',
                'sec-fetch-mode': 'navigate',
                'sec-fetch-site': 'none',
                'sec-fetch-user': '?1',
                'upgrade-insecure-requests': '1',
                'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36',
            }

            response = requests.get('https://ifconfig.me/', headers=theaders, timeout=10, proxies=proxies)

            if "What Is My IP Address? - ifconfig.me" not in response.text:
                raise Exception("InvalidIP")
            else:
                logger.debug("IP Valid")

            driver = webdriver.Firefox(executable_path=geckoPath, seleniumwire_options=options)
            # driver.
            driver.maximize_window()
            time.sleep(randint(10000, 100000) / 10000)
            try:
                driver.get("https://ifconfig.me/")
                # time.sleep(randint(50,150)/1000)
                driver.refresh()
                if '''<a href="http://ifconfig.me">What Is My IP Address? - ifconfig.me</a>''' in driver.page_source:
                    logger.debug(f"New Rotated IP: {driver.find_element(by=By.ID, value='ip_address').text}")
                    return driver
                # time.sleep(randint(50,150)/1000)
                # TODO remove
                return driver
            except Exception as e:
                logger.debug(e)
                driver.quit()
                raise Exception("BadSession")

        except Exception as e:
            atmpt += 1
            logger.debug(f"IP unavailable, rotating. {e}")
            if atmpt == 10:
                raise e

def loadSearchEngine(driver):
    logger.debug(f"Started loadSearchEngine")
    driver.get("https://www.court.gov.il/NGCS.Web.Site/HomePage.aspx")
    time.sleep(10)
    for _ in range(8):
        ActionChains(driver).send_keys(Keys.TAB).perform()
        time.sleep(0.5)
    ActionChains(driver).send_keys(Keys.ENTER).perform()
    time.sleep(5)
    driver.find_element("id", "ui-id-2").click()
    time.sleep(2)


def loadSearchAndTrigger(driver):
    logger.debug(f"Started loadSearchAndTrigger")

    logger.debug("------------------------------------------------")
    logger.critical("Please input/confirm search FROM date in DD/MM/YYYY format")
    logger.debug("------------------------------------------------")
    while True:
        try:
            startDate = input()
            if startDate.count("/") == 2: raise Exception("InvalidYear")
            if int(startDate.strip("/")[0]) > 32: raise Exception("Invalid Date")
            if int(startDate.strip("/")[1]) > 13: raise Exception("Invalid Month")
            if int(startDate.strip("/")[1]) > 2025: raise Exception("Invalid Year")
            break
        except Exception as e:
            logger.debug(e)

    logger.debug("------------------------------------------------")
    logger.critical("Please input/confirm search END/TILL date in DD/MM/YYYY format")
    logger.debug("------------------------------------------------")
    while True:
        try:
            stopDate = input()
            if stopDate.count("/") == 2: raise Exception("InvalidYear")
            if int(stopDate.strip("/")[0]) > 32: raise Exception("Invalid Date")
            if int(stopDate.strip("/")[1]) > 13: raise Exception("Invalid Month")
            if int(stopDate.strip("/")[1]) > 2025: raise Exception("Invalid Year")
            break
        except Exception as e:
            logger.debug(e)
    return startDate, stopDate


def checkCourtContent(threadDriver):
    errorTriggerTime = 120
    # searchParams = {"SelectCourt":threadDriver.find_element(By.ID,"LocateByParameters1_ddlSelectCourt").get_property("value"),
    #                 "SelectProceeding":threadDriver.find_element(By.ID,"LocateByParameters1_ddlSelectProceeding").get_property("value"),
    #                 "SelectCaseType":threadDriver.find_element(By.ID,"LocateByParameters1_ddlSelectCaseType").get_property("value"),
    #                 "SelectCaseInterest":threadDriver.find_element(By.ID,"LocateByParameters1_ddlSelectCaseInterest").get_property("value"),
    #                 "JudgeName":threadDriver.find_element(By.ID,"LocateByParameters1_ddlJudgeName").get_property("value"),
    #                 "DecisionType":threadDriver.find_element(By.ID,"LocateByParameters1_ddlDecisionType").get_property("value"),
    #                 "dateFrom":threadDriver.find_element(By.ID,"LocateByParameters1_dateFrom").get_property("value"),
    #                 "DateTo":threadDriver.find_element(By.ID,"LocateByParameters1_DateTo").get_property("value")}
    # logger.debug("Scraping \n" + json.dumps(searchParams,indent=5))
    try: judgeName = [a.text for a in threadDriver.find_element(By.ID,"LocateByParameters1_ddlJudgeName").find_elements(By.TAG_NAME,"option") if a.get_property("selected")][0]
    except: judgeName = ""
    countOfCases = 0
    try:
        threadDriver.find_element("id", "ButtonsGroup1_btnLocate").click()
        while threadDriver.current_url != "https://www.court.gov.il/NGCS.Web.Site/LocateDecisions/LocateDecisionOutput.aspx":
            if errorTriggerTime < 5:
                threadDriver.quit()
                raise Exception("Error on court site.")
            errorTriggerTime -= 5
            time.sleep(5)
        try: threadDriver.find_element(By.ID, "returnFocus").click()
        except: pass
        time.sleep(0.5)
        soup = BeautifulSoup(threadDriver.page_source, "html.parser")
        countOfCases = int(soup.find("span", attrs={"ref": "lbRecordCount"}).text)
    except Exception as e:
        logger.debug(e)

    threadDriver.get("javascript:__doPostBack('Header1$UpperMenu1$btnVerdictLocalization','')")
    while threadDriver.current_url != "https://www.court.gov.il/NGCS.Web.Site/LocateDecisions/LocateDecisionQuering.aspx":
        if errorTriggerTime < 5:
            threadDriver.quit()
            raise Exception("Error on court site.")
        errorTriggerTime -= 5
        time.sleep(5)
    threadDriver.find_element("id", "ui-id-2").click()
    time.sleep(1)

    return countOfCases

def processSearchDataframe(driver, finalFilter):
    logger.debug(f"Started processSearchDataframe {finalFilter}")
    errorTriggerTime = 120
    searchParams = {"SelectCourt":driver.find_element(By.ID,"LocateByParameters1_ddlSelectCourt").get_property("value"),
                    "SelectProceeding":driver.find_element(By.ID,"LocateByParameters1_ddlSelectProceeding").get_property("value"),
                    "SelectCaseType":driver.find_element(By.ID,"LocateByParameters1_ddlSelectCaseType").get_property("value"),
                    "SelectCaseInterest":driver.find_element(By.ID,"LocateByParameters1_ddlSelectCaseInterest").get_property("value"),
                    "JudgeName":driver.find_element(By.ID,"LocateByParameters1_ddlJudgeName").get_property("value"),
                    "DecisionType":driver.find_element(By.ID,"LocateByParameters1_ddlDecisionType").get_property("value"),
                    "dateFrom":driver.find_element(By.ID,"LocateByParameters1_dateFrom").get_property("value"),
                    "DateTo":driver.find_element(By.ID,"LocateByParameters1_DateTo").get_property("value")}
    logger.debug("Scraping \n" + json.dumps(searchParams,indent=5))
    try: judgeName = [a.text for a in driver.find_element(By.ID,"LocateByParameters1_ddlJudgeName").find_elements(By.TAG_NAME,"option") if a.get_property("selected")][0]
    except: judgeName = ""

    try:
        driver.find_element("id", "ButtonsGroup1_btnLocate").click()
        while driver.current_url != "https://www.court.gov.il/NGCS.Web.Site/LocateDecisions/LocateDecisionOutput.aspx":
            if errorTriggerTime < 5:
                driver.quit()
                raise Exception("Error on court site.")
            errorTriggerTime -= 5
            time.sleep(5)
        try: driver.find_element(By.ID, "returnFocus").click()
        except: pass
        time.sleep(0.5)
        soup = BeautifulSoup(driver.page_source, "html.parser")
        currentPage = int(soup.find("span", attrs={"ref": "lbCurrent"}).text)
        totalPages = int(soup.find("span",attrs={"ref":"lbTotal"}).text)+1

        if int(soup.find("span", attrs={"ref": "lbRecordCount"}).text) == 100:
            if not finalFilter:
                driver.get("javascript:__doPostBack('Header1$UpperMenu1$btnVerdictLocalization','')")
                while driver.current_url != "https://www.court.gov.il/NGCS.Web.Site/LocateDecisions/LocateDecisionQuering.aspx":
                    if errorTriggerTime < 5:
                        driver.quit()
                        raise Exception("Error on court site.")
                    errorTriggerTime -= 5
                    time.sleep(5)
                driver.find_element("id", "ui-id-2").click()
                time.sleep(1)
                return "GoSub"

        pageContent = driver.page_source
        soup = BeautifulSoup(pageContent, "html.parser")

        r_LocateDecisionsGridArrayStore = soup.find("input", id="LocateDecisionsGridArrayStore").attrs["value"]
        listOfDocs = json.loads(r_LocateDecisionsGridArrayStore)

        for x in listOfDocs: x["JudgeName"] = judgeName

        if len(listOfDocs) >0:
            if "allCourt.referenceTable.csv" in os.listdir():
                df = pd.read_csv("allCourt.referenceTable.csv")
                df.append(pd.DataFrame.from_dict(listOfDocs)).to_csv("allCourt.referenceTable.csv", index=False)
            else:
                pd.DataFrame.from_dict(listOfDocs).to_csv("allCourt.referenceTable.csv", index=False)
        while currentPage < totalPages:
            currentPage = int(soup.find("span", attrs={"ref": "lbCurrent"}).text)
            logger.debug("Downloading "+ soup.find("span",attrs={"ref":"lbCurrent"}).text +"/"+ soup.find("span",attrs={"ref":"lbTotal"}).text)
            for z,a in enumerate(driver.find_element(By.CLASS_NAME,"ag-center-cols-container").find_elements(By.CLASS_NAME,"ag-row")):
                driver.find_element(By.CLASS_NAME,"ag-center-cols-container").find_elements(By.CLASS_NAME,"ag-row")[z].find_element(By.TAG_NAME, "input").click()
                time.sleep(0.5)

                if len(driver.find_element(By.CLASS_NAME,"ag-center-cols-container").find_elements(By.CSS_SELECTOR,"div[aria-selected='true']")) == 5:
                    driver.get('javascript:WebForm_DoPostBackWithOptions(new WebForm_PostBackOptions("btnDownloadWordDocs", "", true, "", "", false, true))')
                    time.sleep(5)
                    try:
                        driver.find_element(By.ID, "returnFocus").click()
                        try:
                            errorMsg = driver.find_element(By.CSS_SELECTOR,"td[style='PADDING-RIGHT: 10px; FONT-WEIGHT: normal; FONT-SIZE: 12px; COLOR: #333366; DIRECTION: rtl; FONT-FAMILY: Arial']").text
                        except:
                            errorMsg = ""
                        logger.debug("Skipping set with error on page '" + soup.find("span", attrs={"ref": "lbCurrent"}).text + "' \nerror reported by site: " + errorMsg)
                    except: pass

                    [b.find_element(By.TAG_NAME,"input").click() for b in driver.find_element(By.CLASS_NAME,"ag-center-cols-container").find_elements(By.CSS_SELECTOR,"div[aria-selected='true']")]
                    [b.find_element(By.TAG_NAME,"input").click() for b in driver.find_element(By.CLASS_NAME,"ag-center-cols-container").find_elements(By.CSS_SELECTOR,"div[aria-selected='true']")]
                    time.sleep(0.5)

            if len(driver.find_element(By.CLASS_NAME, "ag-center-cols-container").find_elements(By.CSS_SELECTOR,"div[aria-selected='true']")) > 0:
                driver.get('javascript:WebForm_DoPostBackWithOptions(new WebForm_PostBackOptions("btnDownloadWordDocs", "", true, "", "", false, true))')
                time.sleep(5)
                [b.find_element(By.TAG_NAME, "input").click() for b in driver.find_element(By.CLASS_NAME, "ag-center-cols-container").find_elements(By.CSS_SELECTOR,"div[aria-selected='true']")]
                [b.find_element(By.TAG_NAME, "input").click() for b in driver.find_element(By.CLASS_NAME, "ag-center-cols-container").find_elements(By.CSS_SELECTOR,"div[aria-selected='true']")]
            driver.find_element(By.CSS_SELECTOR,"div[ref='btNext']").click()
            soup = BeautifulSoup(driver.page_source, "html.parser")
            time.sleep(2)
            if currentPage == int(soup.find("span", attrs={"ref": "lbCurrent"}).text): break
    except Exception as e:
        logger.debug(e)
    driver.get("javascript:__doPostBack('Header1$UpperMenu1$btnVerdictLocalization','')")
    while driver.current_url != "https://www.court.gov.il/NGCS.Web.Site/LocateDecisions/LocateDecisionQuering.aspx":
        if errorTriggerTime < 5:
            driver.quit()
            raise Exception("Error on court site.")
        errorTriggerTime -= 5
        time.sleep(5)
    driver.find_element("id", "ui-id-2").click()
    time.sleep(1)
    return "Completed"


def checkResumeStat(driver):
    logger.debug(f"Started checkResumeStat")
    if "resumeMap.map" in os.listdir():
        logger.debug("------------------------------------------------")
        logger.debug("-------------Resume previous run?[Y/N]----------")
        logger.debug("------------------------------------------------")
        if input().lower() == "y":
            resOpts = json.loads(open("resumeMap.map", "r").read())
            startDate = resOpts["startDate"]
            stopDate = resOpts["stopDate"]
        else:
            logger.debug("Resume rejected")
            # logger.critical("Please input search parameters in browser and press Y to start extraction.")
            resOpts = {"startDate": "", "stopDate": "", "optA": [], "optB": [], "optC": [], "optD": [], "optE": [],
                       "optF": []}
            startDate, stopDate = loadSearchAndTrigger(driver)
    else:
        logger.debug("Fresh run, no mapping found")
        # logger.critical("Please input search parameters in browser and press Y to start extraction.")
        resOpts = {"startDate": "", "stopDate": "", "optA": [], "optB": [], "optC": [], "optD": [], "optE": [],
                   "optF": []}
        startDate, stopDate = loadSearchAndTrigger(driver)

    optA = [a.get_property("value") for a in driver.find_element("id", "LocateByParameters1_ddlSelectCourt").find_elements(By.TAG_NAME, "option")]
    return startDate, stopDate, resOpts, optA

def lowerSelector(driver, optDepth, cssSelector):
    logger.debug(f"Started lowerSelector {optDepth}, {cssSelector}")
    for _ in range(50):
        driver.find_element(By.ID, cssSelector).send_keys(Keys.UP)
        time.sleep(0.1)
    for _ in range(optDepth):
        driver.find_element(By.ID, cssSelector).send_keys(Keys.DOWN)
        time.sleep(0.5)
    time.sleep(5)


def dateSelector(driver, startDate, stopDate):
    logger.debug(f"Started dateSelector {startDate}, {stopDate}")
    driver.execute_script("document.getElementById('LocateByParameters1_dateFrom').value = '" + startDate + "';")
    time.sleep(2)
    driver.execute_script("document.getElementById('LocateByParameters1_DateTo').value = '" + stopDate + "';")
    time.sleep(2)
    driver.find_element(By.ID,"LocateByParameters1_rbFundamentalDecision").click()


def threadProcess(a, b, startDate, stopDate):
    logger.debug(f"Started threadProcess {(a, b, startDate, stopDate)}")


    try:
        for c in range(b, b + 2):
            atmpt = 0
            while atmpt < 5:
                try:
                    threadDriver = seleniumLiteTrigger(headlessFlag=False)
                    loadSearchEngine(threadDriver)
                    lowerSelector(threadDriver, optDepth=a, cssSelector="LocateByParameters1_ddlSelectCourt")
                    lowerSelector(threadDriver, optDepth=c, cssSelector="LocateByParameters1_ddlJudgeName")
                    dateSelector(threadDriver, startDate, stopDate)
                    processSearchDataframe(threadDriver, finalFilter=True)
                    threadDriver.quit()
                    break
                except Exception as e:
                    logger.debug(e)
                    #
                    try:
                        threadDriver.save_screenshot(f"Error_{str(time.time()).split('.')[0]}.png")
                        threadDriver.quit()
                    except: pass
                    atmpt += 1
                    if atmpt == 5:
                        raise e
    except Exception as e:
        logger.debug(e)
        # threadDriver.save_screenshot(f"Error_{str(time.time()).split('.')[0]}.png")
        # logger.debug("---Please notify dev about current error before closing for debug---")
        # logger.debug("---Continue with exit sequence?[Y]---")
        # while input().lower() != "y":
        #     logger.debug("---Continue with exit sequence?[Y]---")
    # threadDriver.quit()

def courtCheck(a, startDate, stopDate):
    logger.debug(f"Started threadProcess {(a, startDate, stopDate)}")
    try:
        atmpt = 0
        while atmpt < 5:
            try:
                threadDriver = seleniumLiteTrigger(headlessFlag=False)
                loadSearchEngine(threadDriver)
                lowerSelector(threadDriver, optDepth=a, cssSelector="LocateByParameters1_ddlSelectCourt")
                dateSelector(threadDriver, startDate, stopDate)
                countOfCases = checkCourtContent(threadDriver)
                threadDriver.quit()
                break
            except Exception as e:
                logger.debug(e)
                #
                try:
                    threadDriver.save_screenshot(f"Error_{str(time.time()).split('.')[0]}.png")
                    threadDriver.quit()
                except: pass
                atmpt += 1
                if atmpt == 5:
                    raise e
    except Exception as e:
        logger.debug(e)
    return countOfCases

def threadInit(a, startDate, stopDate, statOpts, optA, resOpts):
    logger.debug(f"Started threadInit {(a, startDate, stopDate, statOpts, optA, resOpts)}")
    subdriver = seleniumLiteTrigger(headlessFlag=False)
    try:
        atmpt = 4
        while atmpt < 5:
            try:
                loadSearchEngine(subdriver)
                time.sleep(2)
                lowerSelector(subdriver, optDepth=a, cssSelector="LocateByParameters1_ddlSelectCourt")
                time.sleep(2)
                dateSelector(subdriver, startDate, stopDate)
                statOpts["optA"] = optA[(a):]
                statOpts["optB"] = []
                statOpts["optC"] = []
                statOpts["optD"] = []
                statOpts["optE"] = []
                statOpts["optF"] = []
                open("resumeMap.map", "w").write(json.dumps(statOpts))
                # logger.debug("100+ entries on level A. Activating Sub Filters.")
                break
            except Exception as e:
                logger.debug(e)
                atmpt +=1
                if atmpt ==5:
                    raise e

        optE = [a.get_property("value") for a in subdriver.find_element("id", "LocateByParameters1_ddlJudgeName").find_elements(By.TAG_NAME, "option")]
        if len(resOpts["optE"]) > 0:
            startPointE = len(optE) - len(resOpts["optE"])
            resOpts["optE"] = []
        else:
            startPointE = 1

        logger.debug("100+ entries on level D. Activating Sub Filters.")
        subdriver.quit()

        with ThreadPoolExecutor(max_workers=maxWorkerCount) as executor:
            results = []
            for b in range(startPointE, len(optE) + 1,2):
                dataOut = executor.submit(threadProcess, a, b, startDate, stopDate)
                results.append(dataOut)
            executor.shutdown(wait=True)

    except Exception as e:
        logger.debug(e)
        subdriver.save_screenshot(f"Error_{str(time.time()).split('.')[0]}.png")
        # logger.debug("---Please notify dev about current error before closing for debug---")
        # logger.debug("---Continue with exit sequence?[Y]---")
        # while input().lower() != "y":
        #     logger.debug("---Continue with exit sequence?[Y]---")
        subdriver.quit()



def rotatingFetch(startDate, stopDate, resOpts, optA):
    logger.debug(f"Started rotatingFetch {(startDate, stopDate, resOpts, optA)}")
    statOpts = {"startDate": startDate, "stopDate": stopDate, "optA": [], "optB": [], "optC": [], "optD": [],"optE": [], "optF": []}

    if len(resOpts["optA"]) > 0:
        startPointA = len(optA) - len(resOpts["optA"])
        resOpts["optA"] = []
    else: startPointA = 1

    for a in range(startPointA, len(optA) + 1):
        # print(a)
        # a=1
        countOfCases = courtCheck(a, startDate, stopDate)
        if countOfCases > 0:
            threadInit(a, startDate, stopDate, statOpts, optA, resOpts)
        # break
        # break


def prepDownloadDirectory():
    logger.debug(f"Started prepDownloadDirectory {()}")
    try:
        os.makedirs(f"{os.getcwd()}/downloads")
    except:
        pass

def core():
    logger.debug(f"Started core")
    prepDownloadDirectory()
    driver = seleniumLiteTrigger(headlessFlag=False)
    try:
        logger.debug("Initiated loadSearchEngine module")
        loadSearchEngine(driver)
        logger.debug("Initiated loadSearchAndTrigger module")
        startDate, stopDate, resOpts, optA = checkResumeStat(driver)
        driver.quit()

        # rotatingFetch(startDate, stopDate, resOpts, optA)
        # os.remove("resumeMap.map")

        # time.sleep(10)
        logger.debug("Clearing cache")

    except Exception as e:
        logger.debug(e)
        driver.save_screenshot(f"Error_{str(time.time()).split('.')[0]}.png")
        # logger.debug("---Please notify dev about current error before closing for debug---")
        # logger.debug("---Continue with exit sequence?[Y]---")
        # while input().lower() != "y":
        #     logger.debug("---Continue with exit sequence?[Y]---")
        driver.quit()



if __name__ == '__main__':
    logger.debug(f"Bot Initiated")
    vdisplay = Xvfb()
    vdisplay.start()
    try:
        maxWorkerCount = multiprocessing.cpu_count() * 2
        logger.debug(f"Slave count: {maxWorkerCount}")
        core()
    except Exception as e:
        logger.debug(e)
    vdisplay.stop()
    pass