#!/usr/bin/env python3
"""
Various host utilities around docker
"""
import sys
import os
import argparse
import logging
from fnmatch import fnmatch

import docker
from docker.models.containers import Container


__author__ = 'David Nugent'
__version__ = '2020.03.11.00'


COMPOSE_SERVICE = 'com.docker.compose.service'
COMPOSE_PROJECT = 'com.docker.compose.project'
COMPOSE_WORKDIR = 'com.docker.compose.project.working_dir'


def compose_get(c: Container, var: str, default: str=''):
    return c.labels[var] if c.labels and var in c.labels else default


def match_container(c: Container, service: str, patterns: list, running: bool=False, exited: bool=False):
    if running and c.status != 'running':
        return False
    if exited and c.status != 'exited':
        return False
    if patterns:
        for pattern in patterns:
            if c.id and c.id.startswith(pattern):
                break
            if fnmatch(c.name, pattern):
                break
            if service and fnmatch(service, pattern):
                break
        else:
            return False
    return True


def run(client, argv: argparse.Namespace) -> int:
    ran_something = 0
    cmd = ' '.join(argv.cmd)
    logging.debug(f"Container {'exec' if argv.exec else 'run'}: '{cmd}'")
    for containr in client.containers.list():
        exit_code = 0
        result = None
        # type: Container
        project = compose_get(containr, COMPOSE_PROJECT)
        service = compose_get(containr, COMPOSE_SERVICE)
        if match_container(containr, service, argv.container) and (not argv.project or argv.project == project):
            logging.debug(f"Matched container {containr.name} id={containr.id}")
            stdout = stderr = False if argv.detach else True
            stdin = tty = False
            workdir = None  # compose_get(containr, COMPOSE_WORKDIR, os.getcwd())
            if argv.exec:
                if containr.status != 'running':
                    logging.warning(f"exec: container {containr.name} is not running - skipped")
                else:

                    result = containr.exec_run(cmd, stdout=stdout, stderr=stderr, stdin=stdin,
                                               tty=tty, detach=argv.detach, workdir=workdir)
                    ran_something += 1
                    exit_code = result.exit_code
                    if exit_code:
                        logging.warning(f"Container {containr.name} returned exit code {exit_code}")
                    result = result.output.decode('utf-8')

            else:
                remove = True
                containr = client.containers.run(containr.image, cmd, stdout=stdout, stderr=stderr, stdin=stdin,
                                                 tty=tty, detach=argv.detach, remove=remove)
                result = '' if argv.detach else containr.logs()
                ran_something += 1

            sys.stdout.write(result)

    return 0 if ran_something else 1


def container(client, argv: argparse.Namespace) -> int:
    """
    Execute container functions
    :param argv: command line namespace
    :return: exit code to OS
    """
    if argv.ls:
        logging.debug("Listing containers")
        found = 0
        for containr in client.containers.list():
            project = compose_get(containr, COMPOSE_PROJECT)
            service = compose_get(containr, COMPOSE_SERVICE)
            if match_container(containr, service, argv.patterns, argv.running, argv.exited) and \
                (not argv.project or argv.project == project):
                logging.debug(f"Matched container {containr.name} id={containr.id}")
                found += 1
                if not argv.query:
                    if argv.short:
                        print(f"{containr.id[:8]},{containr.name},{service},{containr.status},{','.join(containr.image.tags)}")
                    else:
                        print(f"Name: {containr.name}")
                        print(f"Image: {', '.join(containr.image.tags)}")
                        print(f"Id: {containr.id[:8]} ({containr.id})")
                        print(f"Status: {containr.status}")
                        if containr.labels:
                            nl = '\n'
                            labels = [f'  {k}: {v}{nl}' for k, v in containr.labels.items()]
                            print(f"Labels:{nl}{''.join(labels)}")
        if argv.query and not found:
            return 1

    else:
        logging.error(f"{argv.prog}: no operation quested (see container --help)")

    return 0


def parse_args(prog: str, args: list):
    """
    argparse support
    :param prog: program name
    :param args: program args
    :return: return code to OS
    """
    prog = os.path.splitext(os.path.basename(prog))[0]
    parser = argparse.ArgumentParser(prog=prog, description=__doc__)

    parser.add_argument('-V', '--version', action='version', version=__version__)
    parser.add_argument('-v', '--verbose', action='store_true', default=False,
                        help='increase verbosity')
    parser.add_argument('-q', '--query', action='store_true',
                        help='query only, 0 exit status on success else 1')
    parser.add_argument('-l', '--log', action='store',
                        help='log to named file')
    parser.add_argument('-p', '--project', action='store',
                        help='filter by project name')

    subparsers = parser.add_subparsers(title='command', dest='command')
    container_parser = subparsers.add_parser('container',
                                             help='container related functions')

    container_parser_group = container_parser.add_mutually_exclusive_group()
    container_parser_group.add_argument('-l', '--ls', action='store_true',
                                        help='list container info')

    container_parser_status = container_parser.add_mutually_exclusive_group()
    container_parser_status.add_argument('-r', '--running', action='store_true',
                                  help='running containers only')
    container_parser_status.add_argument('-x', '--exited', action='store_true',
                                  help='exited containers only')
    container_parser.add_argument('-s', '--short', action='store_true',
                                  help='brief output only')
    container_parser.add_argument('patterns', action='store', nargs='*',
                                  help='match on container name, id or compose service')

    run_parser = subparsers.add_parser('run',
                                       help='run (or exec) a command in a running container')
    run_parser.add_argument('-c', '--container', action='store', nargs='*',
                            help='(one or more allowed) match container name, id or service')
    run_parser.add_argument('-d', '--detach', action='store_true',
                            help='detach instead of waiting until completion')
    run_parser.add_argument('-e', '--exec', action='store_true',
                            help='exec command in running container, do not start new')

    run_parser.add_argument('cmd', action='store', nargs='+',
                            help='command to exec/run')

    argv = parser.parse_args(args)

    if not argv.command:
        parser.print_help(sys.stdout)
        exit(3)
    try:
        command_func = globals()[argv.command]
        if not callable(command_func):
            print(f"{prog}: not a valid command: {argv.command}")
            exit(2)
        argv.prog = prog
        return command_func, argv
    except KeyError:
        print(f"{prog}: unknown command: {argv.command}")
        exit(2)


def main(prog: str, args: list) -> int:
    """
    :param prog: program name (sys.argv[0]
    :param args: program args
    :return: return code to OS
    """
    client = docker.from_env()

    command, argv = parse_args(prog, args)
    if argv.log:
        fh = logging.FileHandler(argv.log)
        fh.setLevel(logging.DEBUG)
        logging.getLogger().addHandler(fh)
        logging.info('---')
    if argv.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    return command(client, argv)


if __name__ == '__main__':
    logging.basicConfig(
        format="%(asctime)s %(levelname)-9s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        level=logging.INFO
    )
    exit(main(sys.argv[0], sys.argv[1:]))
