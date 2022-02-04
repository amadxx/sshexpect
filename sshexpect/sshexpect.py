"""
pexpect.spawn functionality for asyncssh

LICENSE:
    The MIT License (MIT)

    Copyright (c) 2022 Dmytro Pavliuk

    Permission is hereby granted, free of charge, to any person obtaining a copy
    of this software and associated documentation files (the "Software"), to deal
    in the Software without restriction, including without limitation the rights
    to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
    copies of the Software, and to permit persons to whom the Software is
    furnished to do so, subject to the following conditions:

    The above copyright notice and this permission notice shall be included in all
    copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
    AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
    OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
    SOFTWARE.
"""

import os
import typing
import threading
import pexpect.fdpexpect

HAVE_ASYNCSSH = False
HAVE_PARAMIKO = False


try:
    import asyncssh
    HAVE_ASYNCSSH = True
except ImportError:
    pass

try:
    import paramiko
    HAVE_PARAMIKO = True
except ImportError:
    pass

class SSHClientProcessExpect(pexpect.fdpexpect.fdspawn):
    "Fdspawn-based class for asyncssh process"
    def __init__(self, fd: int, proc: "asyncssh.process.SSHClientProcess", *args, **kwargs) -> None:
        super().__init__(fd, *args, **kwargs)
        self.ssh_proc = proc

    def terminate(self, force=False):
        "Terminate the process"
        if force:
            self.ssh_proc.kill()
        else:
            self.ssh_proc.terminate()

    def send(self, s):
        "Write to fd, return number of bytes written"
        self.ssh_proc.stdin.write(f"{s}")
        return len(s)

    def sendline(self, s):
        "Write to fd, return number of bytes written"
        data = f"{s}{os.linesep}"
        self.ssh_proc.stdin.write(data)
        return len(data)

    def write(self, s):
        "Write to fd, return None"
        return self.ssh_proc.stdin.write(f"{s}")

    def expect(self, *args, **kw):
        "Run fdexpect.expect asynchronously"
        kw["async_"] = True
        return super().expect(*args, **kw)


async def spawn_asyncssh(connection: "asyncssh.SSHClientConnection"
                        , *args, **kw) \
                        -> SSHClientProcessExpect:
    "Spawn process using SSHClientConnection.create_process"

    # Prepare pipe to redirect process stdout to fdexpect
    child_fd, kw["stdout"] = os.pipe()

    # Set default terminal to request PTY
    kw["term_type"] = kw.get("term_type", "vt100")

    # Spawn remote process
    proc = await connection.create_process(*args, **kw)

    # Create fdspawn child
    return SSHClientProcessExpect(child_fd, proc)


class ParamikoChannelExpect(pexpect.fdpexpect.fdspawn):
    "Fdspawn-based class for paramiko channel"
    def __init__(self, fd: int, proc: "paramiko.Channel", *args, **kwargs) -> None:
        super().__init__(fd, *args, **kwargs)
        self.ssh_proc = proc

    def terminate(self, force=False):
        "Terminate the process"
        self.ssh_proc.close()

    def send(self, s):
        "Write to fd, return number of bytes written"
        return self.ssh_proc.send(s)

    def sendline(self, s):
        "Write to fd, return number of bytes written"
        data = f"{s}{os.linesep}"
        return self.ssh_proc.send(data)

    def write(self, s):
        "Write to fd, return None"
        self.ssh_proc.send(s)


def spawn_paramiko(connection: "paramiko.SSHClient"
                  , command: typing.AnyStr
                  , **kw) \
                    -> ParamikoChannelExpect:
    "Spawn process using SSHClientConnection.create_process"

    # Prepare pipe to redirect process stdout to fdexpect
    child_fd, stdout = os.pipe()

    kwkeys = {
        "session": ("window_size", "max_packet_size", "timeout"),
        "pty": ("term", "width", "height", "width_pixels", "height_pixels"),
        "spawn": ("buff_size",)
    }

    kwmap = {}

    for kwdest, kwnames in kwkeys.items():
        kwargs = {}
        for name in kwnames:
            if name in kw:
                kwargs[name] = kw[name]
        kwmap[kwdest] = kwargs

    # Open session
    session: "paramiko.Channel" = connection.get_transport().open_session(**kwmap["session"])

    # Request PTY
    session.get_pty(**kwmap["pty"])

    # Spawn remote process
    session.exec_command(command)

    def redirect():
        "Thread for redirecting stdout from session to pipe"
        buff_size = kwmap["spawn"].get("buff_size", 2048)

        while True:
            if session.recv_ready():
                os.write(stdout, session.recv(buff_size))
            if session.exit_status_ready():
                break

    # Redirect stdout
    thread = threading.Thread(target=redirect)

    # Thread will finish after terminate() call
    thread.start()

    return ParamikoChannelExpect(child_fd, session)


def spawn(connection: "typing.Union[asyncssh.SSHClientConnection, paramiko.SSHClient]"
         , *args, **kw) \
         -> typing.Union[SSHClientProcessExpect, ParamikoChannelExpect]:
    "Spawn SSH process"

    if HAVE_ASYNCSSH and issubclass(type(connection), asyncssh.SSHClientConnection):
        return spawn_asyncssh(connection, *args, **kw)

    if HAVE_PARAMIKO and issubclass(type(connection), paramiko.SSHClient):
        return spawn_paramiko(connection, *args, **kw)

    raise ValueError("Unsupported connection type")
