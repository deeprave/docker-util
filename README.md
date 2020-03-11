# docker-util

## Description

This utility is is a utility suite that provides a convenient (for me)
command line interface for running and exited docker containers.
The intended use is on a docker host, to provide a way to manage
local containers.

On outset, this was just my way of exploring the docker python api
and providing some useful functions for automated interaction with
containers running on the host.

## Status

This utility is incrementally developed, adding functions when
required.

## Usage

    usage: dockerutil [-h] [-V] [-v] [-q] [-l LOG] [-p PROJECT] {container,run} ...
       Various host utilities around docker

    optional arguments:
      -h, --help                    show this help message and exit
      -V, --version                 show program's version number and exit
      -v, --verbose                 increase verbosity
      -q, --query                   query only, 0 exit status on success else 1
      -l|--log LOG                  log to named file
      -p|--project                  PROJECT filter by project name

    command:
      container [patterns ...]      container related functions
        -l, --ls                    list container info
        -r, --running               running containers only
        -x, --exited                exited containers only
        -s, --short                 brief output only

      run [cmd]                     run (or exec) a command in a running container
        -c|--container [CONTAINER [CONTAINER ...]]
                                    match on container name, id or service
        -d, --detach                detach instead of waiting until completion
        -e, --exec                  exec command in running container, do not start new
