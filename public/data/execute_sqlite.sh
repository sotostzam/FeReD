#!/bin/bash

# https://askcodez.com/non-interactive-sqlite3-lutilisation-de-script-bash.html
./sqlite <<EOF
.read q-learning.sql
EOF
