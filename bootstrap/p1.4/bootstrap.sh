#!/usr/bin/env bash
# shellcheck disable=SC2034
# shellcheck source=.bootstrap.sh

# The Python executable to use during the build of the Python virtual environment. May be hardcoded to a path
PYTHON="python"
# The Python executable to run in the created virtual environment. DO NOT HARDCODE path. Must be similar to:
# python, python2, python3, python2.7, etc.
BOOTSTRAP_PYTHON="python"
ENTRYPOINT_INSTALL="bootstrap_install.py"
ENTRYPOINT_UNINSTALL="bootstrap_uninstall.py"
ENTRYPOINT_UPGRADE="bootstrap_upgrade.py"

if [ "$1" == "install" ]; then
  ENTRYPOINT="${ENTRYPOINT_INSTALL}"
elif [ "$1" == "uninstall" ]; then
  ENTRYPOINT="${ENTRYPOINT_UNINSTALL}"
elif [ "$1" == "upgrade" ]; then
  ENTRYPOINT="${ENTRYPOINT_UPGRADE}"
else
  cat << EOM
Bootstrap operations for MapR software

Usage: bootstrap.sh COMMAND [OPTIONS]
Commands:
  install | uninstall | upgrade  Run command - must be supplied

Options:
  --help                         List help for the specified command

Examples:
  bootstrap.sh install           Run installer
  bootstrap.sh uninstall         Run uninstaller
  bootstrap.sh upgrade           Run bootstrap upgrade
  bootstrap.sh install --help    Get installation options
  bootstrap.sh uninstall --help  Get uninstallation options
  bootstrap.sh upgrade --help    Get bootstrap upgrade options

EOM
  exit 1
fi


pushd ${0%/*} > /dev/null || (echo "ERROR: Could not pushd to current directory" && exit 1)
WORKING_DIR=$(pwd)
VIRTUALENV="${WORKING_DIR}/virtualenv"
ACTIVATE="${VIRTUALENV}/bin/activate"
REQ="${WORKING_DIR}/src/common/mapr_conf/requirements.txt"
COMMAND="${WORKING_DIR}/src/${ENTRYPOINT}"
popd > /dev/null || (echo "ERROR: Could not popd" && exit 1)
source "${WORKING_DIR}/.bootstrap.sh"
shift 1
${BOOTSTRAP_PYTHON} "${COMMAND}" $@
