package utils

import (
	"net"
)

func GetFreePort() (int, error) {
	addr, err := net.ResolveTCPAddr("tcp", "localhost:0")
	if err != nil {
		return 0, nil
	}

	tcp, err := net.ListenTCP("tcp", addr)
	defer tcp.Close()
	if err != nil {
		return 0, err
	}
	return tcp.Addr().(*net.TCPAddr).Port, nil
}
