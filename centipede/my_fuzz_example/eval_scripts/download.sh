#!/bin/bash

machines=("pc851" "pc811")

for machine in ${machines[@]}; do
    echo $machine
    rsync -aPrzWm --include='random-result*' --include='random-result*/*' --include='*/' --exclude='*' --rsync-path="sudo rsync" vlivinsk@$machine.emulab.net:/var/lib/docker/volumes/ $machine
done
