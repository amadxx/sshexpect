# sshexpect

## Overview

This library adapts `pexpect` to work with `asyncssh` and `paramiko`

## asyncssh example

```python
import asyncssh
import sshexpect

connection = await asyncssh.connect(...)
child = await sshexpect.spawn(connection, "bash")

await child.expect(...)
child.sendline(...)

child.terminate()
```

## paramiko example

```python
import paramiko
import sshexpect

connection = paramiko.SSHClient()
connection.connect(...)

child = sshexpect.spawn(connection, "bash")

child.expect(...)
child.sendline(...)

child.terminate()
```

## Installation 
```shell
pip install git+https://github.com/amadxx/sshexpect.git
```

## License

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