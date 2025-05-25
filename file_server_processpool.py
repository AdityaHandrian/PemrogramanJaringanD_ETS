# file_server_processpool.py
from socket import *
import socket
import logging
from file_protocol import FileProtocol
import multiprocessing
import concurrent.futures
import signal
import sys

fp = FileProtocol()

def handle_client(connection, address):
    """Function to handle client requests"""
    logging.warning(f"Process {multiprocessing.current_process().pid} handling connection from {address}")
    buffer = ""
    try:
        connection.settimeout(1800)  # 30 minutes timeout for large files
        while True:
            data = connection.recv(1024*1024)  # 1MB buffer
            if not data:
                break
            buffer += data.decode()
            while "\r\n\r\n" in buffer:
                command, buffer = buffer.split("\r\n\r\n", 1)
                hasil = fp.proses_string(command)
                response = hasil + "\r\n\r\n"
                connection.sendall(response.encode())
    except Exception as e:
        logging.warning(f"Error in process {multiprocessing.current_process().pid}: {str(e)}")
    finally:
        logging.warning(f"connection from {address} closed by process {multiprocessing.current_process().pid}")
        connection.close()


class Server:
    def __init__(self, ipaddress='0.0.0.0', port=8889, pool_size=5):
        self.ipinfo = (ipaddress, port)
        self.pool_size = pool_size
        self.my_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.executor = None

    def signal_handler(self, signum, frame):
        logging.warning("Received interrupt signal, shutting down server...")
        if self.executor:
            self.executor.shutdown(wait=True)
        if self.my_socket:
            self.my_socket.close()
        sys.exit(0)

    def run(self):
        # Setup signal handlers
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        logging.warning(f"server running on ip address {self.ipinfo} with process pool size {self.pool_size}")
        self.my_socket.bind(self.ipinfo)
        self.my_socket.listen(10)
        
        # Create a ProcessPoolExecutor
        with concurrent.futures.ProcessPoolExecutor(max_workers=self.pool_size) as executor:
            self.executor = executor
            try:
                while True:
                    connection, client_address = self.my_socket.accept()
                    logging.warning(f"connection from {client_address}")
                    
                    # Submit the client handling task to the process pool
                    executor.submit(handle_client, connection, client_address)
            except KeyboardInterrupt:
                logging.warning("Server shutting down")
            except Exception as e:
                logging.warning(f"Error in server: {str(e)}")
            finally:
                if self.my_socket:
                    self.my_socket.close()


def main():
    import argparse
    parser = argparse.ArgumentParser(description='File Server with Process Pool')
    parser.add_argument('--port', type=int, default=6667, help='Server port (default: 6667)')
    parser.add_argument('--pool-size', type=int, default=5, help='Process pool size (default: 5)')
    args = parser.parse_args()
    
    svr = Server(ipaddress='0.0.0.0', port=args.port, pool_size=args.pool_size)
    svr.run()


if __name__ == "__main__":
    # This is important for multiprocessing to work properly on some platforms
    multiprocessing.freeze_support()
    logging.basicConfig(level=logging.WARNING, format='%(asctime)s - %(levelname)s - %(message)s')
    main()