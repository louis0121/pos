#!/bin/bash

# Read parameters from config file
function __readINI() {
 INIFILE=$1;    SECTION=$2; ITEM=$3
 _readIni=`awk -F '=' '/\['$SECTION'\]/{a=1}a==1&&$1~/'$ITEM'/{print $2;exit}' $INIFILE`
echo ${_readIni}
}

INFILE=measure.ini
SECTION=runconf

runnode=$(__readINI $INFILE $SECTION runnode)
startport=$(__readINI $INFILE $SECTION startport)
stakesum=$(__readINI $INFILE $SECTION stakesum)
firstcommem=$(__readINI $INFILE $SECTION firstcommem)
firstcomno=$(__readINI $INFILE $SECTION firstcomno)
secondcommem=$(__readINI $INFILE $SECTION secondcommem)

SECTION=measureconf

tpsmeanode=$(__readINI $INFILE $SECTION tpsmeanode)

basepath=$(pwd)

if [ -d ./log ]; then
    echo "./log already exit, remove it."
    rm -r ./log
fi
echo "create new node log directory"
mkdir ./log

eachstake=`expr $stakesum / $runnode`
# echo $eachstake
for ((i=1;i<=$runnode;i++))
do
    logpath=$basepath/log/$i/
#    confpath=$basepath/log/$i/bitcoin.conf
    clientport=`expr $startport + $i`
    stakemax=`expr $i \* $eachstake`
    stakemin=`expr $i \* $eachstake - $eachstake`
#    echo $stakemin
#    echo $stakemax
    mkdir $logpath 
    touch $logpath/clicf.ini
    port1=`expr $startport + $i - 1`
    #port2=`expr $startport + $i + 1`
    filecontent="[baseconf]\nnodenumber=1\nhost1=localhost\nport1=$port1\nstakesum=$stakesum\nstakemin=$stakemin\nstakemax=$stakemax\nfirstcommem=$firstcommem\nfirstcomno=$firstcomno\nsecondcommem=$secondcommem"
    echo -e $filecontent > ./log/$i/clicf.ini
    ./minernode.py $logpath $clientport $i 0 &
   # sleep 0.1 
done

beginmea=`expr $runnode + 1`
endmea=`expr $runnode + $tpsmeanode`
# echo $beginmea
# echo $endmea
for ((i=$beginmea;i<=$endmea;i++))
do
    logpath=$basepath/log/$i/
#    confpath=$basepath/log/$i/bitcoin.conf
    clientport=`expr $startport + $i`
    stakemax=`expr $i \* $eachstake`
    stakemin=`expr $i \* $eachstake - $eachstake`
#    echo $stakemin
#    echo $stakemax
    mkdir $logpath 
    touch $logpath/clicf.ini
    port1=`expr $startport + $beginmea - 1`
    port2=`expr $startport + 2`
    port3=`expr $startport + $i - 5`
    port4=`expr $startport + $i - 9`
    port5=`expr $startport + $i - 11`
    filecontent="[baseconf]\nnodenumber=2\nhost1=localhost\nport1=$port1\nhost2=localhost\nport2=$port2\nstakesum=$stakesum\nstakemin=$stakemin\nstakemax=$stakemax\nfirstcommem=$firstcommem\nfirstcomno=$firstcomno\nsecondcommem=$secondcommem"
    echo -e $filecontent > ./log/$i/clicf.ini
    ./minernode.py $logpath $clientport $i 1 &
   # sleep 0.1 
done
