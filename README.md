pivoter() is a light weight shiny shell around some basic plotting tools (matplotlib, seaborn, plotly) and pandas pd.pivot_table function.   
What it attempts to do:

1. Read a .csv file in
2. Create a pivot table based on user's choice of variables, and filters
3. Complex compound row and column structures.
4. Plot the pivot table
5. Minimal guard rails 
Early developement/proof of concept stage code.

Basic operation  

Input tab

1. Choose andinput file on the Input tab.  .csv work well .dta (STATA) files sometimes work
   
Pivot Table Tab

3. Aggregation allows to you choose the summary of the value variable to compute for each cell
4. Value expects a column name of a column containing numerical values, unless you use "count" which just counts occupied cells.
5. Group rows by and group columns by are lists of column names.  In the case of group rows by, th evalues in the column names will
    be used as grouping categories.   More than one row grouping variable and column grouping variable creates complex tables.
6. Show margins if yes applies the aggregation function to all values contrained in the adjacent column or row.
7. Filter On: choose a variable use values of that variable to include/ or exclude observations from your pivot table
8. Included Rows: the values of the variable chosen in #7 that will be included in the pivot table
9. Start With:  if "all" start with all rows included, if "none" start with all rows excluded

Pivot Plot

11. Pivoter will bravely try to represent the pivot table you created using the chart type you chose.
