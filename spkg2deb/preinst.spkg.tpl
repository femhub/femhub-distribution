#! /bin/bash
set -e

if [ "$FEMHUB_LOCAL" = "" ]; then
    echo "FEMHUB_LOCAL undefined ... exiting";
    exit 1
fi
