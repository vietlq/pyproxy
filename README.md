pyproxy
=======

A Simple Python TCP Proxy Server With Ability to Broadcast Auxiliary Messages

#### Starting an instance of EchoServer

`./async_echo.py localhost 9090`

#### Starting an instance of TcpProxyServer with no message injection capability

The main port is `8080`.

`./async_proxy.py 8080 localhost:9090`

#### Starting an instance of TcpProxyServer with message injection capability

The main port is `8080`.

The injection port is `8181`. Anything sent to this port will be broadcasted to all clients connected to the main port `8080`.

`./async_proxy.py 8080 localhost:9090 8181`

#### Notes

You may use `telnet` to test small messages manually.

Never ever use `telnet` to send receive files or messages. Use `netcat` instead.

DO:

`nc 127.0.0.1 8181 < /tmp/original_file.pdf`

DON'T:

`telnet 127.0.0.1 8181 < /tmp/original_file.pdf`

DO:

`nc 127.0.0.1 8080 > /tmp/received_file.pdf`

DON'T:

`telnet 127.0.0.1 8080 > /tmp/received_file.pdf`

*The reason*: I witnessed `telnet` sending some padding bytes or dropping some messages
