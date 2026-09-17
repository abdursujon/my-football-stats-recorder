# Development process of Football Stats Recorder 
# Create the script record_football_match_stats.py
- write all functions and nessary code 

# How to automate git commit on timer 
1. Create the service file:
mkdir -p ~/.config/systemd/user
nano ~/.config/systemd/user/football-stats-prompt.service
Paste:
[Unit]
Description=Prompt for football match stats

[Service]
Type=oneshot
WorkingDirectory=/home/sujon/Project/my-football-stats-recorder
ExecStart=/usr/bin/python3 /home/sujon/Project/my-football-ll_match_stats.py

2. Create the timer file:
nano ~/.config/systemd/user/football-stats-prompt.timer
Paste:
[Unit]
Description=Daily 10pm football stats prompt

[Timer]
OnCalendar=*-*-* 22:00:00
Unit=football-stats-prompt.service

[Install]
WantedBy=timers.target

3. Enable it:
systemctl --user daemon-reload
systemctl --user enable --now football-stats-prompt.timer

4. Confirm the next run time:
systemctl --user list-timers football-stats-prompt.timer

5. Test the prompt without waiting for 10pm:
systemctl --user start football-stats-prompt.service

6. If nothing appears, check the log:
journalctl --user -u football-stats-prompt.service -n 20

# How to setup SHH for this project 
Set up SSH access:

1. Generate a key with no passphrase (empty passphrase is what makes unattended push possible):
ssh-keygen -t ed25519 -C "football-stats-recorder" -f ~/.ssh/github_stats -N ""

2. Print the public key and copy it:
cat ~/.ssh/github_stats.pub

3. On GitHub: Settings → SSH and GPG keys → New SSH key → paste → Add.

4. Tell SSH to use that key for GitHub:
printf 'Host github.com\n  IdentityFile ~/.ssh/github_stats\n  IdentitiesOnly yes\n' >> ~/.ssh/config

5. Test and accept GitHub's host fingerprint:
ssh -T git@github.com
Type yes at the prompt. Expect: Hi abdursujon! You've successfully authenticated...

6. Switch the remote from HTTPS to SSH:
cd ~/Project/my-football-stats-recorder
git remote set-url origin git@github.com:abdursujon/my-football-stats-recorder.git

7. Verify a push works by hand before trusting the timer:
git push


Test auto github push 
1. Queue the test run:
systemd-run --user --on-active=5m --unit=football-stats-test \
  /usr/bin/python3 /home/sujon/Project/my-football-stats-recorder/record_football_match_stats.py

2. Confirm it's queued:
systemctl --user list-timers football-stats-test.timer