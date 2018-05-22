#!/bin/sh

#@TODO take dates as command-line options for weekly runs
#@TODO fork and run in mutliple threads

GT=/home/Public/socialsim/weekly_evals/2018_0517/simulation/groundtruth_time-events-20170817-20170831.csv
SIM=''
JSON_FILE=''
LOG_FILE=''

clear

echo "SocialSim Evaluation Engine"
echo ""
echo "Select an option:"
echo " * 1: GT - GT"
echo " * 2: GT - Repo Centric Model"
echo " * 3: GT - User Centric Model"

read SEL
case $SEL in
	1) echo "Evaluate GT-GT"
	   SIM=/home/Public/socialsim/weekly_evals/2018_0517/simulation/groundtruth_time-events-20170817-20170831.csv
  	   JSON_FILE=/home/Public/socialsim/weekly_evals/2018_0517/evals/latest/gtgt_eval.json
  	   LOG_FILE=/home/Public/socialsim/weekly_evals/2018_0517/evals/latest/gtgt_eval.log
		;;
	2) echo "Evaluate GT - repo centric model"
	   SIM=/home/Public/socialsim/weekly_evals/2018_0517/simulation/sim_2017_0817-31_pointprocess_poisson_events.csv
	   JSON_FILE=/home/Public/socialsim/weekly_evals/2018_0517/evals/latest/repocentric_eval.json
	   LOG_FILE=/home/Public/socialsim/weekly_evals/2018_0517/evals/latest/repocentric_eval.log
		;;
	3) echo "Evaluate GT - user centric model"
	   SIM=/home/Public/socialsim/weekly_evals/2018_0517/simulation/sim_2017_0817-31_simple_events.csv
	   JSON_FILE=/home/Public/socialsim/weekly_evals/2018_0517/evals/latest/usercentric_eval.json
	   LOG_FILE=/home/Public/socialsim/weekly_evals/2018_0517/evals/latest/usercentric_eval.log
		;;
	*) echo "INVALID NUMBER!" ;;
esac

python3 metrics_config.py -s $SIM -g $GT -o $JSON_FILE &> $LOG_FILE 
