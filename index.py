#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Mar 28 10:24:42 2020

@author: himanshu teotia
"""

from spacy import displacy
import spacy
import re
import datetime
from bs4 import BeautifulSoup
import json
import codecs
print("spacy version", spacy.__version__)
nlp = spacy.load("en_core_web_lg")

# load the html file
f = codecs.open("bankstatement.html", 'r')
html_doc = f.read()

# readd the file
soup = BeautifulSoup(html_doc, 'html.parser')
data = soup.find_all("p")

bank_statement_details = {
    "name_of_customer": "",
    "address_of_customer": "",
    "bank_account_number": "",
    "statement_date": "",
    "transactions": []
}

transaction = {   # this object will track the individual transaction
    "date": "",
    "description": "",
    "transaction_type": "",
    "amount": ""
}

array_of_sentences = []
# # # configs
date_values = ["ACCOUNT SUMMARY", "ACCOUNT DETAILS"]
date_filters = r"(" + "|".join(date_values) + ")"

transaction_values = ["Point-of-Sale Transaction", "Quick Cheque Deposit"]
transaction_description_filters = r"(" + "|".join(transaction_values) + ")"

transaction_start = False
start_transaction= ["CURRENCY: SINGAPORE DOLLAR"]
stop_transaction = ["Total"]

def regex_to_check_account_number(text):
    return bool(re.match(r"[0-9]{2}-[0-9]{6}-[0-9]{1}", text))

def remove_special_characters(text):
    return re.sub(r"[\|\*<>\(\)]", "", text)

def count_matches(pattern, thestring):
    return re.subn(pattern, '', thestring)[1]

# this function is to match the amounts those have more then one dot(.) like (1.254.12)
def replace_multiple_dots(text):
    # to check only for number, comma and periods
    pattern = re.compile("^[0-9,.]*$")
    if bool(re.match(pattern, text)):
        periods_pattern = re.compile(r"\.")
        if count_matches(periods_pattern, text) > 1:
            return text.replace('.', ',', 1)
    return text

def print_entities(ents):
    for ent in ents:
        print("[")
        print("Label : ", ent.label_)
        print("Entity : ", ent.text)
        print("]")

def check_month_abbv(text):
    match = re.search(r"\b[0-9]{1,2}\s[A-Z]{1}[a-z]{2}\b", text)
    if bool(match):
        replaced_string = text.replace(text[match.start(
        )+3:match.end()], datetime.datetime.strptime(text[match.start()+3:match.end()], '%b').strftime('%B'))
        replaced_string = replaced_string.replace(text[match.start():match.start(
        )+2], text[match.start():match.start()+2] + "" + get_strftime(int(text[match.start():match.start()+2])))
        return replaced_string
    return text

def get_strftime(day):
    if 4 <= day <= 20 or 24 <= day <= 30:
        suffix = "th"
    else:
        suffix = ["st", "nd", "rd"][day % 10 - 1]
    return suffix

def set_account_name(label, text):
    if label == "PERSON" and not bank_statement_details["name_of_customer"]:
        bank_statement_details["name_of_customer"] = text

def set_address(label, text):
    if label == "ORG" and not bank_statement_details["address_of_customer"] and bank_statement_details["name_of_customer"]:
        bank_statement_details["address_of_customer"] = text

def set_account_number(label, text):
    if label == "CARDINAL" and not bank_statement_details["bank_account_number"] and regex_to_check_account_number(text):
        bank_statement_details["bank_account_number"] = text

def set_date(label, text):
    if label == "DATE" and not bank_statement_details["statement_date"]:
        bank_statement_details["statement_date"] = text

def set_transactions(label, text, sentence):
    global transaction_start
    if transaction_start:
        if label == "CARDINAL":
            check_and_set_transaction("amount", text)
        if label == "DATE":
            check_and_set_transaction("date", text)
        if label == "ORG":
            check_and_set_transaction("description", text)
        if bool(re.match(transaction_description_filters, sentence)):
            if bool(re.search("Deposit",sentence)):
                check_and_set_transaction("transaction_type", "DEPOSIT")
            else:
                check_and_set_transaction("transaction_type", "WITHDRAWAL")

# set the transaction and push each transaction in global object
def check_and_set_transaction(type_, value):
    global transaction
    global bank_statement_details
    if not transaction[type_]:
        transaction[type_] = value
    else:
        bank_statement_details["transactions"].append(transaction)
        transaction = {   # this object will track the individual transaction
            "date": "",
            "description": "",
            "transaction_type": "",
            "amount": ""
        }
        transaction[type_] = value

def main():
    sentence = ""
    global transaction_start
    for i in data:
        spans = i.find_all("span")
        if sentence:
            sentence = check_month_abbv(sentence)
            sentence = remove_special_characters(sentence)
            sentence = replace_multiple_dots(sentence)
            if sentence in stop_transaction:
                transaction_start = False
            doc = nlp(sentence)
            array_of_sentences.append(sentence)
            if transaction_start and len(doc.ents) == 0:
                set_transactions("", "", sentence)
            for ent in doc.ents:
                set_account_name(ent.label_, ent.text)
                set_account_number(ent.label_, ent.text)
                set_address(ent.label_, ent.text)
                if bool(re.match(date_filters, sentence)):
                    set_date(ent.label_, ent.text)
                set_transactions(ent.label_, ent.text, sentence)
                if sentence in start_transaction:
                    transaction_start = True          
        sentence = ""
        for j in spans:
            sentence = sentence + j.get_text()


main()
print(bank_statement_details)
