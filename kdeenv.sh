#!/bin/bash
EMERGE_ENV=$(python3.5 "$( dirname "${BASH_SOURCE[0]}" )"/bin/EmergeSetupHelper.py --setup --mode bash)

for line in $EMERGE_ENV; do
  if [[ $line  =~ "=" ]];then
    export $line
  fi
done
