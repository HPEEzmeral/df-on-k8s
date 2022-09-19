#!/usr/bin/env bash

read -p 'What is the old tag? ' OLDTAG
read -p 'What is the new tag? ' NEWTAG
DEFAULT='y'
read -e -p "Replacing ${OLDTAG} with ${NEWTAG}. Proceed [Y/n/q]:" PROCEED
# adopt the default, if 'enter' given
PROCEED="${PROCEED:-${DEFAULT}}"
if [[ ${PROCEED} == 'y' ]]; then
  echo "replacing tags..."
  #grep --include={*.yaml} -rnl './' -e "${OLDTAG}" | xargs -I@ sed -i "s/${OLDTAG}/${NEWTAG}/g" @
  grep -rli "${OLDTAG}" * | xargs -I@ sed -i "" "s/${OLDTAG}/${NEWTAG}/g" @
fi
