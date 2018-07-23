#!bin/env/python2.7
# -*- coding: utf-8 -*-
"""
stripe_duplicate_watcher
Module which retrieves all customers from stripe,
 generates an md5 hash of their payment card, 
 finds duplicate cards, and 
 removes all subscriptions w/ that card for that customer
"""

from __future__ import print_function

import md5

import stripe

stripe.api_key = "sk_live_vwnQe2VvOwrXOQmsE5YOAfzR"
card_list = []
customers = {}
customer_id = None
i = 0
while len(card_list) < 650 and i < 20:
    i = i + 1
    if customer_id:
        stripe_list = stripe.Customer.list(
            limit=100, starting_after=customer_id)
    else:
        stripe_list = stripe.Customer.list(limit=100)
    for cust in stripe_list['data']:
        card_last4 = str(cust['sources']['data'][0]['last4'])
        card_month = str(cust['sources']['data'][0]['exp_month'])
        card_year = str(cust['sources']['data'][0]['exp_year'])
        card_brand = str(cust['sources']['data'][0]['brand'])
        card_country = str(cust['sources']['data'][0]['country'])
        card_type = str(cust['sources']['data'][0]['funding'])
        m = md5.new()
        m.update(
            card_last4 +
            card_month +
            card_year +
            card_brand +
            card_country +
            card_type)
        card_hash = m.hexdigest()
        print(card_hash)
        card_list.append(card_hash)
        customer_id = cust['id']
        customers[customer_id] = card_hash
    print(customer_id)


print(card_list)
duplicate_list = []


def FindDuplicates(in_list):
    unique = set(in_list)
    for each in unique:
        count = in_list.count(each)
        if count > 1:
            print('There are duplicates in this list')
            duplicate_list.append(each)
    print('There are no duplicates in this list')


FindDuplicates(card_list)
print(duplicate_list)
print(len(duplicate_list))
duplicate_customer_list = []
for customer in customers:
    if customers[customer] in duplicate_list:
        print(customer)
        duplicate_customer_list.append(customer)


print(duplicate_customer_list)


#for customer in duplicate_customer_list:
for customer in customers:
    cust = stripe.Customer.retrieve(customer)
    sub_id = cust['subscriptions']['data']
    if len(sub_id) == 0:
        print('len 0')
    if len(sub_id) == 1:
        print('len 1')
        subr_id = sub_id[0]['items']['data'][0]['subscription']
        print(subr_id)
        sub_plan = stripe.Subscription.retrieve(subr_id)
        sub_plan.delete()
    if len(sub_id) == 2:
        print('len 2')
        subr_id = sub_id[0]['items']['data'][0]['subscription']
        print(subr_id)
        sub_plan = stripe.Subscription.retrieve(subr_id)
        sub_plan.delete()
        subr_id = sub_id[1]['items']['data'][0]['subscription']
        print(subr_id)
        sub_plan = stripe.Subscription.retrieve(subr_id)
        sub_plan.delete()

