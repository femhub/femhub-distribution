# -*- coding: utf-8 *-*
import os
import subprocess
from spkg2deb.ex import CalledProcessError


def check_call(quiet, *popenargs, **kwargs):
    if quiet == True:
        fnull = open(os.devnull, 'w')
        retcode = subprocess.call(stdout=fnull, stderr=fnull,
                                    *popenargs, **kwargs)
        fnull.close()
    else:
        retcode = subprocess.call(*popenargs, **kwargs)
    if retcode == 0:
        return
    raise CalledProcessError(retcode)


def process_command(args, cwd=None):
    if not isinstance(args, (list, tuple)):
        raise RuntimeError("args passed must be in a list")
    check_call(False, args, cwd=cwd)
