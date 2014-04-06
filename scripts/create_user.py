#!/usr/bin/env python
import nupay
import ConfigParser
import sys
import os
import argparse
from getpass import getpass

# Program name, version and date
PROGRAM_NAME = 'UPAY User Mangement Utility'
PROGRAM_VERSION = '0.1'
PROGRAM_DATE = '2014-03-16'
PROGRAM_STRING = "%s %s (%s)" % (PROGRAM_NAME, PROGRAM_VERSION, PROGRAM_DATE)

# Configure arguments and set parsing options
parser = argparse.ArgumentParser(description=PROGRAM_STRING)
parser.add_argument('-c', '--configuration', 
						  type=str,
						  dest='config_file_name',
						  help='Location of the configuration file')

parser.add_argument('-a', '--action',
						  type=str,
						  dest='action',
						  help='action to perform: create, set_password',
						  required=True)

parser.add_argument('-u', '--username',
						  type=str,
						  dest='username',
						  required=True)


# Parse the arguments as defined
args = parser.parse_args()

config_file_path = args.config_file_name

config = ConfigParser.RawConfigParser()
config.read(config_file_path)

session_manager = nupay.ServerSessionManager(config)
session = session_manager.create_session()

if args.action == 'create' or args.action == 'set_password':
    password = getpass()
if args.action == 'create':
    session.create_user(args.username, password)
session.close()

