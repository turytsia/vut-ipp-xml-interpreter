#!/usr/bin/env bash

# pouziti:   is_it_ok.sh xlogin01-XYZ.zip testdir [task-num]
#  
#   - POZOR: obsah adresare zadaneho druhym parametrem bude po dotazu VYMAZAN (nebo s volbou --force)!
#   - rozbali archiv studenta xlogin99.zip do adresare testdir a overi formalni pozadavky pro odevzdani projektu IPP
#   - cislo ulohy (task-num) je nepovinny parametr (mozne hodnoty: 1 nebo 2) 
#   - nasledne vyzkousi spusteni
#   - detaily prubehu jsou logovany do souboru is_it_ok.log v adresari testdir

# Autor: Zbynek Krivka
# Verze: 1.5.5 (2023-02-08)
#  2012-04-03  Zverejnena prvni verze
#  2012-04-09  Pridana kontrola tretiho radku (prispel Vilem Jenis) a maximalni velikosti archivu
#  2012-04-26  Oprava povolenych pripon archivu, aby to odpovidalo pozadavkum v terminu ve WIS
#  2014-02-14  Pridana moznost koncovky tbz u archivu; Podpora koncovky .php; Kontrola zkratek rozsireni
#  2014-02-25  Pridani parametru -d open_basedir="" interpretu php
#  2015-03-12  Pridana chybejici zavorka v popisu chyby tretiho paramatru
#  2015-03-22  Pridana kontrola tretiho radku i v dalsich skriptech (prispela Michaela Lukasova), kontrola neexistence __MACOSX
#  2016-03-08  Pridana kontrola ulohy CLS a odebrana uloha CST (upozornil Michal Ormoš)
#  2017-02-06  Zrusen pozadavek na metainformace na tretim radku skriptu, zakomentovan kontrolni kod
#  2017-03-04  Aktualizace prikazu pro PHP 5.6 a Python 3.6 na Merlinovi (upozornil ¼uboš Hlipala)
#  2018-03-05  Zruseno deleni projektu na ulohy s pismennymi identifikatory, nyni 1. a 2. uloha
#  2018-03-12  Kontrola existence prikazu dos2unix, nepovinny parametr task-num (umi kontrolovat ulohu 1 nebo 2), barevne vypisy
#  2019-02-12  Uprava jmen a podporovanych formatu dokumentace (pdf|md)
#  2020-01-30  Aktualizace prikazu pro PHP 7.4 a Python 3.8
#  2022-02-03  Aktualizace prikazu pro PHP 8.1, rozsireni NVP, NVI
#  2022-02-08  Skript vraci navratove kody (0=vse OK, 1=vyskytla se chyba v archivu, 2=spatne parametry/vstupyz, 3=spatna pripona skriptu), 
#              Novy parametr --force (prepis existujiciho adresare).  
#              Zruseno rozsireni NVI a FILES.
# TODO: --log pro jmeno souboru pro log, jinak se neloguje.

LOG="is_it_ok.log"
MAX_ARCHIVE_SIZE=1100000
COURSE="IPP"
PARSESCRIPT="parse.php"
INTERPRETSCRIPT="interpret.py"
#TESTSCRIPT="test.php"

# Konstanty barev
REDCOLOR='\033[1;31m'
GREENCOLOR='\033[1;32m'
BLUECOLOR='\033[1;34m'
NOCOLOR='\033[0m' # No Color

# Funkce: vypis barevny text
function echo_color () { # $1=color $2=text [$3=-n]
  COLOR=$NOCOLOR
  if [[ $1 == "red" ]]; then
    COLOR=$REDCOLOR
  elif [[ $1 == "blue" ]]; then
    COLOR=$BLUECOLOR
  elif [[ $1 == "green" ]]; then
    COLOR=$GREENCOLOR
  fi
  echo -e $3 "$COLOR$2$NOCOLOR"
}

# Funkce: patri polozka do pole? (ze seznamu hodnot $* (parametry) hleda prvni parametr v ostatnich parametrech)
function member ()
{
  local -a arr=($*)
  for i in $(seq 1 $#); 
  do
    if [ "${arr[$i]}" = "$1" ];
    then
      return 0
    fi
  done  
  return 1
}

#   Pri nedostatku parametru (povinnych) vypis napovedu
if [[ $# -lt 2 ]]; then
  echo_color red "ERROR: Missing arguments or too much arguments!"
  echo "Usage: $0  ARCHIVE  TESTDIR [TASKNUM] [--force]"
  echo "       This script checks formal requirements for archive with solution of $COURSE project."
  echo "         ARCHIVE - the filename of archive to check"
  echo "         TESTDIR - temporary directory that can be deleted/removed during testing!"
  echo "         TASKNUM - the task number (1 or 2) - optional"
  echo "         --force - do not ask and rewrite existing directory - optional"
  exit 2
fi

declare -i ERRORS=0
declare -a REQUIRED_SCRIPTS=( $PARSESCRIPT $INTERPRETSCRIPT )
declare -a NON_REQUIRED_SCRIPTS=()
declare -i FORCE=0

#   Zpracovani nepovinneho parametru task-num
declare -i TASK=0
if [[ -n $3 ]]; then
  if [[ $3  = "--force" ]]; then
    FORCE=1
  else
    TASK=$3
    if [[ $TASK -eq 1 ]]; then
      REQUIRED_SCRIPTS=( $PARSESCRIPT )
      NON_REQUIRED_SCRIPTS=( $INTERPRETSCRIPT )
    elif [[ $TASK -eq 2 ]]; then
      REQUIRED_SCRIPTS=( $INTERPRETSCRIPT )
      NON_REQUIRED_SCRIPTS=( $PARSESCRIPT )
    else
      echo_color red "ERROR (Unsupported task number: $3 not in {1, 2})"
      exit 2
    fi 
    if [[ -n $4 ]]; then
      if [[ $4 = "--force" ]]; then
        FORCE=1
      fi      
    fi
  fi
fi

#   Extrakce archivu
function unpack_archive () {
  local ext=`echo $1 | cut -d . -f 2,3`
  echo -n "Archive extraction: "
  RETCODE=100  
	if [[ "$ext" = "zip" ]]; then
		unzip -o $1 >> $LOG 2>&1
    RETCODE=$?
	elif [[ "$ext" = "tgz" ]]; then
		tar xfz $1 >> $LOG 2>&1
    RETCODE=$? 
	elif [[ "$ext" = "tbz" || "$ext" = "tbz2" ]]; then
		tar xfj $1 >> $LOG 2>&1
    RETCODE=$? 
	fi
  if [[ $RETCODE -eq 0 ]]; then
    echo_color green OK
  elif [[ $RETCODE -eq 100 ]]; then
    echo_color red "ERROR (unsupported extension)"
    exit 1
  else
    echo_color red "ERROR (code $RETCODE)"
    exit 1
  fi
} 

#   Priprava testdir
if [[ -d $2 ]]; then
  if [[ $FORCE -eq 1 ]]; then
    rm -rf $2 2>/dev/null
  else
    read -p "Do you want to delete $2 directory? (y/n)" RESP
    if [[ $RESP = "y" ]]; then
      rm -rf $2 2>/dev/null
    else
      echo_color red "ERROR:" -n
      echo "User cancelled rewriting of existing directory."
      exit 2
    fi
  fi
fi
mkdir $2 2>/dev/null
cp $1 $2 2>/dev/null


#   Overeni serveru (ala Eva neni Merlin)
echo -n "Testing on Merlin: "
HN=`hostname`
if [[ $HN = "merlin.fit.vutbr.cz" ]]; then
  echo_color green "Yes"
else
  echo_color blue "No"
fi

#   Kontrola jmena archivu
cd $2
touch $LOG
ARCHIVE=`basename $1`
NAME=`echo $ARCHIVE | cut -d . -f 1 | egrep "^x[a-z]{5}[0-9][0-9a-z]$"`
echo -n "Archive name ($ARCHIVE): "
if [[ -n $NAME ]]; then
  echo_color green "OK"
else
  echo_color red "ERROR (the name $NAME does not correspond to a login)"
  let ERROR=ERROR+1
fi

#   Kontrola velikosti archivu
echo -n "Checking size of $ARCHIVE: "
ARCHIVE_SIZE=`du --bytes $ARCHIVE | cut -f 1`
if [[ ${ARCHIVE_SIZE} -ge ${MAX_ARCHIVE_SIZE} ]]; then 
  echo_color red "ERROR (Too big (${ARCHIVE_SIZE} bytes > ${MAX_ARCHIVE_SIZE} bytes)"
  let ERROR=ERROR+1
else 
  echo_color green "OK" 
fi

#   Extrahovat do testdir
unpack_archive ${ARCHIVE}

#   Dokumentace
echo -n "Searching for readme${TASK}.(pdf|md): "
if [[ $TASK -eq 0 ]]; then
  if [ -f "readme1.pdf"  -o  -f "readme1.md" ]; then
    echo_color blue "OK (readme1 found)"
  elif [ -f "readme2.pdf"  -o  -f "readme2.md" ]; then
    echo_color blue "OK (readme2 found)"
  else  
    echo_color red "ERROR (not found; required readme1 or readme2!)"
    let ERROR=ERROR+1
  fi
elif [ $TASK -eq 1 -o  $TASK -eq 2 ]; then
  if [ -f "readme${TASK}.pdf"  -o  -f "readme${TASK}.md" ]; then
    echo_color green "OK"
  else  
    echo_color red "ERROR (not found!)"
    let ERROR=ERROR+1
  fi
else
  echo_color red "ERROR (not found!)"  
fi
#fi

#   Spusteni skriptu
echo "Scripts execution test (--help): "
for SCRIPT in "${REQUIRED_SCRIPTS[@]}" "${NON_REQUIRED_SCRIPTS[@]}"; do
  if [[ -f $SCRIPT ]]; then
    echo -n "  Checking $SCRIPT: "
    EXT=`echo $SCRIPT | cut -d . -f 2`
    if [[ "$EXT" = "php" ]]; then
      php8.1 $SCRIPT --help >> $LOG 2>&1
      RETCODE=$?
	  elif [[ "$EXT" = "py" ]]; then
      python3.8 $SCRIPT --help >> $LOG 2>&1
      RETCODE=$?		 
	  else
      echo_color red "INTERNAL ERROR: Unknown script extension."
      exit 3
	  fi
    if [[ $RETCODE -eq 0 ]]; then
      #echo -n "  $SCRIPT: "
      echo_color green "OK"
    else
      #echo -n "  $SCRIPT: "
      echo_color red "ERROR (returns code $RETCODE)"
      let ERROR=ERROR+1
    fi    
  else
    if [[ $TASK -eq 0 ]]; then
      if [[ "$SCRIPT" = "$PARSESCRIPT" ]]; then
        echo_color blue "  $SCRIPT: ERROR (not found; required for 1st task only!)"
        let ERROR=ERROR+1 
      else
        echo_color blue "  $SCRIPT: ERROR (not found; required for 2nd task only!)"
        let ERROR=ERROR+1
      fi
    else
      if ( member $SCRIPT ${REQUIRED_SCRIPTS[@]} ); then
        echo_color red "  $SCRIPT: ERROR (not found; required for task $TASK!)"
        let ERROR=ERROR+1
      fi      
    fi  
  fi
done

#   Kontrola rozsireni
echo -n "Presence of file rozsireni (optional): "
if [[ -f rozsireni ]]; then
  echo_color green "Yes"
  echo -n "Unix end of lines in rozsireni: "
  if command -v dos2unix >/dev/null 2>&1; then
      dos2unix -n rozsireni rozsireni.lf >> $LOG 2>&1
  else
      tr -d '\r' < rozsireni > rozsireni.lf 2>&1
  fi
  diff rozsireni rozsireni.lf >> $LOG 2>&1
  RETCODE=$?
  if [[ $RETCODE = "0" ]]; then
    UNKNOWN=`cat rozsireni | grep -v -E -e "^(STATP|NVP|FLOAT|STACK|STATI)$" | wc -l`
    if [[ $UNKNOWN = "0" ]]; then
      echo_color green "OK" 
    else
      echo_color red "ERROR (Unknown bonus identifier or redundant empty line)"
      let ERROR=ERROR+1
    fi
  else
    echo_color red "ERROR (CRLFs)"
    let ERROR=ERROR+1
  fi
else
  echo "No"
fi 

#   Kontrola adresare __MACOSX
if [[ -d __MACOSX ]]; then
  echo_color blue "Archive ($ARCHIVE) should not contain (hidden) __MACOSX directory!"
  let ERROR=ERROR+1
fi

echo -n "ALL CHECKS COMPLETED"
if [[ $ERROR -eq 0 ]]; then
  echo_color green " WITHOUT ERRORS!"
  # Vse je OK
  exit 0
elif [[ $ERROR -eq 1 ]]; then
  echo_color red " WITH $ERROR ERROR!"
  # Vyskytla se chyba!
  exit 1    
else
  echo_color red " WITH $ERROR ERRORS!"
  # Vyskytlo se vice chyb!
  exit 1
fi
