# shellcheck disable=SC2034
# shellcheck disable=SC1090
if [[ ! -d "${VIRTUALENV}" ]]; then
    PYTHON_EXEC=$(command -v "${PYTHON}")
    if [[ $? -ne 0 ]]; then
        echo "ERROR: Cannot find python in path. Exiting"
        exit 1
    fi
    PYTHON_DIR=$(dirname "${PYTHON_EXEC}")
    echo "Python found at: ${PYTHON_EXEC}"

    PYTHON_VER=$(${PYTHON} -V 2>&1 | grep -o -e "[1-9]" | head -n 1)
    if [ $? -eq 0 ]; then
      echo "Python major version is: ${PYTHON_VER}"
    else
      echo "ERROR: Could not determine Python version; Will assume Python 3"
      PYTHON_VER=3
    fi

    if [ $PYTHON_VER -ne 3 ]; then
      echo "ERROR: Python version ${PYTHON_VER} is not compatible with this Python 3 program"
      exit 2
    fi

    ${PYTHON} -m venv -h > /dev/null 2>&1
    if [ $? -eq 0 ]; then
      echo "Python 3 venv module is available"
      VENV_AVAIL=3
    else
      echo "ERROR: Python 3 venv module is not available"
      exit 7
    fi

    if [ $PYTHON_VER -ne $VENV_AVAIL ]; then
      echo "WARNING: Something appears to be incorrect in your Python environment and the venv module"
    fi

    echo ""
    echo "Virtual environment does not exist. Creating environment for Python $PYTHON_VER..."
    if [ $PYTHON_VER -eq 3 ]; then
      VE="${PYTHON_EXEC}"
      VE_OPT="-m venv"
    fi

    echo "Executable to create virtual environment is: ${VE}"
    $VE $VE_OPT "${VIRTUALENV}"
    virtualenv_rslt=$?
    if [ $virtualenv_rslt -ne 0 ]; then
        echo "ERROR: There was an error installing the Python virtual environment. Exiting"
        exit 4
    fi

    . "${ACTIVATE}"
    if [[ $? -ne 0 ]]; then
        echo "ERROR: Unable to activate the Python virtual environment. Exiting"
        exit 5
    fi

    ${PIP} install -r "${REQ}"
    if [[ $? -ne 0 ]]; then
        echo "ERROR: Unable to install pip packages. Exiting"
        exit 6
    fi
else
    . "${ACTIVATE}"
    if [[ $? -ne 0 ]]; then
        echo "ERROR: Unable to activate the Python virtual environment. Exiting"
        exit 1
    fi
fi
