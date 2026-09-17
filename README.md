# my_football_stats_recorder
A stats recorder which automate recording my football match contribution and prompt automatic message the days I play football.

To do: 
1. A script that will run automatically on Thursday and Saturday at UK time 10pm 
with a prompt pop up with entry of asking 
a) how many goal I scored
b) how many assist 
c) option to choose not played 

2. After getting the entry the script will then write a file in this repo with 
Date | Goal Scored | Assits
Then next row will have stats like below 
Total Goal = number | Total Assist = number

3. After writing the file, the the script will auto commit the file to github 

my-football-stats-recorder/
├── README.md
├── record_match.py      # prompt, append, render, commit
├── STATS.md             # the table
└── stats.timer/.service # scheduling