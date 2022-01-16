# This  program was written as a Python learning exercise only. It is not guaranteed
# or intended for any other purpose and should not be used for stock trading. Parts of the
# program were based on code samples suggested by financialmodelingprep.com
#
# The goal of the program:
#
# The program takes a user-defined stock list of large US ticker symbols & looks up corresponding stock and financial
# data Financial Modeling Prep (see https://financialmodelingprep.com/developer/docs/). Access to
# Financial Modeling Prep is available with an API key which the user must enter into the program code. The user can
# also vary a number of other parameters (discussed below) in the code.
#
# For each stock in the stock list, the program calculates the compound annual growth rate (CAGR) for the diluted
# earnings per share (EPS) over the past five years. It then calculates the internal rate of return (IRR) and net
# present value (NPV) for someone purchasing a single unit of the stock at the current share price, assuming the EPS
# growth continues unchanged for a user-defined number of years after the purchase. The program also
# calculates the minimum EPS growth needed for the NPV of the purchaser's share earnings to breakeven with the
# share purchase.
#
# This last calculation is performed iteratively up to a maximum of 20 steps. If no minimmum EPS growth can be found for
# the NPV to break even, the iteration attempts are output to a .csv file for inspection and a warning is printed.

# The user is able to alter the discount rate for the NPV in the code, and to alter the number of years over which the
# NPV and IRR are calculated.
#
# The share purchaser's personal taxes are ignored. Terminal values for the stock are ignored. The EPS in the year of
# purchase is ignored. Additional assumptions not listed here may be implicit in the code.
#
# The program prints results both to the terminal console and to an Excel file. The file is saved in the same directory
# as the program. In the case of an early end to the program a partial output file is provided.
#
# This program was written as a Python learning exercise and is not intended for stock trading, trading advice or any
# other purpose. Nor is it guaranteed to be in any way error-free. Comments, corrections and suggestions are welcome.


# For Python 3.0 and later
import json
import sys
import numpy as np
import numpy_financial as npf
import pandas as pd
from datetime import datetime
from urllib.request import urlopen
from colorama import Fore
import copy
import ssl




# ---------------------------------------------------------------------------------------------------
def get_jsonparsed_data(url):
    """
    Receive the content of ``url``, parse it as JSON and return the object.

    Parameters
    ----------
    url : str

    Returns
    -------
    dict
    """

    #   response = urlopen(url, cafile=certifi.where())
    #   in the above line cafile is now deprecated. Have used the below ssl line instead
    #   although the ssl line may not even be needed - I'm merely following documentation.

    myContext = ssl.create_default_context(purpose=ssl.Purpose.SERVER_AUTH)
    response = urlopen(url, context=myContext)
    data = response.read().decode("utf-8")
    return json.loads(data)

# --------------------------------------------------------------------------------------------------------
# this sub open the csv file to which the price/book ratios will be saved.
# The "w" parameter means old files are overwritten


def fileopen(filename):
    try:
        file = open(filename, "w")
        return file
    except IOError:
        print("Could not open file! Is it already/still open - please close it.")
        input("Please press enter to confirm you've seen this message.")
        sys.exit()


# --------------------------------------------------------------------------------------------------------------------
def strTofloat(x):
    try:
        if x == "":
            x = 0
        x = float(x)
        return float(x)

    except Exception as ex1:
        print(ex1)
        template1 = "An exception of type {0} occurred in the function strTofloat. Arguments:\n{1!r}"
        message1 = template1.format(type(ex1).__name__, ex1.args)
        print(message1)
        sys.exit()

# ---------------------------------------------------------main----------------------------------------------------

# ----------------------------------------------------user input
# access key for financial modeling prep dot com


myApiKey = "<Insert your API key here>"

# ticker list and description.
stockListInput = ['abt', 'clx', 'dgx', 'googl', 'wec', 'ed', 'chd']
listDescription: str = "demo list"

# stocks with market cap < minMarketCap will be ignored
minMarketCap: float = 1000000000.0

# npv discount factor and years of growth after purchase
disctFactor: float = .06
yrsDiscted: int = 15

# ----------------------------------------------------check and cleanse user input

if myApiKey == "<Insert your API key here>":
    print("Error. You must obtain a valid API key from https://site.financialmodelingprep.com/developer "
          "and insert it into the code input section. The program will end.")
    sys.exit()

# stocks must be uppercase
stockList: list = []
for stocks in stockListInput:
    stockList = stockList + [stocks.upper()]

# ----------------------------------------------------initialize misc. variables

# the following correspond to Variable [newest year, oldest year]
NetIncome: float = [0, 0]
EPS: float = [0, 0]
EPScurrentSplit: float = [0, 0]
SharesOut: float = [0, 0]

# prepare a dataframe to hold the results of the caclulations across all stocks in stocklist.
# dataframe row index = stocklist names.
# dataframe column names as follows:

colNames = ["Newest yr history", "Oldest yr history", "EPS newest", "Net Income gr %",
            "EPS gr %", "Req gr % for NPV break-even", "Share gr %",
            "Price", "Shares out-standing", "Mkt Cap", "NPV", "Disct rate %",
            "IRR %", "Warnings if any", "Yrs discounted after purchase"]

# npResults = np.zeros([len(stockList), len(colNames)])
# pdResults = pd.DataFrame(data=npResults, index=stockList, columns=colNames)
pdResults = pd.DataFrame(index=stockList, columns=colNames)

# print gen info
print("Raw data provided by Financial Modeling Prep (see https://financialmodelingprep.com/developer/docs/)")
print("Oldest data are already adjusted in source database for subsequent stock splits (if any).")
print("This program is a Python learning exercise, not to be used for stock trading or financial advice. ")

# loop through each stock
for stock in stockList:
    # print blank line, then ticker
    print("")
    print("Ticker = " + stock)

    urlIncome = "https://financialmodelingprep.com/api/v3/financials/income-statement/" + stock + "?apikey=" + myApiKey
    urlSharePrice = "https://financialmodelingprep.com/api/v3/quote-short/" + stock + "?apikey=" + myApiKey
    oldTimeStamp = datetime.now()

    # load url for each stock in turn as dict
    try:
        bigDict = dict(get_jsonparsed_data(urlIncome))  # contrary to fin mod prep screen, this contains several
        # dictionaries. Their form is
        # {ticker symbol, "financials", [{"date", blaha, blah, blah blah},{older date, blah, blah ...

        if bigDict == {}:
            print(Fore.RED, "No income statement for ", stock)
            pdResults.loc[stock, "Warnings if any"] = "No income statement found."
            print(Fore.BLACK, end="")
            continue  # move on to next stock

        finDictNew = dict(bigDict['financials'][0])
        if len(bigDict['financials']) < 5:
            print(Fore.RED, "less than 5 years of data for ", stock)
            pdResults.loc[stock, "Warnings if any"] = "Less than 5 years of data"
            print(Fore.BLACK, end="")
            continue

        finDictOld = dict(bigDict['financials'][4])
        newestYear = finDictNew['date'][0:4]  # first 4 characters
        oldestYear = finDictOld['date'][0:4]  # first 4 characters
        newestYearInt = int(newestYear)
        oldestYearInt = int(oldestYear)

        # print years
        print("....................Newest Year................Oldest year")
        print("                       " + newestYear + "                       " + oldestYear)

        # get newest year data
        NetIncome[0] = strTofloat((finDictNew['Net Income Com']))
        if NetIncome[0] <= 0:
            print(Fore.RED, "Net income is negative in newest year for ", stock)
            print(Fore.BLACK, end="")
            pdResults.loc[stock, "Warnings if any"] = "NI negative in newest year"
            continue

        EPS[0] = strTofloat(finDictNew['EPS Diluted'])
        if EPS[0] == 0:
            print("Newest yr history EPS not found or blank or zero for ", stock)
            pdResults.loc[stock, "Warnings if any"] = "Newest yr history EPS not found or blank or zero"
            continue

        # get oldest year data
        NetIncome[1] = strTofloat(finDictOld['Net Income Com'])
        EPS[1] = strTofloat(finDictOld['EPS Diluted'])
        if EPS[1] == 0:
            print("EPS not found for ", stock)
            pdResults.loc[stock, "Warnings if any"] = "Oldest yr history EPS not found"
            continue

        # if either old or new net income is non-positive print warning and advance to next stock in stocklist
        if (NetIncome[0] <= 0) or (NetIncome[1] <= 0):
            print(Fore.RED, "Oldest or newest net income, or both, were non-positive for ", stock)
            pdResults.loc[stock, "Warnings if any"] = "Oldest or newest net income was non-positive."
            continue

        # from here on both old and new incomes are positive
        # calculate % compound annual growth rate from oldest year to newest year
        SharesOut[0] = NetIncome[0] / EPS[0]
        SharesOut[1] = NetIncome[1] / EPS[1]

        if SharesOut[0] < 1 or SharesOut[1] < 1:
            print(Fore.RED, "Shares outstanding estimation has resulted in negative shares.")
            print(Fore.BLACK, end="")
            pdResults.loc[stock, "Warnings if any"] = "Estimate of shares outstanding is negative."
            continue  # move on to next stock.

        Sharesgr: float = (SharesOut[0] / SharesOut[1]) ** (1 / (newestYearInt - oldestYearInt)) * 100 - 100
        NIgr: float = (NetIncome[0] / NetIncome[1]) ** (1 / (newestYearInt - oldestYearInt)) * 100 - 100
        EPSgr: float = (EPS[0] / EPS[1]) ** (1 / (newestYearInt - oldestYearInt)) * 100 - 100
        pdResults.loc[stock,
                      ["Newest yr history", "Oldest yr history", "EPS newest", "Net Income gr %",
                       "EPS gr %", "Shares out-standing", "Share gr %"]] = \
            [newestYearInt, oldestYearInt, EPS[0], NIgr, EPSgr, SharesOut[0], Sharesgr]

        # print new and old values and growth for net income, EPS (diluted) and shares outstanding
        print("Net Income ", "${:19,.0f}".format(NetIncome[0]), "    ", "${:19,.0f}".format(NetIncome[1]),
              "    CAGR = ", "{:6.1f}%".format(NIgr))
        print("Dil. EPS   ", "${:19,.2f}".format(EPS[0]), "    ", "${:19,.2f}".format(EPS[1]),
              "    CAGR = ", "{:6.1f}%".format(EPSgr))
        print("Shares      ", "{:19,.0f}".format(SharesOut[0]), "     ", "{:19,.0f}".format(SharesOut[1]),
              "    CAGR = ", "{:6.1f}%".format(Sharesgr))
        print(Fore.BLACK, end="")  # resets printing to black, in case previous was red. no line feed

        if EPSgr < 0:
            print(Fore.RED, "EPS growth during past 5 years was negative.")
            print(Fore.BLACK, end="")  # resets printing to black, in case previous was red. no line feed
            pdResults.loc[stock, "Warnings if any"] = "EPS growth during past 5 years was negative."
            continue  # advance to next stock analysis

        # look up current stock price if income is positive in both oldest and newest year.
        quoteRet = get_jsonparsed_data(urlSharePrice)
        if len(quoteRet) == 0:
            print("no shareprice found for ", stock)
            pdResults[stock, "Warnings if any"] = "No share price found"
            continue

        quoteDic = dict(quoteRet[0])
        if quoteDic == {}:
            print("no shareprice found for ", stock)
            pdResults[stock, "Warnings if any"] = "No share price found"
            continue

        shPrice: float = float(quoteDic["price"])
        # estimate market cap
        mktCap: float = shPrice * SharesOut[0]
        print("price = ", "${:6.2f}".format(shPrice), "and est. market cap = ", "${:,.2f}".format(mktCap))
        pdResults.loc[stock, ["Price", "Mkt Cap"]] = [shPrice, mktCap]
        # form is ticker, price, volume

        if mktCap < minMarketCap:
            print(Fore.RED, "market cap is less than $ ", minMarketCap, " for ", stock)
            print(Fore.BLACK, end="")
            pdResults[stock, "Warnings if any"] = "Market cap is less than $1 Billion."
            continue  # continue with next stock in list

        # project out EPS and share buyers cashflow for yrsDiscted number of  years
        # after purchase year using the 5 yr EPS gr history
        epsProj = np.zeros(yrsDiscted + 1)
        cashflProj = np.zeros(yrsDiscted + 1)
        epsProj[0] = 0  # conservative assumption, buy shares late in year, no earnings this year
        epsProj[1] = EPS[0] * (1 + EPSgr / 100)  # next years eps is this year times growth
        for count in range(2, yrsDiscted + 1):  # from 2 to 20 or whatever yrsDiscted is
            epsProj[count] = epsProj[count - 1] * (1 + EPSgr / 100)  # grow by EPSgr every year

        # share purchaser's cashflow projection is same as EPS projection except purchase price in year 0
        cashflProj = copy.deepcopy(epsProj)  # the two items are independent after copying
        cashflProj[0] = -shPrice

        epsNPV = npf.npv(disctFactor, epsProj)
        shareIRR = npf.irr(cashflProj)
        print("npv of eps projected out ", yrsDiscted, " years from next yr at gr ", "{:3.1f}%".format(EPSgr),
              " and discounted at ", "{:3.1%}".format(disctFactor), " = ", "${:6.2f}".format(epsNPV))
        print("irr of share purchase with these EPSs and current share price = ", "{:4.2%}".format(shareIRR))
        pdResults.loc[stock, ["NPV", "Disct rate %", "Yrs discounted after purchase", "IRR %"]] = \
            [epsNPV, disctFactor * 100, yrsDiscted, shareIRR * 100]  # as percents

        # find iteratively the min growth needed for an NPV on buyer's cashflow breakeven with the given disct rate
        # iteration will use up to 20 steps, so put into a pdframe of 20 cols by 23 rows
        # the rows will be the purchase price, EPS growth values for the next yrsDisct-1 years, the trial growth on EPS,
        # the NPV at the given disct rate, and finally the slope (npv2-npv1)/(trial growth2-trial growth1)
        # i.e. slope this col vs. last col
        dfColumns: int = list(range(0, 20))
        dfRows = ["purchase price"] + list(range(1, yrsDiscted + 1)) + ["trial growth", "trial npv", "slope"]
        dfIterate = pd.DataFrame(columns=dfColumns, index=dfRows)
        dfIterate.iloc[:, :] = 0  # initialize to zero each time for new stock in stock list

        # for every col (iteration) the purchase price is the same
        dfIterate.loc["purchase price", :] = -shPrice

        # 1st column of dfIterate is cashflow as previously calculated, EPSgr, and epsNPV as prev calc
        for row in range(0, yrsDiscted + 1):  # stops at yrsDsct
            dfIterate.iloc[row, 0] = cashflProj[row]
        dfIterate.loc["trial growth", 0] = EPSgr
        dfIterate.loc["trial npv", 0] = epsNPV

        # for 2nd iteration, stored in col 1, use 0.2 times the growth rate of col 0 to project EPS out
        # yrsDisct years beyond the initial purchase year
        dfIterate.loc['trial growth', 1] = EPSgr * 0.2
        dfIterate.loc[1, 1] = EPS[0] * (1 + .2 * EPSgr / 100)  # EPS in 1st yr after share purchase
        for row in range(2, yrsDiscted + 1):  # stops in yrsDiscted
            dfIterate.loc[row, 1] = dfIterate.loc[row-1, 1] * (1 + 0.2 * EPSgr / 100)

        dfIterate.loc["trial npv", 1] = npf.npv(disctFactor, dfIterate.iloc[0:yrsDiscted, 1])
        # calc slope for col 2
        fname = "min req grwth fail for " + stock + ".csv"  # print iterations here in case of failure
        if (dfIterate.loc["trial growth", 1] - dfIterate.loc["trial growth", 0]) != 0:
            dfIterate.loc["slope", 1] = (dfIterate.loc["trial npv", 1] - dfIterate.loc["trial npv", 0]) / \
                                        (dfIterate.loc["trial growth", 1] - dfIterate.loc["trial growth", 0])
        else:
            print("Slope denom. = 0. required growth not found for stock", stock)
            pdResults.loc[stock, "Warnings if any"] = "Required growth not found. Slope denom. = 0"
            dfIterate.to_csv(fname)
            break  # on 0 slope go to next stock

        if dfIterate.loc["slope", 1] == 0:
            print("Slope = 0. Required growth not found for stock", stock)
            pdResults.loc[stock, "Warnings if any"] = "Required growth not found. Slope = 0"
            dfIterate.to_csv(fname)
            break  # min. growth not found, go to next stock

        # with the first two cols in place can iterate to find the required growth for npv to be 0 - breakeven
        # growth
        for col in range(2, 20):  # iterate cols 2 to 19
            if dfIterate.loc["slope", col - 1] == 0:
                print("Minimum required growth could not be found for ", stock)
                pdResults.loc[stock, "Warnings if any"] = "Required growth not found. Prev slope = 0"
                dfIterate.to_csv(fname)
                # print(dfIterate)
                break  # min. growth not found, go to next stock

            dfIterate.loc["trial growth", col] = \
                dfIterate.loc["trial growth", col - 1] - dfIterate.loc["trial npv", col - 1] / dfIterate.loc[
                    "slope", col - 1]
            dfIterate.loc[1, col] = EPS[0] * \
                            (1 + dfIterate.loc["trial growth", col] / 100)  # 1st yr of earnings after purchase

            for row in range(2, yrsDiscted + 1):
                dfIterate.iloc[row, col] = dfIterate.iloc[row-1, col] * \
                                           (1 + dfIterate.loc["trial growth", col] / 100)  # all other earning yrs

            # take the npv of the cashflow at the trial growth
            dfIterate.loc["trial npv", col] = npf.npv(disctFactor, dfIterate.iloc[0:yrsDiscted, col])
            # calc new slope
            if (dfIterate.loc["trial growth", col] - dfIterate.loc["trial growth", col - 1]) == 0:
                print("Slope = 0. Minimum required growth could not be found for ", stock)
                pdResults.loc[stock, "Warnings if any"] = "Required growth not found. Slope = 0"
                dfIterate.to_csv(fname)
                # print(dfIterate)
                break  # slope not found, go to next stock

            dfIterate.loc["slope", col] = \
                (dfIterate.loc["trial npv", col] - dfIterate.loc["trial npv", col - 1]) / \
                (dfIterate.loc["trial growth", col] - dfIterate.loc["trial growth", col - 1])

            if (abs(dfIterate.loc["trial npv", col]) < 0.01) and (col <= 19):  # iteration has come to a successful end
                if dfIterate.loc["trial growth", col] <= EPSgr:
                    print(Fore.GREEN, end="")
                else:
                    print(Fore.RED, end="")
                print("The min. required EPS growth for breakeven is    ",
                      "{:4.1f}".format(dfIterate.loc["trial growth", col]),
                      "% at a dsct rate of ", "{:4.1f}".format(100 * disctFactor), " %")
                print("The actual 5 year historical comp ann EPS grwth = ", "{:4.1f}".format(EPSgr), "%")
                print(Fore.BLACK, end="")  # reset print to black
                pdResults.loc[stock, "Req gr % for NPV break-even"] = dfIterate.loc["trial growth", col]
                break  # no need to iterate further.

            if (abs(dfIterate.loc["trial npv", col]) >= 0.01) and (col == 19):  # iteration ended unsuccessfully
                print("Minimum required EPS growth not found.")
                pdResults.loc[stock, "Warnings if any"] = "Minimum required growth not found after 20th iteration."
                dfIterate.to_csv(fname)

    except Exception as ex2:
        print(ex2)
        template1 = "An exception of type {0} occurred in the main program section. Arguments:\n{1!r}"
        message1 = template1.format(type(ex2).__name__, ex2.args)
        print(message1)
        pdResults.to_csv("early end for DCF program.csv")
        sys.exit()

# print(pdResults)

dateTimeObj = datetime.now()
timestampStr = dateTimeObj.strftime("%d-%b-%Y (%H-%M.%f)")

fileName: str = "DCF at " + str(disctFactor) + " " + listDescription + " over " + str(yrsDiscted) \
                + " yrs from " + stockList[0] + " to " + stockList[-1] + " on " + timestampStr + ".xlsx"
text2 = "Raw data provided by Financial Modeling Prep (see https://financialmodelingprep.com/developer/docs/). " \
        "All other data are calculated by program. "

text3 = "The program is for Python programming training only, not for trading or stock advice or any other purpose."

writer = pd.ExcelWriter(fileName, engine="xlsxwriter")
pdResults.to_excel(writer, startrow=4, startcol=0, sheet_name='NPV etc. results')
worksheet = writer.sheets['NPV etc. results']
worksheet.write(0, 0, fileName)
worksheet.write(1, 0, text2)
worksheet.write(2, 0, text3)
writer.save()
print("The results have been saved to an Excel file named ", fileName,
      "\nThe file is in the same directory as the program.")

