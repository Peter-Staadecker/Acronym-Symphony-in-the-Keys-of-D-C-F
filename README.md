# Acronym-Symphony-in-the-Keys-of-D-C-F
A program that calculates the IRR and NPV of share purchases using past EPS growths projected into the future.

The goal of the program:

The program takes a user-defined list of ticker symbols for large US stocks & looks up corresponding stock and financial data in Financial Modeling Prep (see https://financialmodelingprep.com/developer/docs/). Access to Financial Modeling Prep is available with an API key which the user must enter into the program code. The user can
also vary a number of other parameters (discussed below) in the code.

For each stock in the stock list, the program calculates the compound annual growth rate (CAGR) for the diluted earnings per share (EPS) over the past five years. Financial Modeling Prep will have already adjusted the data for past splits, if any. The program then calculates the internal rate of return (IRR) and net present value (NPV) for someone purchasing a single unit of the stock at the current share price, assuming the EPS growth continues unchanged for a user-defined number of years after the purchase. The program also calculates the minimum EPS growth needed for the NPV of the purchaser's future share earnings during the stated number of years to breakeven with the share purchase price.

This last calculation is performed iteratively in a maximum of 20 steps. If no minimmum EPS growth can be found for the NPV to break even, the iteration attempts are output to a .csv file for inspection and a warning is printed.

The user is able to alter the discount rate for the NPV in the code, and to alter the number of years over which the NPV and IRR are calculated.

The share purchaser's personal taxes are ignored. Terminal values for the stock are ignored. The EPS in the year of purchasea are ignored. Additional assumptions not listed here may be implicit in the code.

The program prints results both to the terminal console and to an Excel file. The file is saved in the same directory as the program. In the case of an early end to the program a partial output file is provided.

Some sections of this program were based on example code provided by Financial Modeling Prep.

This program was written as a Python learning exercise and is not intended for stock trading, trading advice or any other purpose. Nor is it guaranteed to be in any way error-free. Comments, corrections and suggestions are welcome.
