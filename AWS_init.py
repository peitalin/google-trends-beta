
# Spin up EC2 instances, then execute this script.

import json, subprocess, os, time

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












"""
~/.dropbox-dist/dropboxd; python ~/Dropbox/gtrends-beta/gtrends_ioi.py
python ~/Dropbox/gtrends-beta/gtrends_ioi.py



##### Dropbox account
woolford.paul13@gmail.com
justfortesting!

### Install dependencies
sudo apt-get update && \
sudo apt-get install git tree python-pip python3 -y && \
sudo pip install ipython arrow fuzzywuzzy argparse requests selenium


echo 'force_color_prompt=yes' > .bashrc2
cat .bashrc >> .bashrc2
echo 'export base_dir="$HOME/Dropbox/gtrends-beta"' >> .bashrc2
echo 'export LC_CTYPE="en_US.UTF-8"' >> .bashrc2
echo 'alias dbox="~/.dropbox-dist/dropboxd"' >> .bashrc2
mv .bashrc2 .bashrc


### Install dropbox
cd ~ && wget -O - "https://www.dropbox.com/download?plat=lnx.x86_64" | tar xzf -
screen
~/.dropbox-dist/dropboxd
###  copy and verify resulting link

### .bashrc configs
echo $GMAIL_USER $base_dir && ps aux | grep dropbox



#########################################
### GMAIL USER SETUPS
echo 'export GMAIL_USER="halos.laurel13@gmail.com"' >> .bashrc
echo 'export PS1="<1> $PS1"' >> .bashrc

echo 'export GMAIL_USER="pika.colt13@gmail.com"' >> .bashrc
echo 'export PS1="<2> $PS1"' >> .bashrc

echo 'export GMAIL_USER="hecker.tim13@gmail.com"' >> .bashrc
echo 'export PS1="<3> $PS1"' >> .bashrc

echo 'export GMAIL_USER="kenton.slash13@gmail.com"' >> .bashrc
echo 'export PS1="<4> $PS1"' >> .bashrc

echo 'export GMAIL_USER="woolford.paul13@gmail.com"' >> .bashrc
echo 'export PS1="<5> $PS1"' >> .bashrc

echo 'export GMAIL_USER="frahms.ford13@gmail.com"' >> .bashrc
echo 'export PS1="<6> $PS1"' >> .bashrc

echo 'export GMAIL_USER="sam.blasko13@gmail.com"' >> .bashrc
echo 'export PS1="<7> $PS1"' >> .bashrc

echo 'export GMAIL_USER="fur.florian13@gmail.com"' >> .bashrc
echo 'export PS1="<8> $PS1"' >> .bashrc

echo 'export GMAIL_USER="watts.valeska13@gmail.com"' >> .bashrc
echo 'export PS1="<9> $PS1"' >> .bashrc

echo 'export GMAIL_USER="henke.phil13@gmail.com"' >> .bashrc
echo 'export PS1="<10> $PS1"' >> .bashrc

echo 'export GMAIL_USER="apollonia.verre13@gmail.com"' >> .bashrc
echo 'export PS1="<11> $PS1"' >> .bashrc

echo 'export GMAIL_USER="lennon.laika13@gmail.com"' >> .bashrc
echo 'export PS1="<12> $PS1"' >> .bashrc





    python $base_dir/google_trends/trends.py \
        --username $GMAIL_USER \
        --password justfortesting! \
        --ipo-quarters "2012-05" \
        --keyword "Facebook"



    python3 $base_dir/google_trends/trends.py \
        --username $GMAIL_USER \
        --password justfortesting! \
        --ipo-quarters "2012-05" \
        --keyword "Facebook"





cd /usr/local/share
sudo wget https://bitbucket.org/ariya/phantomjs/downloads/phantomjs-1.9.7-linux-x86_64.tar.bz2
sudo tar xjf phantomjs-1.9.7-linux-x86_64.tar.bz2

sudo unlink /usr/local/bin/phantomjs
sudo unlink /usr/local/share/phantomjs
sudo unlink /usr/bin/phantomjs

sudo ln -s /usr/local/share/phantomjs-1.9.7-linux-x86_64/bin/phantomjs /usr/local/share/phantomjs;
sudo ln -s /usr/local/share/phantomjs-1.9.7-linux-x86_64/bin/phantomjs /usr/local/bin/phantomjs;
sudo ln -s /usr/local/share/phantomjs-1.9.7-linux-x86_64/bin/phantomjs /usr/bin/phantomjs


"""
