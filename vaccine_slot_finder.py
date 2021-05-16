#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
This Python Script will send WhatsApp messages only if it is able to find the vaccine slot in the district of the user.
It uses Twilio to send the message which charges user for the pay per use basis.

Twilio has a word limit of 1600 words, hence the code is optimized to send the maximum information of vaccination centers inside
the district within a single WhatsApp message. Hence, all the center information of district are sent on whatsapp in a cost optimized way.

__author__ : "Vinayak Sharda"
__version__ = "1.0.1"
__maintainer__ = "Vinayak Sharda"
__status__ = "Development"
"""

import time
import subprocess
import sys

def install(package):
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])

try:
    from twilio.rest import Client
except ImportError:
    print('Twilio is not installed, installing it now!')
    install('twilio')

try:
    import requests
except ImportError:
    print('Requests is not installed, installing it now!')
    install('requests')

from twilio.rest import Client
import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)


def call_cowin_api(type_of_api, **api_args):
    try:
        if type_of_api == 'geo':
            url = "https://cdn-api.co-vin.in/api/v2/admin/location/" + api_args['geography'] + "/" + api_args['geo_id']
        else:
            url = "https://cdn-api.co-vin.in/api/v2/appointment/sessions/public/findByDistrict?district_id=" + str(
                api_args['district_id']) + "&" + "date=" + api_args['date']

        param = {"Accept-Language": "hi_IN"}
        user_agent = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}
        response = requests.get(url=url, params=param, verify=False, headers=user_agent)

        if response.status_code == 200:
            return response.json()

    except requests.exceptions.RequestException as ex:
        print("Please find the exception here", ex)


def search_state_id(state_name):
    try:
        all_state_dict = call_cowin_api(type_of_api='geo', geography='states', geo_id="")
        for each_state_info in all_state_dict['states']:
            if each_state_info['state_name'] == state_name:
                print("State Found")
                return each_state_info['state_id']

    except Exception as ex:
        print(ex)


def search_district_id(given_state_id, district_name):
    try:
        all_districts_in_state = call_cowin_api(type_of_api='geo', geography='districts', geo_id=str(given_state_id))
        for each_district_info in all_districts_in_state['districts']:
            if each_district_info['district_name'] == district_name:
                print("District Found")
                return each_district_info['district_id']

    except Exception as ex:
        print(ex)


def lookup_vaccine_slot(given_district_id, given_date, given_age):
    try:
        session_dict = call_cowin_api(type_of_api='session', district_id=given_district_id, date=str(given_date))
        return session_dict
    except Exception as ex:
        print(ex)


def trigger_whatsapp_notification(center_details, twilio_client_id, twilio_authentication_token, twilio_whatsapp_number, user_whatsapp_number):
    try:
        client = Client(twilio_client_id, twilio_authentication_token)
        from_details = 'whatsapp:' + twilio_whatsapp_number
        to_details = 'whatsapp:' + user_whatsapp_number
        client.messages.create(body=str(center_details), from_=from_details,
                               to=to_details)
    except Exception as ex:
        print(ex)


# User Inputs Here.
state = 'Maharashtra'  # Enter State of India For eg "Maharashtra"
district = 'Pune'  # Enter District  of State Chosen For eg "Pune"
date = "17-05-2021"  # Enter Date of Slot to be chosen for vaccination. For eg "16-05-2021"
age_limit = 18  # Enter Age bracket of vaccination ie 18 or 45.
choose_dosage = "first"  # Enter the dose type if it is "first" or "second" in words.

twilio_client_id = ''  # Enter from twilio dashboard
twilio_authentication_token = ''  # Enter from twilio dashboard
twilio_whatsapp_number = ''  # Enter from twilio dashboard
user_whatsapp_number = ''  # Enter WhatsApp number of user with +91 format.

# User Inputs Ends Here.

while True:
    state_id = search_state_id(state)
    district_id = search_district_id(state_id, district)

    if choose_dosage == 'first':
        look_up_dosage_detail = 'available_capacity_dose1'
    else:
        look_up_dosage_detail = 'available_capacity_dose2'

    all_center_details = lookup_vaccine_slot(district_id, date, age_limit)
    active_centers_as_per_request = []
    notifications = []

    if len(all_center_details) >= 1:
        for each_sessions in all_center_details['sessions']:
            if int(each_sessions['min_age_limit']) == age_limit and int(each_sessions[look_up_dosage_detail]) > 0:
                active_centers_as_per_request.append(
                    {'name': each_sessions['name'], 'vaccine': each_sessions['vaccine'],
                     'pincode': each_sessions['pincode'], 'age limit': each_sessions['min_age_limit'],
                     'slots': each_sessions['slots'],
                     'capacity_of_selected_dose': each_sessions[look_up_dosage_detail]})
    try:
        if len(active_centers_as_per_request) > 0:
            print("Slot Found")
            # print(active_centers_as_per_request)
            for center_details in active_centers_as_per_request:
                slot_details = "Center: {} , Zip: {} , Vaccine: {}, Capacity: {},  Slots: {}".format(center_details['name'], center_details['pincode'],center_details['vaccine'], center_details['capacity_of_selected_dose'], ", ".join(center_details['slots']))
                notifications.append(slot_details)

            notification_message = "\n\n".join(notifications)

            start_index = 0
            increment = 1600
            last_index = notification_message.rfind("Center", start_index, start_index + increment)

            while True:
                if start_index + increment > len(notification_message):
                    trigger_whatsapp_notification(notification_message[start_index:start_index + increment], twilio_client_id, twilio_authentication_token, twilio_whatsapp_number, user_whatsapp_number)
                    break

                trigger_whatsapp_notification(notification_message[start_index:last_index], twilio_client_id, twilio_authentication_token, twilio_whatsapp_number, user_whatsapp_number)
                start_index = last_index
                last_index = notification_message.rfind("Center", start_index, start_index + increment)
        else:
            print("No Slot Found, will lookup again in 10 minutes")

    except Exception as ex:
        print("Please check the exception", ex)

    time.sleep(10 * 60)





