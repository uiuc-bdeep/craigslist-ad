from __future__ import print_function
import gspread
from oauth2client.client import SignedJwtAssertionCredentials
import pandas as pd
import json
import numpy as np

SCOPE = ["https://spreadsheets.google.com/feeds"]
SECRETS_FILE = "/home/junyu/Research/ZillowAd/FormExtractKey.json"


EMAIL_ACCOUNT ="rentingmanagement@gmail.com"
EMAIL_PASSWORD = "Zjy960606"

sheet_address_dict = {'1703101': 'E Lake St',
						'1703102': 'W Randolph St'}

address_log_dict = {'E Lake St': "/home/junyu/Research/ZillowAd/form_log1703101.csv", 
					'W Randolph St': '/home/junyu/Research/ZillowAd/form_log1703102.csv'}


sheet_set = ['1703101', '1703102']

def generate_reply(reci_first, address):
	text = ""
	text += "Dear " + reci_first + ","
	text += "\n\n"
	text += "The housing you are searching for at "
	text += address
	text += " is no longer available. \n\n"
	text += "Thank you for your interest "
	text += "and best of luck with your search."
	return text


def send_email(reci_first, reci_email, address):
	global SCOPE
	global SECRETS_FILE

	# Import smtplib for the actual sending function
	import smtplib

	# Import the email modules we'll need
	from email.mime.text import MIMEText

	# Open a plain text file for reading.  For this example, assume that
	# the text file contains only ASCII characters.

	# Create a text/plain message
	msg = MIMEText(generate_reply(reci_first, address))


	msg['Subject'] = "Update on %s " % address
	msg['From'] = EMAIL_ACCOUNT
	msg['To'] = reci_email

	# Send the message via our own SMTP server, but don't include the
	# envelope header.
	s = smtplib.SMTP('smtp.gmail.com', port = '587')
	s.ehlo()
	s.starttls()
	s.ehlo
	s.login(EMAIL_ACCOUNT, EMAIL_PASSWORD)
	s.sendmail(EMAIL_ACCOUNT, [reci_email], msg.as_string())
	s.quit()



def handle_work_sheet(SPREADSHEET, down):
	global SCOPE
	global SECRETS_FILE
	global sheet_address_dict

	address = sheet_address_dict[SPREADSHEET]
	log_file = address_log_dict[address]


	print("handling for", address)


	# Based on docs here - http://gspread.readthedocs.org/en/latest/oauth2.html
	# Load in the secret JSON key (must be a service account)
	json_key = json.load(open(SECRETS_FILE))
	# Authenticate using the signed key
	credentials = SignedJwtAssertionCredentials(json_key['client_email'],
												json_key['private_key'], SCOPE)

	gc = gspread.authorize(credentials)
	print("The following sheets are available")
	for sheet in gc.openall():
		print("{} - {}".format(sheet.title, sheet.id))
	# Open up the workbook based on the spreadsheet name
	workbook = gc.open(SPREADSHEET)
	# Get the first sheet
	sheet = workbook.sheet1
	# Extract all data into a dataframe
	data = pd.DataFrame(sheet.get_all_records())
	# Do some minor cleanups on the data
	# Rename the columns to make it easier to manipulate
	# The data comes in through a dictionary so we can not assume order stays the
	# same so must name each column
	column_names = {'Timestamp': 'timestamp',
					'First Name': 'first_name',
					'Last Name': 'last_name',
					'Gender': 'gender',
					'Age': 'age',
					'Current Employer': 'employer',
					"Current Employer's City and State": 'employer_city',
					'Gross Annual Income': 'income',
					'Co-Applicant Gross Annual Income (if applicable)': 'co_income',
					'How many cars do you own': 'cars',
					'Contact Email': 'email',
					'Current Address - Street Address': 'cur_street',
					'Current Address - City and State': 'cur_city',
					'Current Address - ZIP Code': 'cur_zip'
					}
	data.rename(columns=column_names, inplace=True)
	if (len(data)==0):
		return
	data.timestamp = pd.to_datetime(data.timestamp)

	for i in range(down, data.shape[0]):
		email = data['email'][i]
		first_name = data['first_name'][i]
		try:
			send_email(first_name, email, address)
		except:
			print("record '", address, "' sending to'", email, "' failed")

	data.to_csv(log_file, index=False)


def iterate_sheets(sheet):
	address = sheet_address_dict[sheet]
	log_file = address_log_dict[address]

	try:
		csv_array = np.array(pd.read_csv(log_file)).tolist()
		down = len(csv_array)
	except:
		down = 0

	handle_work_sheet(sheet, down)

for sheet in sheet_set:
	iterate_sheets(sheet)