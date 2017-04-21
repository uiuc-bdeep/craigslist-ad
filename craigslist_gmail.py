#!/usr/bin/env python

import sys
import imaplib
import getpass
import email
import email.header
import datetime

import numpy as np
import pandas as pd
import base64

EMAIL_ACCOUNT = "rentingmanagement@gmail.com"
EMAIL_PASSWORD = "BdeepCraigslist"
EMAIL_FOLDER = "Inbox"
log_file = '/home/ubuntu/RentalAd/craig_email_log.csv'

code_form_dict = {
	'1703101' : 'https://goo.gl/forms/abZGFoRIY2t1JpXR2',
	'1703102' : 'https://goo.gl/forms/dt6JeujC280c0bvk2'
}

code_address_dict = {
	'1703101' : 'E Lake St',
	'1703102' : 'W Randolph St'
}

CL_code_dict = {
	'dk2rc-6087105721@hous.craigslist.org' : '1703101',
	'fbd2j-6092672765@hous.craigslist.org' : '1703101',
	'4gnwm-6094399942@hous.craigslist.org' : '1703102',
	'w44s7-6095554881@hous.craigslist.org' : '1703102',
	'fdhjm-6097992357@hous.craigslist.org' : '1703101'
}

def split_sender_email(from_header):
	splitted = from_header.split("<")
	return (splitted[0][0:-1], splitted[1][0:-1])


def generate_message(sender, code):
	address = code_address_dict[code]
	form = code_form_dict[code]


	text = ""
	text += "Dear " + sender + ","
	text += "\n\n"
	text += "Thank you for your interest in "
	text += address + ". "	
	text += "\n\n"
	text += "Please expedite your process by answering a few questions using the following google form:"
	text += "\n"
	text += form
	text += "\n\n"
	text += "Thank you!"
	text += "\n\n"
	text += "Note: This is an auto-reply message and please do not reply to this. "

	return text

def send_email(recipient, sender, code):
	# Import smtplib for the actual sending function
	import smtplib

	# Import the email modules we'll need
	from email.mime.text import MIMEText


	# Create a text/plain message
	msg = MIMEText(generate_message(sender, code))


	# me == the sender's email address
	# you == the recipient's email address
	msg['Subject'] = "Auto-Reply Message Regarding Rental Inquiry for Property on " +  code_address_dict[code]
	msg['From'] = EMAIL_ACCOUNT
	msg['To'] = recipient

	print msg

	# Send the message via our own SMTP server, but don't include the
	# envelope header.
	# s = smtplib.SMTP('smtp.gmail.com', port = '587')
	# s.ehlo()
	# s.starttls()
	# s.ehlo
	# s.login(EMAIL_ACCOUNT, EMAIL_PASSWORD)
	# s.sendmail(EMAIL_ACCOUNT, [recipient], msg.as_string())
	# s.quit()


def process_message(num, msg):
	content = None

	for part in msg.walk():
		if part.get_content_type() == 'text/html':
			content = part.get_payload()


	subject = email.header.decode_header(msg['Subject'])[0][0]

	print subject


	from_header = email.header.decode_header(msg['From'])[0][0]
	to_header = email.header.decode_header(msg['To'])[0][0]

	print from_header, to_header

	if to_header not in CL_code_dict.keys():
		return

	code = CL_code_dict[to_header]



	date_tuple = email.utils.parsedate_tz(msg['Date'])
	if date_tuple:
		local_date = datetime.datetime.fromtimestamp(email.utils.mktime_tz(date_tuple))


	splitted = split_sender_email(from_header)
	sender = splitted[0].replace('"', '')
	return_email = splitted[1]

	global csv_array 
	csv_array += [[num, code, local_date, sender, return_email]]
	send_email(return_email, sender, code)


def process_mailbox(M):


	rv, data = M.search(None, "ALL")
	if rv != 'OK':
		print "No messages found!"
		return

	for num in data[0].split():
		rv, data = M.fetch(num, '(RFC822)')
		if rv != 'OK':
			print "ERROR getting message", num
			return

		msg = email.message_from_string(data[0][1])
		num = int(num)
		global down
		if num <= down: 
			continue
		process_message(num, msg)

csv_array = None

try:
	csv_array = np.array(pd.read_csv(log_file)).tolist()
	down = csv_array[len(csv_array)-1][0]
except:
	csv_array = []
	down = 0


M = imaplib.IMAP4_SSL('imap.gmail.com')

try:
	rv, data = M.login(EMAIL_ACCOUNT, EMAIL_PASSWORD) 
except imaplib.IMAP4.error:
	print "LOGIN FAILED!!! "
	sys.exit(1)

print rv, data

rv, mailboxes = M.list()
if rv == 'OK':
	print "Mailboxes:"
	print mailboxes

rv, data = M.select(EMAIL_FOLDER)
if rv == 'OK':
	print "Processing mailbox...\n"
	process_mailbox(M)
	M.close()
else:
	print "ERROR: Unable to open mailbox ", rv


M.logout()

def save_list_to_file (table, file_path, headers):
	
	if (len(table)>0):
		matrix = np.asarray(table)
		df = pd.DataFrame(matrix)
		df.to_csv(file_path, index = False, header = headers)

print csv_array

save_list_to_file(csv_array, log_file, ['num', 'code', 'local_date', 'sender', 'return_email'])
