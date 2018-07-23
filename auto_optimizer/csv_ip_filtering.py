"""
CSV IP Filtering

Accepts CSV file input from Voluum,
uses a dataframe to break out conversion and cost data per IP address,
then processess IP list into /16 blocks to cut and keep based on performance
def get_sixteen_addr(ip):
    print(ip)
    ip = str(ip)
    return ip.split('.')[0] + ip.split('.')[1] + '.0.0'

df.groupby(get_sixteen_addr, axis=0)
df.groupby('IP')

TrafficHunt Us is $10,933 spend for last 30 days

"""

from __future__ import print_function

from ipwhois import IPWhois
import datetime
from pprint import pprint

import numpy
import pandas as pd

START_TIME = datetime.datetime.now()
# Read exported Voluum IP data from CSV
df = pd.read_table("exoclick-us-push-ron.csv", sep=",")
IP_ISP_LIST = {}
IP_LIST = {}
# Sort dataframe by IP address
df = df.drop(columns=['Visits', 'Clicks', 'Revenue', 'Custom conversion 1', 'Profit', 'CPV', 'CTR', 'CR', 'CV', 'ROI', 'EPV', 'AP', 'ECPA'])
df = df.sort_values(['IP'])


# Iterate through dataframe and add conversion and cost data to /24 cidr blocks
for entry in df.values:
    sixteen_cidr = entry[0].split(
        '.')[0] + '.' + entry[0].split('.')[1] + '.0.0'
    ip_conversions = entry[1]
    ip_cost = entry[2]
    IP_ISP_LIST.setdefault(sixteen_cidr, [])
    IP_ISP_LIST[sixteen_cidr].append((ip_conversions, ip_cost))

for ip in IP_ISP_LIST.keys():
    try:
        obj = IPWhois(ip)
        results = obj.lookup_rdap(depth=1)
        pprint(results['asn_description'].split('- ')[1])
    except:
        print('NA')
    #pprint(results['asn_description'])

END_TIME = datetime.datetime.now()

def analyze_placements(ip_list, target_ecpa, simulate):
    # Take all data in each block and calculate sums for costs and
    # conversions, then figure ecpa and judge whether placement should be cut
    to_cut_placements = []
    no_cr_under_cost_placements = []
    no_cr_over_cost_placements = []
    #target_ecpa = 0.10
    # for target_ecpa in target_ecpas:
    keep_total_cost = 0
    keep_total_conversions = 0
    cut_total_cost = 0
    cut_total_conversions = 0
    total_cost = 0
    total_conversions = 0
    for block in ip_list.keys():
        conversions = 0.0
        cost = 0.0
        for row in ip_list[block]:
            conversions += row[0]
            cost += row[1]
        #print(block, conversions, cost)
        if conversions == 0 and cost > 0.50:
            to_cut_placements.append((block, conversions, cost, 'No Conversions'))
            no_cr_over_cost_placements.append(
                (block, conversions, cost, 'No Conversions'))
        if conversions > 0:
            ecpa = cost / conversions
            if ecpa > target_ecpa:
                to_cut_placements.append((block, conversions, cost, ecpa))
    cut_total_cost = 0
    cut_total_conversions = 0
    for block in to_cut_placements:
        cut_total_cost += block[2]
        cut_total_conversions += block[1]
    if cut_total_cost > 0 and cut_total_conversions > 0:
        cut_average_cpa = cut_total_cost / cut_total_conversions
    else:
        cut_average_cpa = 1
    keep_placements = []
    for block in ip_list.keys():
        conversions = 0.0
        cost = 0.0
        for row in ip_list[block]:
            conversions += row[0]
            cost += row[1]
        #print(block, conversions, cost)
        if conversions == 0 and cost < 0.50:
            keep_placements.append(
                (block, conversions, cost, 'No Conversions'))
            no_cr_under_cost_placements.append(
                (block, conversions, cost, 'No Conversions'))
        if conversions > 0:
            ecpa = cost / conversions
            if ecpa <= target_ecpa:
                keep_placements.append((block, conversions, cost, ecpa))
    keep_total_cost = 0
    keep_total_conversions = 0
    for block in keep_placements:
        keep_total_cost += block[2]
        keep_total_conversions += block[1]
    if keep_total_cost > 0 and keep_total_conversions > 0:
        keep_average_cpa = keep_total_cost / keep_total_conversions
    else:
        keep_average_cpa = 1
    no_cr_under_cost = 0
    no_cr_over_cost = 0
    for block in no_cr_under_cost_placements:
        no_cr_under_cost += block[2]
    for block in no_cr_over_cost_placements:
        no_cr_over_cost += block[2]
    total_cost = cut_total_cost + keep_total_cost
    total_conversions = cut_total_conversions + keep_total_conversions
    cost_reduction = (cut_total_cost / total_cost * 100)
    conversion_reduction = (cut_total_conversions / total_conversions * 100)
    reduction_spread = (cost_reduction - conversion_reduction)
    print('===================================')
    print('Stats for ECPA: ' + str(target_ecpa))
    print('Keep: Cost - Conversion - Average CPA')
    print(keep_total_cost, keep_total_conversions, keep_average_cpa)
    print('Cut: Cost - Conversion - Average CPA')
    print(cut_total_cost, cut_total_conversions, cut_average_cpa)
    print('Total: Cost - Conversion:')
    print(total_cost, total_conversions)
    print('% Cost Reduction:')
    print(cost_reduction)
    print('% Conversion Reduction:')
    print(conversion_reduction)
    print('Spread Between Cost and Conversion:')
    print(reduction_spread)
    print('Cost of Placements with no Conversions and under cost:')
    print(no_cr_under_cost)
    print('Cost of Placements with no Conversions and over cost:')
    print(no_cr_over_cost)
    if simulate == False:
        return to_cut_placements


TARGET_ECPAS = numpy.arange(0.01, 0.20, 0.01)
for target in TARGET_ECPAS:
    try:
        analyze_placements(IP_ISP_LIST, target, True)
    except BaseException:
        print('Failed')


print(START_TIME)
print(END_TIME)

# Exoclick x.x.0.0/24
CUT_PLACEMENTS = analyze_placements(IP_ISP_LIST, 0.19, False)
CUT_PLACEMENTS_SIXTEEN_BLOCK = []
for placement in CUT_PLACEMENTS:
    # Traffic Stars /16, one per line
    #CUT_PLACEMENTS_SIXTEEN_BLOCK.append(
    #    placement[0].split('.')[0] +
    #    '.' +
    #    placement[0].split('.')[1] +
    #    '.0.0/16')
    # x.x.0.0-x.x.255.255 - TrafficHunt
    CUT_PLACEMENTS_SIXTEEN_BLOCK.append(placement[0] + '-' + placement[0].split('.')[0] + '.' + placement[0].split('.')[1] + '.255.255')
    #cut_placements_twenty.append(placement[0].split('.')[0] + '.' + placement[0].split('.')[1] + '.0.0')

