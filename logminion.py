#!/usr/bin/env python

# log minion: generate and email logs and shit
# by jiva

import smtplib, os, re, time, datetime, gzip, operator
from optparse import OptionParser

#option parser shit
def createoptions():
	parser = OptionParser('Usage: %prog [options]')
	parser.add_option('-s', '--sshfailz', action='store_true', dest='sshfailz', default=False, help='Email failed SSH login attempts for the previous day')
	parser.add_option('-n', '--name', dest='name', help='Specify the name of this machine to use in the subject line of the email')
	return parser

#parse the ssh log files and return the interesting stuff
def getsshfailz():
	rawfailedattempts = []
	LOG_DIR = '/var/log/'
	months = {'1':'Jan', '2':'Feb', '3':'Mar', '4':'Apr', '5':'May', '6':'Jun', '7':'Jul', '8':'Aug', '9':'Sep', '10':'Oct', '11':'Nov', '12':'Dec'}
	month = months[str((datetime.date.today() - datetime.timedelta(1)).month)]
	day = str((datetime.date.today() - datetime.timedelta(1)).day)
	files = os.listdir(LOG_DIR)
	for file in files:
		if file.startswith('auth.log'): #ubuntu box
			if file.endswith('gz'):
				f = gzip.open(os.path.join(LOG_DIR, file), 'rb')
			else:
				f = open(os.path.join(LOG_DIR, file), 'r')
			for line in f:
				matches = re.findall(r'^' + month + '\s+?' + day + '.*?Failed\spassword\sfor\s.*?from\s(\d+\.\d+\.\d+\.\d+).*$', line)
				if matches:
					for match in matches:
						rawfailedattempts.append(match)
		elif file.startswith('secure'): #fedora box
			if file.endswith('gz'):
				f = gzip.open(os.path.join(LOG_DIR, file), 'rb')
			else:
				f = open(os.path.join(LOG_DIR, file), 'r')
			for line in f:
				matches = re.findall(r'^' + month + '\s+?' + day + '.*?Failed\spassword\sfor\s.*?from\s(\d+\.\d+\.\d+\.\d+).*$', line)
				if matches:
					for match in matches:
						rawfailedattempts.append(match)
	countedfailedattempts = {}
	for attempt in rawfailedattempts:
		if attempt in countedfailedattempts:
			countedfailedattempts[attempt] += 1
		else:
			countedfailedattempts[attempt] = 1
	retlist = []
	for attempt,count in sorted(countedfailedattempts.iteritems(), key=operator.itemgetter(1), reverse=True):
		retlist.append(attempt + ':\t' + str(count))
	return retlist

#email the shit
def mail(_message, _subj):
	smtpuser = 'SOME_EMAIL@gmail.com'
	smtppass = 'SOME_PASSWORD'
	frm = 'SOMEONE@SOME_EMAIL.COM'
	to = ['SOMEONE@SOME_EMAIL.COM']
	subj = _subj + ': ' + str(int(time.time()))
	message = 'To:' + str(to) + '\n' + 'From:' + frm + '\n' + 'Subject:' + subj + '\n\n'
	message = message + _message
	server = smtplib.SMTP('smtp.gmail.com')
	# server.set_debuglevel(1)
	server.ehlo()
	server.starttls()
	server.ehlo()
	server.login(smtpuser,smtppass)
	server.sendmail(frm, to, message)
	server.quit()

#main function
def main():
	parser = createoptions()
	(options, args) = parser.parse_args()
	if not options.name:
		print '--name required'
		parser.print_help()
	elif options.sshfailz:
		retsshfailz = getsshfailz()
		if len(retsshfailz) != 0:
			mail('\n'.join(retsshfailz), 'SSH failz for ' + options.name)
	else:
		parser.print_help()

if __name__ == '__main__':
	main()

# crontab -e to run each midnight
# 0 0 * * * python /path/to/logminion.py -s --name "name-here"
