import pandas as pd
import os as os
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import os
import io
import signal
from datetime import datetime

from shiny import App, Inputs, Outputs, Session, reactive, render, ui#from shiny.express import input, render, ui
#from shinywidgets import render_plotly

#fname = './' + 'AnnArborRealEstate2023-b-noNA.csv'
#nudata = pd.read_csv(fname)
protected_names = ['Residuals','Predictions','Deviance_Resid','CI_lb', 'CI_ub','PI_lb', 'PI_ub']
max_factor_values = 50

def collisionAvoidance(name,namelist):
    while name in namelist: 
        name = name + '_0'        
    return(name)


# ui.page_opts(title="Pivot Tabler", fillable=True)

# with ui.sidebar():
#     ui.input_selectize(
#         "var", "Select variable",
#         nudata.columns
#     )
#     ui.input_numeric("bins", "Number of bins", 30)

#dfn = nudata.copy(deep = True)
aggopts = ['sum','mean','median', 'min', 'max', 'count' , 'std','var']
app_ui = ui.page_navbar( 
    ui.nav_panel("Input",
        ui.input_file("file1", "Choose .csv or .dta File", accept=[".csv",".CSV",".dta",".DTA"], multiple=False, placeholder = ''),
        ui.input_radio_buttons('killna', 'Remove rows with missing data in one or more columns?',choices = ['No','Yes']),
        ui.row(ui.output_data_frame("info"), height = '500px'),
        ui.row(ui.output_data_frame("summary")),
        ui.row(ui.output_data_frame("data")),
        ),
    ui.nav_panel("Pivot Table",
                ui.row(
                    ui.column(1,offset = 0,*[ui.input_selectize("aggfunV","Aggregation:",choices = aggopts,selected = 'count', multiple = False,width = "100px")]),
                    ui.column(3,offset = 0,*[ui.input_selectize("valuesV","Values to aggregate:",choices = ['-'],multiple = True, width = "400px")]),
                    ui.column(3,offset = 0,*[ui.input_selectize("indexV" ,"Group Rows By:",choices = ['-'],multiple = True,width = "400px")]),
                    ui.column(3,offset = 0, *[ui.input_selectize("columnsV","Group Cols By:",choices = ['-'],multiple = True,width = "400px")]),
                ),
                ui.row(
                    #ui.column(4,offset = 0, *[ui.input_radio_buttons('nacode',"Code Missing Values:",choices = ['NaN','0','blank'], selected = '0', inline=True)]),
                    #ui.column(3,offset = 0, *[ui.input_numeric("nodig","# of Digits:", value = 3, min=0, max=10,width='100px')]),
                    ui.column(3,offset = 0, *[ui.input_radio_buttons('mtotals',"Show Margins:",choices = ['Yes','No'],selected = 'No',inline = True)]),   
                    ui.column(2,offset = 0,),  
                    ui.column(3,offset = 0,*[ui.download_button("downloadDP","Save Pivot Table",width = "200px")]),     
                ),
                ui.row(ui.output_table("pivotDF")),
                ui.row(
                     ui.column(3,offset = 1,*[ui.input_selectize("fvar","Filter On:" ,choices = ['-'], multiple=False)]),
                     ui.column(3,offset = 1, *[ui.input_selectize("fitems","Included Rows:",choices = ['-'], multiple=True)]),
                     ui.column(2,offset = 0, *[ui.input_radio_buttons("filterinit","Start with:",choices = ['All','None'],selected = 'All',inline = True)]),
                     ui.column(4,offset = 0,)
                     ),
                 ui.row(
                        ui.HTML("<p>Rows Selected (filter on \"-\" above to clear filter).</p>"),
                     ),
                 ui.row(
                     ui.output_text_verbatim("log")
                     ),
                ),
    ui.nav_panel("Pivot Plot",
                ui.row(
                    ui.input_radio_buttons("pltype", "Plot Type:", choices =['bar','line','barh', 'area'],selected = 'bar',inline = True),
                ),
                ui.row(
                    ui.output_plot("pivot_plot"), height="900px"
                ),
                ),
underline = True, title = "pivot v.0.0.0 ")

def server(input: Inputs, output: Outputs, session: Session):
    plt_data = reactive.value(pd.DataFrame())
    logstr = reactive.value(f"Log Start: {datetime.now()}")
    pvt_data = reactive.value(pd.DataFrame())
    subdict = reactive.value({})
##########################################################################
####  Input panel
##########################################################################

    @reactive.calc
    def parsed_file():
        #print("Starting file read.")
        if input.file1() is None:
            #print("No file found in parsed_file.")
            return pd.DataFrame()
        else: 
            fpath = str(input.file1()[0]['datapath'])
            if (fpath[-4:] == '.csv') or (fpath[-4:] == '.CSV'):
                df = pd.read_csv(input.file1()[0]["datapath"])
            else:
                df = pd.read_stata(input.file1()[0]["datapath"])
            #pushlog("************************************************")
            #print("File read: "  + input.file1()[0]['name'])
            #pushlog("************************************************")
            stemp = df.isna().sum().sum()
            df.replace('',np.nan,inplace = True)
            stemp = df.isna().sum().sum() - stemp
            nona = sum(df.isna().sum(axis=1) >0)
            if (stemp > 0) | (nona > 0):
                print(f" {stemp} blank entries converted to NaNs. {nona} rows out of {len(df)} have missing data.")
            else:
                print("No rows have missing data.")
                
            #get rid of spaces in column names
            df.columns = df.columns.str.lstrip()
            df.columns = df.columns.str.rstrip()
            df.columns = df.columns.str.replace(' ','_')
            # df.columns = df.columns.str.replace('[','_')
            # df.columns = df.columns.str.replace(']','_')
            # df.columns = df.columns.str.replace('(','_')
            # df.columns = df.columns.str.replace(')','_')
            #change names to avoid collisions with protected names
            #df.columns = [collisionAvoidance(item,protected_names) for item in df.columns]
            if (input.killna() == 'Yes') : 
                #print("Rows with missing values dropped on input by user request.")
                df.dropna(inplace = True)
            #reset plotting data
            cols = df.columns
            #print(f"Setting plt_data. {len(df)} rows.")
            plt_data.set(df)
            num_var = list(df.select_dtypes(include=np.number).columns)
            str_var = [item for item in cols if item not in num_var]    
            all_var = list(df.columns)

            ui.update_selectize('valuesV',choices = num_var)
            ui.update_selectize('indexV',choices = all_var)
            ui.update_selectize('columnsV',choices = all_var)

            #reset subsetting data
            cols = list(df.columns)
            #print(list(df.columns))
            #fct used for subsetting (fct short for factor) and coloring
            fct_var = [item for item in cols if ((item not in num_var) or (len(list(df[item].unique()))<=max_factor_values))]
            #subset dictionary
            newdict = {}                
            newdict = {item: list(map(str,list(df[item].unique()))) for item in fct_var}
            subdict.set(newdict)
            num_fct = [item for item in list(df.columns) if (item in num_var) and len(list(df[item].unique())) <= max_factor_values]
            ui.update_selectize("fvar",choices = ['-']+fct_var)           
            return df
        
    @reactive.effect
    @reactive.event(input.aggfunV)
    def chooseValues():
        df = plt_data()
        if df.empty : return
        if (input.aggfunV == 'count') : 
            ui.update_selectize('valuesV', choices = list(df.columns))
        else:
            num_var = list(df.select_dtypes(include=np.number).columns)
            ui.update_selectize('valuesV', choices = num_var)
        return
    
    @render.data_frame
    def info():
        df = parsed_file()
        if len(df) < 50000 : return
        #df = plt_data()
        if df.empty:
           return 
        #display df.info
        buffer = io.StringIO()
        df.info(buf=buffer)
        slst = buffer.getvalue().splitlines()
        sdf = pd.DataFrame([item.split() for item in slst[5:-2]],columns = slst[3].split())
        return sdf
    
    @render.data_frame
    def data():
        df =parsed_file()
         #df = plt_data()
        if df.empty : 
            return
        if (len(df) > 50000): return
        return df
##########################################################################
####  Create and Render Pivot Table
##########################################################################

    @render.table(index=True)
    @reactive.event(input.mtotals, input.aggfunV, input.columnsV, input.indexV, input.valuesV, input.fvar, input.fitems)
    def pivotDF():
        aV = input.aggfunV()
        cV = input.columnsV()
        iV = input.indexV()
        vV = input.valuesV()
        if (len(cV) == 0) & (len(iV) == 0) : return
        #if (len(vV) == 0): return
        #print(f"{aV};{list(cV)};{list(iV)};{list(vV)}")
        if (plt_data().empty): return
        dfn = plt_data()
        #if (aV == '-'): return
        if (len(cV)==0): 
            cV = []
        if (len(iV) == 0): 
            iV = []
        if (len(vV) == 0): return
        #take out the rows that the user has decided to ignore
        for item in list(subdict().keys()):
            dfn = dfn[dfn[item].astype('str').isin(list(subdict()[item]))]
        MGN=True
        mgn_title = "All"
        if input.mtotals() == 'No': 
            mgn_title = None
            MGN = False
        #all this setup, one line to do the work
        pivot_table = dfn.pivot_table(values=list(vV), index=list(iV), columns = list(cV), aggfunc= aV,margins = MGN, margins_name = mgn_title )
        #and then a little cleanup
        ##print(f"Rounding to {input.nodig()} places.")
        #pivot_table.round(input.nodig())
        ##print(f"Recoding NaNs to {input.nacode()}")
        #if input.nacode() != 'NaN': pivot_table.fillna(input.nacode())
        #pivot_table.insert(0,"; ".join(iV),list(pivot_table.index))
        pvt_data.set(pivot_table)
        #print("returning pivot table")
        #print(pivot_table)
        return pivot_table
    
    #event observer to update subsetting dictionary
    @reactive.effect
    @reactive.event(input.fvar)
    def newfilter():
        df = plt_data()
        #print("In Newfilter")
        if len(df) == 0: return
        #if fvar is not set, restore all rows
        if (input.fvar() == '-'): 
            #pushlog("Resetting row filter, all rows active.")
            #fct used for subsetting (fct short for factor)
            cols = list(df.columns)
            num_var = list(df.select_dtypes(include=np.number).columns)
            fct_var = [item for item in cols if ((item not in num_var) or (len(list(df[item].unique()))<=max_factor_values))]
            #fctc_var = [item for item in fct_var if (len(list(df[item].unique()))<=5)]#10
            fct_var.insert(0,"-")
            #fctc_var.insert(0,"-")
            newdict = {}
            newdict = {item: list(map(str,list(df[item].unique()))) for item in fct_var if item != '-'}
            subdict.set(newdict)
            ui.update_selectize("fitems",choices = [], selected = [])
            return
        fv = input.fvar()
        cur_items = subdict()[fv]
        inc_items = list(df[input.fvar()].astype('str').unique())
        ui.update_selectize("fitems", choices = inc_items, selected = cur_items)

    @reactive.effect
    @reactive.event(input.fitems)
    def subdict_update():
        #update the dictionary of currently active rows keys=col names values = lists of active row values
        #print("In subset Dictionary update")
        fv = input.fvar()
        if (fv == '-'): return
        newdict = subdict()
        newdict[fv] = list(input.fitems())
        subdict.set(newdict)
        #print(f"Plot dictionary update:  Var = {fv}; Active values: {', '.join(newdict[fv])}")

    @reactive.effect
    @reactive.event(input.filterinit)
    def setFilter():
        #print("resetting filter")
        df = plt_data()
        if (df.empty) : return
        if input.fvar() == '-' : return
        inc_items = list(df[input.fvar()].astype('str').unique())
        #check to see if we've aready started editing
        if input.filterinit() == 'All':
            ui.update_selectize("fitems", choices = inc_items, selected = inc_items)
        else:
            ui.update_selectize("fitems", choices = inc_items, selected = [])


    #displays log of currently active rows
    @render.text
    @reactive.event(input.fvar,input.fitems, input.aggfunV, input.columnsV, input.indexV, input.valuesV)
    def log():  
        #print("In render log")
        if 1==1: #input.fvar() != '-':
            return '\n'.join([f'{item}: {subdict()[item]}' for item in subdict().keys()])
        else:
            return ""
        



    @render.plot
    #@reactive.event(input.updateB)
    def pivot_plot():
        df = pvt_data()
        if df.empty : return
        df.plot(kind = input.pltype())

    @render.download(filename="pivot_table_data.csv")
    def downloadDP():
        df = pvt_data()
        #print(f"from render download {df}")
        #create the row subset for graphing    
        #for item in list(subdict().keys()):
        #    df = df[df[item].astype('str').isin(list(subdict()[item]))]
        yield df.to_csv(index = True)

app = App(app_ui, server)

