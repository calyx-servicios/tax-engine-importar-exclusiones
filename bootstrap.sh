#!/bin/bash

# run various pieces of initialization code here
# ...
echo "COMMAND" ${COMMAND}

init_app() {
    
    if [ ! -z "$CREATE" ]; then 
      echo "=====Starting Database===="
      wait-for-psql.py ${DB_ARGS[@]} --timeout=30
      cd app
      alembic upgrade head
      cd ..
    fi
    echo "=====<Starting == Bot >====="
    cd /code/app
    exec python main.py
}

jupyter_app() {
   if [ ! -z "$CREATE" ]; then 
      echo "=====Starting Database===="
      wait-for-psql.py ${DB_ARGS[@]} --timeout=30
    fi
    echo "Start Jupyterlab"
    exec jupyter lab --allow-root --no-browser --ip=0.0.0.0 --ServerApp.allow_password_change=False
}

case "${COMMAND}" in
  init) init_app;;
  jupyter) jupyter_app;;
  *) echo "No command";;
esac