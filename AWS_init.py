
# Spin up EC2 instances, then execute this script.
# import boto.ec2
# This is automatable with boto.ec2 API.
# Whenever spinning up instances, you may need to reinitialize dropbox process.
# ~/.dropbox-dist/dropboxd
# ALWAYS REMEMBER: apollonia.verre13 and lennon.laika13 need mobile verifications.


import json
import subprocess
import os
import time
from pprint import pprint

print("Obtaining Amazon EC2 instance details...")
aws_out = subprocess.Popen(['aws', 'ec2', 'describe-instances'],
                            stdout=subprocess.PIPE).communicate()[0]
instances = json.loads(aws_out.decode('utf-8'))['Reservations']

aws_pair = []
for instance in instances:
    if instance['Instances'][0]['State']['Name'] != 'running':
        continue
    ip = instance['Instances'][0]['PublicDnsName']
    name = int(instance['Instances'][0]['Tags'][0]['Value'])
    aws_pair.append((name, ip))

aws_pair = sorted(aws_pair)


BASE_DIR = os.path.join('Dropbox', 'gtrends-beta')
ssh_login = 'ssh -i $HOME/Dropbox/dg-beta.pem -o StrictHostKeyChecking=no ubuntu@'
ssh_login = 'ssh -i $HOME/Dropbox/dg-beta.pem ubuntu@'
start_dropbox = ".dropbox-dist/dropboxd"
start_gtrends = "python {base_dir}/gtrends_ioi.py".format(base_dir=BASE_DIR)


logins = [ssh_login + t[1] for t in aws_pair]

for command in logins:
    osxcall = """
        osascript 2>/dev/null <<EOF
          tell application "iTerm"
            set current_terminal to current terminal
            tell current_terminal
              launch session "Default Session"
              set current_session to current session
              tell current_session
                write text "{command}"
              end tell
            end tell
          end tell
        EOF""".format(command=command)
    os.system(osxcall)


print("If nothing happens, make sure iTerm2 is open")







