#!/bin/bash

for d in */ ; do
    echo "$d"
    cd "${d}"
    mkdir "Optimized"
    find . -type f -name "*.jpeg" | parallel jpegoptim --dest="./Optimized" --size=9000
    cd ..
    # ls "${d}"*.jpeg | parallel jpegoptim --dest="${d}"Optimized --size=9000
    # jpegoptim "${d}"*.jpeg --size=9000 --dest="${d}Optimized"
done