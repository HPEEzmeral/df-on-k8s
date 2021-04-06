#!/usr/bin/env bash
ECHOE="echo -e"

# return codes
NO=0
YES=1
INFO=0
WARN=-1
ERROR=1

MAPR_HOME=${MAPR_HOME:-"/opt/mapr"}
CONFDIR="$MAPR_HOME/conf"
PROMPT_SILENT=$NO
SECURE_CLUSTER="false"
CLUSTER_NAME="my.cluster.com"

OUTPUT_FILE="mapr-hsm-config.yaml"


# Output an error, warning or regular message
msg() {
  msg_format "$1" $2
}

msg_prefix() {
  ts=`date "+%Y/%m/%d %H:%M:%S"`
  prefix="$ts $CURRENT_FILE"
}

# Print each word according to the screen size
msg_format() {
    local length=0
    local width=""
    local words=$1

    width=$(tput cols)
    width=${width:-80}
    for word in $words; do
        length=$(($length + ${#word} + 1))
        if [ $length -gt $width ]; then
            $ECHOE "\n$word \c"
            length=$((${#word} + 1))
        else
            $ECHOE "$word \c"
        fi
    done
}

msg_err() {
  msg_prefix
  msg_format "$prefix: [ERROR] $1"
}

prompt() {
    local query=$1
    local default=${2:-""}

    shift 2
    if [ $PROMPT_SILENT -eq $YES ]; then
        if [ -z "$default" ]; then
            msg_err "no default value available"
        else
            msg "$query: $default\n" "-"
            ANSWER=$default
            return
        fi
    fi
    unset ANSWER
    # allow SIGINT to interrupt
    trap - SIGINT
    while [ -z "$ANSWER" ]; do
        if [ -z "$default" ]; then
            msg "$query:" "-"
        else
            msg "$query [$default]:" "-"
        fi
        if [ "$1" = "-s" ] && [ -z "$BASH" ]; then
            trap 'stty echo' EXIT
            stty -echo
            read ANSWER
            stty echo
            trap - EXIT
        else
            read $* ANSWER
        fi
        if [ "$ANSWER" = "q!" ]; then
            exit 1
        elif [ -z "$ANSWER" ] && [ -n "$default" ]; then
            ANSWER=$default
        fi
        [ "$1" = "-s" ] && echo
    done
    trap '' SIGINT
}

prompt_boolean() {
    unset ANSWER
    while [ -z "$ANSWER" ]; do
        prompt "$1 (y/n)" ${2:-y}
        case "$ANSWER" in
        n*|N*) ANSWER=$NO; break ;;
        y*|Y*) ANSWER=$YES; break ;;
        *) unset ANSWER ;;
        esac
    done
}

msg_bold() {
    tput bold
    msg_format "$1"
    tput sgr0
}
