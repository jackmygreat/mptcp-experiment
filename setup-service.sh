#!/bin/bash

if [ "$1" = 'k' ];then
  echo "Killing ptools daemon"
  systemctl disable ptools-daemon.service
  systemctl kill -s SIGKILL ptools-daemon.service
  rm -rf /etc/systemd/system/ptools-daemon.service
  systemctl daemon-reload
else
  echo "Setup ptools daemon"
  cp ./ptools-daemon.service /etc/systemd/system
  systemctl daemon-reload
  systemctl enable ptools-daemon.service
  systemctl start ptools-daemon.service
fi
