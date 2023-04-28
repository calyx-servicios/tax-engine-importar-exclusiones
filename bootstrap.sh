#!/bin/bash

# run various pieces of initialization code here
# ...
echo "COMMAND" ${COMMAND}

init_app() {
    echo "=====<Starting == Bot >====="
    cd /code/app
    exec python main.py
}

jupyter_app() {
    echo "Start Jupyterlab"
    exec jupyter lab --allow-root --no-browser --ip=0.0.0.0 --ServerApp.allow_password_change=False
}

case "${COMMAND}" in
  init) init_app;;
  jupyter) jupyter_app;;
  *) echo "No command";;
esac