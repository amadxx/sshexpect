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
import asyncssh
import pexpect.fdpexpect

class SSHClientProcessExpect(pexpect.fdpexpect.fdspawn):
    "Fdspawn-based class for asyncssh process"
    def __init__(self, fd: int, proc: asyncssh.process.SSHClientProcess, *args, **kwargs) -> None:
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

async def spawn(connection: asyncssh.SSHClientConnection, *args, **kw) -> SSHClientProcessExpect:
    "Spawn process using SSHClientConnection.create_process"

    # Prepare pipe to redirect process stdout to fdexpect
    child_fd, kw["stdout"] = os.pipe()

    # Set default terminal to request PTY
    kw["term_type"] = kw.get("term_type", "vt100")

    # Spawn remote process
    proc = await connection.create_process(*args, **kw)

    # Create fdspawn child
    child = SSHClientProcessExpect(child_fd, proc)

    return child
