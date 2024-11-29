#!/bin/sh
umask 113;
if [ -z "${IBSJOBNAME}" ]; then
  export IBSJOBNAME=fromtty
fi
sudo /storage/Alphafold/scripts/.alphafold3_deepmind_inference_callee.csh `id -u` "$IBSJOBNAME" "$@"
