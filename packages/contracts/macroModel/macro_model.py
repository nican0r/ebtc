# -*- coding: utf-8 -*-
"""Baseline vs Alternative V2 Copy

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1NNPdiKfO3950MuAGyIXTNrr4OMliINKb

# Parameters and Initialization
"""

import random
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import matplotlib.pyplot as plt
import scipy.stats
from plotly.subplots import make_subplots

#policy functions
rate_issuance = 0.01
rate_redemption = 0.01
base_rate_initial = 0

#global variables
period = 24*365
month=24*30
day=24

#ether price
price_ether_initial = 1000
price_ether = [price_ether_initial]
sd_ether=0.02
drift_ether = 0

#LQTY price & airdrop
price_LQTY_initial = 1
price_LQTY = [price_LQTY_initial]
sd_LQTY=0.005
drift_LQTY = 0.0035
#reduced for now. otherwise the initial return too high
quantity_LQTY_airdrop = 500
supply_LQTY=[0]
LQTY_total_supply=100000000

#PE ratio
PE_ratio = 50

#natural rate
natural_rate_initial = 0.2
natural_rate = [natural_rate_initial]
sd_natural_rate=0.002

#stability pool
initial_return=0.2
return_stability=[initial_return]
sd_return=0.001
sd_stability=0.001
drift_stability=1.002
theta=0.001

#liquidity pool & redemption pool
sd_liquidity=0.001
sd_redemption=0.001
drift_liquidity=1.0003
redemption_star = 0.8
delta = -20

#close cdps
sd_closecdps=0.5
#sensitivity to EBTC price
beta = 0.2

#open cdps
distribution_parameter1_ether_quantity=10
distribution_parameter2_ether_quantity=500
distribution_parameter1_CR = 1.1
distribution_parameter2_CR = 0.1
distribution_parameter3_CR = 16
distribution_parameter1_inattention = 4
distribution_parameter2_inattention = 0.08
sd_opencdps=0.5
n_steady=0.5
initial_open=10

#sensitivity to EBTC price & issuance fee
alpha = 0.3

#number of runs in simulation
n_sim= 8640

"""# Exogenous Factors

Ether Price
"""

#ether price
for i in range(1, period):
  random.seed(2019375+10000*i)
  shock_ether = random.normalvariate(0,sd_ether)
  price_ether.append(price_ether[i-1]*(1+shock_ether)*(1+drift_ether))

"""Natural Rate"""

#natural rate
for i in range(1, period):
  random.seed(201597+10*i)
  shock_natural = random.normalvariate(0,sd_natural_rate)
  natural_rate.append(natural_rate[i-1]*(1+shock_natural))

"""LQTY Price - First Month"""

#LQTY price
for i in range(1, month):
  random.seed(2+13*i)
  shock_LQTY = random.normalvariate(0,sd_LQTY)  
  price_LQTY.append(price_LQTY[i-1]*(1+shock_LQTY)*(1+drift_LQTY))

"""# Cdps

Liquidate Cdps
"""

def liquidate_cdps(cdps, index, data):
  cdps['CR_current'] = cdps['Ether_Price']*cdps['Ether_Quantity']/cdps['Supply']
  price_EBTC_previous = data.loc[index-1,'Price_EBTC']
  price_LQTY_previous = data.loc[index-1,'price_LQTY']
  stability_pool_previous = data.loc[index-1, 'stability']

  cdps_liquidated = cdps[cdps.CR_current < 1.1]
  cdps = cdps[cdps.CR_current >= 1.1]
  debt_liquidated = cdps_liquidated['Supply'].sum()
  ether_liquidated = cdps_liquidated['Ether_Quantity'].sum()
  n_liquidate = cdps_liquidated.shape[0]
  cdps = cdps.reset_index(drop = True)

  liquidation_gain = ether_liquidated*price_ether_current - debt_liquidated*price_EBTC_previous
  airdrop_gain = price_LQTY_previous * quantity_LQTY_airdrop
  
  np.random.seed(2+index)
  shock_return = np.random.normal(0,sd_return)
  if index <= day:
   return_stability = initial_return*(1+shock_return)
  elif index<=month:
    #min function to rule out the large fluctuation caused by the large but temporary liquidation gain in a particular period
    return_stability = min(0.5, 365*(data.loc[index-day:index, 'liquidation_gain'].sum()+data.loc[index-day:index, 'airdrop_gain'].sum())/(price_EBTC_previous*stability_pool_previous))
  else:
    return_stability = (365/30)*(data.loc[index-month:index, 'liquidation_gain'].sum()+data.loc[index-month:index, 'airdrop_gain'].sum())/(price_EBTC_previous*stability_pool_previous)
  
  return[cdps, return_stability, debt_liquidated, ether_liquidated, liquidation_gain, airdrop_gain, n_liquidate]

"""Close Cdps"""

def close_cdps(cdps, index2, price_EBTC_previous):
  np.random.seed(208+index2)
  shock_closecdps = np.random.normal(0,sd_closecdps)
  n_cdps = cdps.shape[0]

  if index2 <= 240:
    number_closecdps = np.random.uniform(0,1)
  elif price_EBTC_previous >=1:
    number_closecdps = max(0, n_steady * (1+shock_closecdps))
  else:
    number_closecdps = max(0, n_steady * (1+shock_closecdps)) + beta*(1-price_EBTC_previous)*n_cdps
  
  number_closecdps = int(round(number_closecdps))
  
  random.seed(293+100*index2)
  drops = list(random.sample(range(len(cdps)), number_closecdps))
  cdps = cdps.drop(drops)
  cdps = cdps.reset_index(drop=True)
  if len(cdps) < number_closecdps:
    number_closecdps = -999

  return[cdps, number_closecdps]

"""Adjust Cdps"""

def adjust_cdps(cdps, index):
  issuance_EBTC_adjust = 0
  random.seed(57984-3*index)
  ratio = random.uniform(0,1)
  for i in range(0, cdps.shape[0]):
    random.seed(187*index + 3*i)
    working_cdp = cdps.iloc[i,:]
    p = random.uniform(0,1)
    check = (working_cdp['CR_current']-working_cdp['CR_initial'])/(working_cdp['CR_initial']*working_cdp['Rational_inattention'])

  #A part of the cdps are adjusted by adjusting debt
    if p >= ratio:
      if check<-1:
        working_cdp['Supply'] = working_cdp['Ether_Price']*working_cdp['Ether_Quantity']/working_cdp['CR_initial']
      if check>2:
        supply_new = working_cdp['Ether_Price']*working_cdp['Ether_Quantity']/working_cdp['CR_initial']
        issuance_EBTC_adjust = issuance_EBTC_adjust + rate_issuance * (supply_new - working_cdp['Supply'])
        working_cdp['Supply'] = supply_new
  #Another part of the cdps are adjusted by adjusting collaterals
    if p < ratio and (check < -1 or check > 2):
      working_cdp['Ether_Quantity'] = working_cdp['CR_initial']*working_cdp['Supply']/working_cdp['Ether_Price']
    
    cdps.loc[i] = working_cdp
  return[cdps, issuance_EBTC_adjust]

"""Open Cdps"""

def open_cdps(cdps, index1, price_EBTC_previous):
  random.seed(2019*index1)  
  issuance_EBTC_open = 0
  shock_opencdps = random.normalvariate(0,sd_opencdps)
  n_cdps = cdps.shape[0]

  if index1<=0:
    number_opencdps = initial_open
  elif price_EBTC_previous <=1 + rate_issuance:
    number_opencdps = max(0, n_steady * (1+shock_opencdps))
  else:
    number_opencdps = max(0, n_steady * (1+shock_opencdps)) + alpha*(price_EBTC_previous-rate_issuance-1)*n_cdps
  
  number_opencdps = int(round(float(number_opencdps)))

  for i in range(0, number_opencdps):
    price_ether_current = price_ether[index1]
    
    np.random.seed(2033 + index1 + i*i)
    CR_ratio = distribution_parameter1_CR + distribution_parameter2_CR * np.random.chisquare(df=distribution_parameter3_CR)
    
    np.random.seed(20 + 10 * i + index1)
    quantity_ether = np.random.gamma(distribution_parameter1_ether_quantity, scale=distribution_parameter2_ether_quantity)
    
    np.random.seed(209870- index1 + i*i)
    rational_inattention = np.random.gamma(distribution_parameter1_inattention, scale=distribution_parameter2_inattention)
    
    supply_cdp = price_ether_current * quantity_ether / CR_ratio
    issuance_EBTC_open = issuance_EBTC_open + rate_issuance * supply_cdp

    new_row = {"Ether_Price": price_ether_current, "Ether_Quantity": quantity_ether, 
               "CR_initial": CR_ratio, "Supply": supply_cdp, 
               "Rational_inattention": rational_inattention, "CR_current": CR_ratio}
    cdps = cdps.append(new_row, ignore_index=True)

  return[cdps, number_opencdps, issuance_EBTC_open]

"""# EBTC Market

Stability Pool
"""

def stability_update(stability_pool_previous, return_previous, index):
  np.random.seed(27+3*index)
  shock_stability = np.random.normal(0,sd_stability)
  natural_rate_current = natural_rate[index]
  if index <= month:
    stability_pool = stability_pool_previous* (drift_stability+shock_stability)* (1+ return_previous- natural_rate_current)**theta
  else:
    stability_pool = stability_pool_previous* (1+shock_stability)* (1+ return_previous- natural_rate_current)**theta
  return[stability_pool]

"""EBTC Price, liquidity pool, and redemption"""

def price_stabilizer(cdps, index, data, stability_pool, n_open):
  issuance_EBTC_stabilizer = 0
  redemption_fee = 0
  n_redempt = 0
  redempted = 0
  redemption_pool = 0  
#Calculating Price
  supply = cdps['Supply'].sum()
  np.random.seed(20*index)
  shock_liquidity = np.random.normal(0,sd_liquidity)
  liquidity_pool_previous = float(data['liquidity'][index-1])
  price_EBTC_previous = float(data['Price_EBTC'][index-1])
  price_EBTC_current= price_EBTC_previous*((supply-stability_pool)/(liquidity_pool_previous*(drift_liquidity+shock_liquidity)))**(1/delta)
  

#Liquidity Pool
  liquidity_pool = supply-stability_pool

#Stabilizer
  #Ceiling Arbitrageurs
  if price_EBTC_current > 1.1 + rate_issuance:
    #supply_current = sum(cdps['Supply'])
    supply_wanted=stability_pool+liquidity_pool_previous*(drift_liquidity+shock_liquidity)*((1.1+rate_issuance)/price_EBTC_previous)**delta
    supply_cdp = supply_wanted - supply

    CR_ratio = 1.1
    rational_inattention = 0.1
    quantity_ether = supply_cdp * CR_ratio / price_ether_current
    issuance_EBTC_stabilizer = rate_issuance * supply_cdp

    new_row = {"Ether_Price": price_ether_current, "Ether_Quantity": quantity_ether, "CR_initial": CR_ratio,
               "Supply": supply_cdp, "Rational_inattention": rational_inattention, "CR_current": CR_ratio}
    cdps = cdps.append(new_row, ignore_index=True)
    price_EBTC_current = 1.1 + rate_issuance
    #missing in the previous version  
    liquidity_pool = supply_wanted-stability_pool
    n_open=n_open+1
    

  #Floor Arbitrageurs
  if price_EBTC_current < 1 - rate_redemption:
    np.random.seed(30*index)
    shock_redemption = np.random.normal(0,sd_redemption)
    redemption_ratio = redemption_star * (1+shock_redemption)

    #supply_current = sum(cdps['Supply'])
    supply_target=stability_pool+liquidity_pool_previous*(drift_liquidity+shock_liquidity)*((1-rate_redemption)/price_EBTC_previous)**delta
    supply_diff = supply - supply_target
    if supply_diff < redemption_ratio * liquidity_pool:
      redemption_pool=supply_diff
      #liquidity_pool = liquidity_pool - redemption_pool
      price_EBTC_current = 1 - rate_redemption
    else:
      redemption_pool=redemption_ratio * liquidity_pool
      #liquidity_pool = (1-redemption_ratio)*liquidity_pool
      price_EBTC_current= price_EBTC_previous * (liquidity_pool/(liquidity_pool_previous*(drift_liquidity+shock_liquidity)))**(1/delta)
    
    #Shutting down the riskiest cdps
    cdps = cdps.sort_values(by='CR_current', ascending = True)
    quantity_working_cdp = cdps['Supply'][cdps.index[0]]
    redempted = quantity_working_cdp
    while redempted <= redemption_pool:
      cdps = cdps.drop(cdps.index[0])
      quantity_working_cdp = cdps['Supply'][cdps.index[0]]
      redempted = redempted + quantity_working_cdp
      n_redempt = n_redempt + 1
    
    #Residuals
    redempted = redempted - quantity_working_cdp
    residual = redemption_pool - redempted
    wk = cdps.index[0]
    cdps['Supply'][wk] = cdps['Supply'][wk] - residual
    cdps['Ether_Quantity'][wk] = cdps['Ether_Quantity'][wk] - residual/price_ether_current
    cdps['CR_current'][wk] = price_ether_current * cdps['Ether_Quantity'][wk] / cdps['Supply'][wk]

    #Redemption Fee
    redemption_fee = rate_redemption * redemption_pool
    

  cdps = cdps.reset_index(drop=True)
  return[price_EBTC_current, liquidity_pool, cdps, issuance_EBTC_stabilizer, redemption_fee, n_redempt, redemption_pool, n_open]

"""# LQTY Market"""



def LQTY_market(index, data):
  quantity_LQTY = (100000000/3)*(1-0.5**(index/period))
  np.random.seed(2+3*index)
  if index <= month: 
    price_LQTY_current = price_LQTY[index-1]
    annualized_earning = (index/month)**0.5*np.random.normal(200000000,500000)
  else:
    revenue_issuance = data.loc[index-month:index, 'issuance_fee'].sum()
    revenue_redemption = data.loc[index-month:index, 'redemption_fee'].sum()
    annualized_earning = 365*(revenue_issuance+revenue_redemption)/30
    #discountin factor to factor in the risk in early days
    discount=index/period
    price_LQTY_current = discount*PE_ratio*annualized_earning/LQTY_total_supply
  
  MC_LQTY_current = price_LQTY_current * quantity_LQTY
  return[price_LQTY_current, annualized_earning, MC_LQTY_current]

"""# Simulation Program"""

#Defining Initials
initials = {"Price_EBTC":[1.00], "Price_Ether":[price_ether_initial], "n_open":[initial_open], "n_close":[0], "n_liquidate": [0], "n_redempt":[0], 
            "n_cdps":[initial_open], "stability":[0], "liquidity":[0], "redemption_pool":[0],
            "supply_EBTC":[0],  "return_stability":[initial_return], "airdrop_gain":[0], "liquidation_gain":[0],  "issuance_fee":[0], "redemption_fee":[0],
            "price_LQTY":[price_LQTY_initial], "MC_LQTY":[0], "annualized_earning":[0]}
data = pd.DataFrame(initials)
cdps= pd.DataFrame({"Ether_Price":[], "Ether_Quantity":[], "CR_initial":[], 
              "Supply":[], "Rational_inattention":[], "CR_current":[]})
result_open = open_cdps(cdps, 0, data['Price_EBTC'][0])
cdps = result_open[0]
issuance_EBTC_open = result_open[2]
data.loc[0,'issuance_fee'] = issuance_EBTC_open * initials["Price_EBTC"][0]
data.loc[0,'supply_EBTC'] = cdps["Supply"].sum()
data.loc[0,'liquidity'] = 0.5*cdps["Supply"].sum()
data.loc[0,'stability'] = 0.5*cdps["Supply"].sum()

#Simulation Process
for index in range(1, n_sim):
#exogenous ether price input
  price_ether_current = price_ether[index]
  cdps['Ether_Price'] = price_ether_current
  price_EBTC_previous = data.loc[index-1,'Price_EBTC']
  price_LQTY_previous = data.loc[index-1,'price_LQTY']

#cdp liquidation & return of stability pool
  result_liquidation = liquidate_cdps(cdps, index, data)
  cdps = result_liquidation[0]
  return_stability = result_liquidation[1]
  debt_liquidated = result_liquidation[2]
  ether_liquidated = result_liquidation[3]
  liquidation_gain = result_liquidation[4]
  airdrop_gain = result_liquidation[5]
  n_liquidate = result_liquidation[6]

#close cdps
  result_close = close_cdps(cdps, index, price_EBTC_previous)
  cdps = result_close[0]
  n_close = result_close[1]
  #if n_close<0:
  #  break

#adjust cdps
  result_adjustment = adjust_cdps(cdps, index)
  cdps = result_adjustment[0]
  issuance_EBTC_adjust = result_adjustment[1]

#open cdps
  result_open = open_cdps(cdps, index, price_EBTC_previous)
  cdps = result_open[0]
  n_open = result_open[1]  
  issuance_EBTC_open = result_open[2]

#Stability Pool
  stability_pool = stability_update(data.loc[index-1,'stability'], return_stability, index)[0]

#Calculating Price, Liquidity Pool, and Redemption
  result_price = price_stabilizer(cdps, index, data, stability_pool, n_open)
  price_EBTC_current = result_price[0]
  liquidity_pool = result_price[1]
  cdps = result_price[2]
  issuance_EBTC_stabilizer = result_price[3]
  redemption_fee = result_price[4]
  n_redempt = result_price[5]
  redemption_pool = result_price[6]
  n_open=result_price[7]
  if liquidity_pool<0:
    break

#LQTY Market
  result_LQTY = LQTY_market(index, data)
  price_LQTY_current = result_LQTY[0]
  annualized_earning = result_LQTY[1]
  MC_LQTY_current = result_LQTY[2]

#Summary
  issuance_fee = price_EBTC_current * (issuance_EBTC_adjust + issuance_EBTC_open + issuance_EBTC_stabilizer)
  n_cdps = cdps.shape[0]
  supply_EBTC = cdps['Supply'].sum()
  if index >= month:
    price_LQTY.append(price_LQTY_current)

  new_row = {"Price_EBTC":float(price_EBTC_current), "Price_Ether":float(price_ether_current), "n_open":float(n_open), "n_close":float(n_close), 
             "n_liquidate":float(n_liquidate), "n_redempt": float(n_redempt), "n_cdps":float(n_cdps),
              "stability":float(stability_pool), "liquidity":float(liquidity_pool), "redemption_pool":float(redemption_pool), "supply_EBTC":float(supply_EBTC),
             "issuance_fee":float(issuance_fee), "redemption_fee":float(redemption_fee),
             "airdrop_gain":float(airdrop_gain), "liquidation_gain":float(liquidation_gain), "return_stability":float(return_stability), 
             "annualized_earning":float(annualized_earning), "MC_LQTY":float(MC_LQTY_current), "price_LQTY":float(price_LQTY_current)
             }
  data = data.append(new_row, ignore_index=True)
  if price_EBTC_current < 0:
    break

"""#**Exhibition**"""

data

def linevis(data, measure):
  fig = px.line(data, x=data.index/720, y=measure, title= measure+' dynamics')
  fig.show()

fig = make_subplots(specs=[[{"secondary_y": True}]])
fig.add_trace(
    go.Scatter(x=data.index/720, y=data['Price_EBTC'], name="EBTC Price"),
    secondary_y=False,
)
fig.add_trace(
    go.Scatter(x=data.index/720, y=data['Price_Ether'], name="Ether Price"),
    secondary_y=True,
)
fig.update_layout(
    title_text="Price Dynamics of EBTC and Ether"
)
fig.update_xaxes(tick0=0, dtick=1, title_text="Month")
fig.update_yaxes(title_text="EBTC Price", secondary_y=False)
fig.update_yaxes(title_text="Ether Price", secondary_y=True)
fig.show()

fig = make_subplots(specs=[[{"secondary_y": True}]])
fig.add_trace(
    go.Scatter(x=data.index/720, y=data['n_cdps'], name="Number of Cdps"),
    secondary_y=False,
)
fig.add_trace(
    go.Scatter(x=data.index/720, y=data['supply_EBTC'], name="EBTC Supply"),
    secondary_y=True,
)
fig.update_layout(
    title_text="Dynamics of Cdp Numbers and EBTC Supply"
)
fig.update_xaxes(tick0=0, dtick=1, title_text="Month")
fig.update_yaxes(title_text="Number of Cdps", secondary_y=False)
fig.update_yaxes(title_text="EBTC Supply", secondary_y=True)
fig.show()

fig = make_subplots(rows=2, cols=1)
fig.add_trace(
    go.Scatter(x=data.index/720, y=data['n_open'], name="Number of Cdps Opened", mode='markers'),
    row=1, col=1, secondary_y=False
)
fig.add_trace(
    go.Scatter(x=data.index/720, y=data['n_close'], name="Number of Cdps Closed", mode='markers'),
    row=2, col=1, secondary_y=False
)
fig.update_layout(
    title_text="Dynamics of Number of Cdps Opened and Closed"
)
fig.update_xaxes(tick0=0, dtick=1, title_text="Month")
fig.update_yaxes(title_text="Cdps Opened", row=1, col=1)
fig.update_yaxes(title_text="Cdps Closed", row=2, col=1)
fig.show()

fig = make_subplots(specs=[[{"secondary_y": True}]])
fig.add_trace(
    go.Scatter(x=data.index/720, y=data['n_liquidate'], name="Number of Liquidated Cdps", mode='markers'),
    secondary_y=False,
)
fig.add_trace(
    go.Scatter(x=data.index/720, y=data['n_redempt'], name="Number of Redempted Cdps", mode='markers'),
    secondary_y=False,
)
fig.update_layout(
    title_text="Dynamics of Number of Liquidated and Redempted Cdps"
)
fig.update_xaxes(tick0=0, dtick=1, title_text="Month")
fig.update_yaxes(title_text="Number of Liquidated Cdps", secondary_y=False)
fig.update_yaxes(title_text="Number of Redempted Cdps", secondary_y=True)
fig.show()

fig = make_subplots(specs=[[{"secondary_y": True}]])
fig.add_trace(
    go.Scatter(x=data.index/720, y=data['liquidity'], name="Liquidity Pool"),
    secondary_y=False,
)
fig.add_trace(
    go.Scatter(x=data.index/720, y=data['stability'], name="Stability Pool"),
    secondary_y=False,
)
fig.add_trace(
    go.Scatter(x=data.index/720, y=100*data['redemption_pool'], name="100*Redemption Pool"),
    secondary_y=False,
)
fig.add_trace(
    go.Scatter(x=data.index/720, y=data['return_stability'], name="Return of Stability Pool"),
    secondary_y=True,
)
fig.update_layout(
    title_text="Dynamics of Liquidity, Stability, Redemption Pools and Return of Stability Pool"
)
fig.update_xaxes(tick0=0, dtick=1, title_text="Month")
fig.update_yaxes(title_text="Size of Pools", secondary_y=False)
fig.update_yaxes(title_text="Return", secondary_y=True)
fig.show()

fig = make_subplots(specs=[[{"secondary_y": True}]])
fig.add_trace(
    go.Scatter(x=data.index/720, y=data['airdrop_gain'], name="Airdrop Gain"),
    secondary_y=False,
)
fig.add_trace(
    go.Scatter(x=data.index/720, y=data['liquidation_gain'], name="Liquidation Gain"),
    secondary_y=True,
)
fig.update_layout(
    title_text="Dynamics of Airdrop and Liquidation Gain"
)
fig.update_xaxes(tick0=0, dtick=1, title_text="Month")
fig.update_yaxes(title_text="Airdrop Gain", secondary_y=False)
fig.update_yaxes(title_text="Liquidation Gain", secondary_y=True)
fig.show()

fig = make_subplots(specs=[[{"secondary_y": True}]])
fig.add_trace(
    go.Scatter(x=data.index/720, y=data['issuance_fee'], name="Issuance Fee"),
    secondary_y=False,
)
fig.add_trace(
    go.Scatter(x=data.index/720, y=data['redemption_fee'], name="Redemption Fee"),
    secondary_y=True,
)
fig.update_layout(
    title_text="Dynamics of Issuance Fee and Redemption Fee"
)
fig.update_xaxes(tick0=0, dtick=1, title_text="Month")
fig.update_yaxes(title_text="Issuance Fee", secondary_y=False)
fig.update_yaxes(title_text="Redemption Fee", secondary_y=True)
fig.show()

#linevis(data, 'annualized_earning')

fig = make_subplots(specs=[[{"secondary_y": True}]])
fig.add_trace(
    go.Scatter(x=data.index/720, y=data['price_LQTY'], name="LQTY Price"),
    secondary_y=False,
)
fig.add_trace(
    go.Scatter(x=data.index/720, y=data['MC_LQTY'], name="LQTY Market Cap"),
    secondary_y=True,
)
fig.update_layout(
    title_text="Dynamics of the Price and Market Cap of LQTY"
)
fig.update_xaxes(tick0=0, dtick=1, title_text="Month")
fig.update_yaxes(title_text="LQTY Price", secondary_y=False)
fig.update_yaxes(title_text="LQTY Market Cap", secondary_y=True)
fig.show()

def cdp_histogram(measure):
  fig = px.histogram(cdps, x=measure, title='Distribution of '+measure, nbins=25)
  fig.show()

cdps

cdp_histogram('Ether_Quantity')
cdp_histogram('CR_initial')
cdp_histogram('Supply')
cdp_histogram('Rational_inattention')
cdp_histogram('CR_current')

import matplotlib.pyplot as plt
plt.plot(cdps["Ether_Quantity"])
plt.show()

plt.plot(cdps["CR_initial"])
plt.show()

plt.plot(cdps["Supply"])
plt.show()

plt.plot(cdps["CR_current"])
plt.show()

data.describe()

"""new policy function

issuance fee = redemption fee = base rate

#**Simulation with Policy Function**
"""

#Defining Initials
initials = {"Price_EBTC":[1.00], "Price_Ether":[price_ether_initial], "n_open":[initial_open], "n_close":[0], "n_liquidate": [0], "n_redempt":[0], 
            "n_cdps":[initial_open], "stability":[0], "liquidity":[0], "redemption_pool":[0],
            "supply_EBTC":[0],  "return_stability":[initial_return], "airdrop_gain":[0], "liquidation_gain":[0],  "issuance_fee":[0], "redemption_fee":[0],
            "price_LQTY":[price_LQTY_initial], "MC_LQTY":[0], "annualized_earning":[0], "base_rate":[base_rate_initial]}
data2 = pd.DataFrame(initials)
cdps2= pd.DataFrame({"Ether_Price":[], "Ether_Quantity":[], "CR_initial":[], 
              "Supply":[], "Rational_inattention":[], "CR_current":[]})
result_open = open_cdps(cdps2, 0, data2['Price_EBTC'][0])
cdps2 = result_open[0]
issuance_EBTC_open = result_open[2]
data2.loc[0,'issuance_fee'] = issuance_EBTC_open * initials["Price_EBTC"][0]
data2.loc[0,'supply_EBTC'] = cdps2["Supply"].sum()
data2.loc[0,'liquidity'] = 0.5*cdps2["Supply"].sum()
data2.loc[0,'stability'] = 0.5*cdps2["Supply"].sum()

#Simulation Process
for index in range(1, n_sim):
#exogenous ether price input
  price_ether_current = price_ether[index]
  cdps2['Ether_Price'] = price_ether_current
  price_EBTC_previous = data2.loc[index-1,'Price_EBTC']
  price_LQTY_previous = data2.loc[index-1,'price_LQTY']

#policy function determines base rate
  base_rate_current = 0.98 * data2.loc[index-1,'base_rate'] + 0.5*(data2.loc[index-1,'redemption_pool']/cdps2['Supply'].sum())
  rate_issuance = base_rate_current
  rate_redemption = base_rate_current

#cdp liquidation & return of stability pool
  result_liquidation = liquidate_cdps(cdps2, index, data2)
  cdps2 = result_liquidation[0]
  return_stability = result_liquidation[1]
  debt_liquidated = result_liquidation[2]
  ether_liquidated = result_liquidation[3]
  liquidation_gain = result_liquidation[4]
  airdrop_gain = result_liquidation[5]
  n_liquidate = result_liquidation[6]

#close cdps
  result_close = close_cdps(cdps2, index, price_EBTC_previous)
  cdps2 = result_close[0]
  n_close = result_close[1]
  #if n_close<0:
  #  break

#adjust cdps
  result_adjustment = adjust_cdps(cdps2, index)
  cdps2 = result_adjustment[0]
  issuance_EBTC_adjust = result_adjustment[1]

#open cdps
  result_open = open_cdps(cdps2, index, price_EBTC_previous)
  cdps2 = result_open[0]
  n_open = result_open[1]  
  issuance_EBTC_open = result_open[2]

#Stability Pool
  stability_pool = stability_update(data2.loc[index-1,'stability'], return_stability, index)[0]

#Calculating Price, Liquidity Pool, and Redemption
  result_price = price_stabilizer(cdps2, index, data2, stability_pool, n_open)
  price_EBTC_current = result_price[0]
  liquidity_pool = result_price[1]
  cdps2 = result_price[2]
  issuance_EBTC_stabilizer = result_price[3]
  redemption_fee = result_price[4]
  n_redempt = result_price[5]
  redemption_pool = result_price[6]
  n_open=result_price[7]
  if liquidity_pool<0:
    break

#LQTY Market
  result_LQTY = LQTY_market(index, data2)
  price_LQTY_current = result_LQTY[0]
  annualized_earning = result_LQTY[1]
  MC_LQTY_current = result_LQTY[2]

#Summary
  issuance_fee = price_EBTC_current * (issuance_EBTC_adjust + issuance_EBTC_open + issuance_EBTC_stabilizer)
  n_cdps = cdps2.shape[0]
  supply_EBTC = cdps2['Supply'].sum()
  if index >= month:
    price_LQTY.append(price_LQTY_current)

  new_row = {"Price_EBTC":float(price_EBTC_current), "Price_Ether":float(price_ether_current), "n_open":float(n_open), "n_close":float(n_close), 
             "n_liquidate":float(n_liquidate), "n_redempt": float(n_redempt), "n_cdps":float(n_cdps),
              "stability":float(stability_pool), "liquidity":float(liquidity_pool), "redemption_pool":float(redemption_pool), "supply_EBTC":float(supply_EBTC),
             "issuance_fee":float(issuance_fee), "redemption_fee":float(redemption_fee),
             "airdrop_gain":float(airdrop_gain), "liquidation_gain":float(liquidation_gain), "return_stability":float(return_stability), 
             "annualized_earning":float(annualized_earning), "MC_LQTY":float(MC_LQTY_current), "price_LQTY":float(price_LQTY_current), 
             "base_rate":float(base_rate_current)}
  data2 = data2.append(new_row, ignore_index=True)
  if price_EBTC_current < 0:
    break

data2

"""#**Exhibition Part 2**"""

fig = make_subplots(specs=[[{"secondary_y": True}]])
fig.add_trace(
    go.Scatter(x=data.index/720, y=data['Price_EBTC'], name="EBTC Price"),
    secondary_y=False,
)
fig.add_trace(
    go.Scatter(x=data.index/720, y=data['Price_Ether'], name="Ether Price"),
    secondary_y=True,
)
fig.add_trace(
    go.Scatter(x=data2.index/720, y=data2['Price_EBTC'], name="EBTC Price New", line = dict(dash='dot')),
    secondary_y=False,
)
fig.update_layout(
    title_text="Price Dynamics of EBTC and Ether"
)
fig.update_xaxes(tick0=0, dtick=1, title_text="Month")
fig.update_yaxes(title_text="EBTC Price", secondary_y=False)
fig.update_yaxes(title_text="Ether Price", secondary_y=True)
fig.show()

fig = make_subplots(specs=[[{"secondary_y": True}]])
fig.add_trace(
    go.Scatter(x=data.index/720, y=data['n_cdps'], name="Number of Cdps"),
    secondary_y=False,
)
fig.add_trace(
    go.Scatter(x=data.index/720, y=data['supply_EBTC'], name="EBTC Supply"),
    secondary_y=True,
)
fig.add_trace(
    go.Scatter(x=data2.index/720, y=data2['n_cdps'], name="Number of Cdps New", line = dict(dash='dot')),
    secondary_y=False,
)
fig.add_trace(
    go.Scatter(x=data2.index/720, y=data2['supply_EBTC'], name="EBTC Supply New", line = dict(dash='dot')),
    secondary_y=True,
)
fig.update_layout(
    title_text="Dynamics of Cdp Numbers and EBTC Supply"
)
fig.update_xaxes(tick0=0, dtick=1, title_text="Month")
fig.update_yaxes(title_text="Number of Cdps", secondary_y=False)
fig.update_yaxes(title_text="EBTC Supply", secondary_y=True)
fig.show()

fig = make_subplots(rows=2, cols=2)
fig.add_trace(
    go.Scatter(x=data.index/720, y=data['n_open'], name="Number of Cdps Opened", mode='markers'),
    row=1, col=1, secondary_y=False
)
fig.add_trace(
    go.Scatter(x=data.index/720, y=data['n_close'], name="Number of Cdps Closed", mode='markers'),
    row=2, col=1, secondary_y=False
)
fig.add_trace(
    go.Scatter(x=data2.index/720, y=data2['n_open'], name="Number of Cdps Opened New", mode='markers'),
    row=1, col=2, secondary_y=False
)
fig.add_trace(
    go.Scatter(x=data2.index/720, y=data2['n_close'], name="Number of Cdps Closed New", mode='markers'),
    row=2, col=2, secondary_y=False
)
fig.update_layout(
    title_text="Dynamics of Number of Cdps Opened and Closed"
)
fig.update_xaxes(tick0=0, dtick=1, title_text="Month")
fig.update_yaxes(title_text="Cdps Opened", row=1, col=1)
fig.update_yaxes(title_text="Cdps Closed", row=2, col=1)
fig.show()

fig = make_subplots(rows=2, cols=1)
fig.add_trace(
    go.Scatter(x=data.index/720, y=data['n_liquidate'], name="Number of Liquidated Cdps"),
    row=1, col=1, secondary_y=False
)
fig.add_trace(
    go.Scatter(x=data.index/720, y=data['n_redempt'], name="Number of Redempted Cdps"),
    row=2, col=1, secondary_y=False
)
fig.add_trace(
    go.Scatter(x=data2.index/720, y=data2['n_liquidate'], name="Number of Liquidated Cdps New", line = dict(dash='dot')),
    row=1, col=1, secondary_y=False
)
fig.add_trace(
    go.Scatter(x=data2.index/720, y=data2['n_redempt'], name="Number of Redempted Cdps New", line = dict(dash='dot')),
    row=2, col=1, secondary_y=False
)
fig.update_layout(
    title_text="Dynamics of Number of Liquidated and Redempted Cdps"
)
fig.update_xaxes(tick0=0, dtick=1, title_text="Month")
fig.update_yaxes(title_text="Cdps Liquidated", row=1, col=1)
fig.update_yaxes(title_text="Cdps Redempted", row=2, col=1)
fig.show()

fig = make_subplots(specs=[[{"secondary_y": True}]])
fig.add_trace(
    go.Scatter(x=data.index/720, y=data['liquidity'], name="Liquidity Pool"),
    secondary_y=False,
)
fig.add_trace(
    go.Scatter(x=data.index/720, y=data['stability'], name="Stability Pool"),
    secondary_y=False,
)
fig.add_trace(
    go.Scatter(x=data.index/720, y=100*data['redemption_pool'], name="100*Redemption Pool"),
    secondary_y=False,
)
fig.add_trace(
    go.Scatter(x=data2.index/720, y=data2['liquidity'], name="Liquidity Pool New", line = dict(dash='dot')),
    secondary_y=False,
)
fig.add_trace(
    go.Scatter(x=data2.index/720, y=data2['stability'], name="Stability Pool New", line = dict(dash='dot')),
    secondary_y=False,
)
fig.add_trace(
    go.Scatter(x=data2.index/720, y=100*data2['redemption_pool'], name="100*Redemption Pool New", line = dict(dash='dot')),
    secondary_y=False,
)
fig.update_layout(
    title_text="Dynamics of Liquidity, Stability, Redemption Pools and Return of Stability Pool"
)
fig.update_xaxes(tick0=0, dtick=1, title_text="Month")
fig.update_yaxes(title_text="Size of Pools", secondary_y=False)
fig.show()

fig = make_subplots(specs=[[{"secondary_y": True}]])
fig.add_trace(
    go.Scatter(x=data.index/720, y=data['return_stability'], name="Return of Stability Pool"),
    secondary_y=False,
)
fig.add_trace(
    go.Scatter(x=data2.index/720, y=data2['return_stability'], name="Return of Stability Pool New", line = dict(dash='dot')),
    secondary_y=False,
)
fig.update_layout(
    title_text="Dynamics of Liquidity, Stability, Redemption Pools and Return of Stability Pool"
)
fig.update_xaxes(tick0=0, dtick=1, title_text="Month")
fig.update_yaxes(title_text="Return", secondary_y=False)
fig.show()

fig = make_subplots(specs=[[{"secondary_y": True}]])
fig.add_trace(
    go.Scatter(x=data.index/720, y=data['airdrop_gain'], name="Airdrop Gain"),
    secondary_y=False,
)
fig.add_trace(
    go.Scatter(x=data.index/720, y=data['liquidation_gain'], name="Liquidation Gain"),
    secondary_y=True,
)
fig.add_trace(
    go.Scatter(x=data2.index/720, y=data2['airdrop_gain'], name="Airdrop Gain New", line = dict(dash='dot')),
    secondary_y=False,
)
fig.add_trace(
    go.Scatter(x=data2.index/720, y=data2['liquidation_gain'], name="Liquidation Gain New", line = dict(dash='dot')),
    secondary_y=True,
)
fig.update_layout(
    title_text="Dynamics of Airdrop and Liquidation Gain"
)
fig.update_xaxes(tick0=0, dtick=1, title_text="Month")
fig.update_yaxes(title_text="Airdrop Gain", secondary_y=False)
fig.update_yaxes(title_text="Liquidation Gain", secondary_y=True)
fig.show()

fig = make_subplots(rows=2, cols=1)
fig.add_trace(
    go.Scatter(x=data.index/720, y=data['issuance_fee'], name="Issuance Fee"),
    row=1, col=1
)
fig.add_trace(
    go.Scatter(x=data.index/720, y=data['redemption_fee'], name="Redemption Fee"),
    row=2, col=1
)
fig.add_trace(
    go.Scatter(x=data2.index/720, y=data2['issuance_fee'], name="Issuance Fee New", line = dict(dash='dot')),
    row=1, col=1
)
fig.add_trace(
    go.Scatter(x=data2.index/720, y=data2['redemption_fee'], name="Redemption Fee New", line = dict(dash='dot')),
    row=2, col=1
)
fig.update_layout(
    title_text="Dynamics of Issuance Fee and Redemption Fee"
)
fig.update_xaxes(tick0=0, dtick=1, title_text="Month")
fig.update_yaxes(title_text="Issuance Fee", secondary_y=False, row=1, col=1)
fig.update_yaxes(title_text="Redemption Fee", secondary_y=False, row=2, col=1)
fig.show()

fig = make_subplots(specs=[[{"secondary_y": True}]])
fig.add_trace(
    go.Scatter(x=data.index/720, y=data['annualized_earning'], name="Annualized Earning"),
    secondary_y=False,
)
fig.add_trace(
    go.Scatter(x=data2.index/720, y=data2['annualized_earning'], name="Annualized Earning New", line = dict(dash='dot')),
    secondary_y=False,
)
fig.update_layout(
    title_text="Dynamics of Annualized Earning"
)
fig.update_xaxes(tick0=0, dtick=1, title_text="Month")
fig.update_yaxes(title_text="Annualized Earning", secondary_y=False)
fig.show()

fig = make_subplots(specs=[[{"secondary_y": True}]])
fig.add_trace(
    go.Scatter(x=data.index/720, y=data['price_LQTY'], name="LQTY Price"),
    secondary_y=False,
)
fig.add_trace(
    go.Scatter(x=data.index/720, y=data['MC_LQTY'], name="LQTY Market Cap"),
    secondary_y=True,
)
fig.add_trace(
    go.Scatter(x=data2.index/720, y=data2['price_LQTY'], name="LQTY Price New", line = dict(dash='dot')),
    secondary_y=False,
)
fig.add_trace(
    go.Scatter(x=data2.index/720, y=data2['MC_LQTY'], name="LQTY Market Cap New", line = dict(dash='dot')),
    secondary_y=True,
)
fig.update_layout(
    title_text="Dynamics of the Price and Market Cap of LQTY"
)
fig.update_xaxes(tick0=0, dtick=1, title_text="Month")
fig.update_yaxes(title_text="LQTY Price", secondary_y=False)
fig.update_yaxes(title_text="LQTY Market Cap", secondary_y=True)
fig.show()

fig = make_subplots(specs=[[{"secondary_y": True}]])
fig.add_trace(
    go.Scatter(x=data.index/720, y=[0.01] * n_sim, name="Base Rate"),
    secondary_y=False,
)
fig.add_trace(
    go.Scatter(x=data2.index/720, y=data2['base_rate'], name="Base Rate New"),
    secondary_y=False,
)
fig.update_layout(
    title_text="Dynamics of Issuance Fee and Redemption Fee"
)
fig.update_xaxes(tick0=0, dtick=1, title_text="Month")
fig.update_yaxes(title_text="Issuance Fee", secondary_y=False)
fig.update_yaxes(title_text="Redemption Fee", secondary_y=True)
fig.show()

def cdp2_histogram(measure):
  fig = px.histogram(cdps2, x=measure, title='Distribution of '+measure, nbins=25)
  fig.show()

cdp2_histogram('Ether_Quantity')
cdp2_histogram('CR_initial')
cdp2_histogram('Supply')
cdp2_histogram('Rational_inattention')
cdp2_histogram('CR_current')