"""
Author: Ege Ozan Ozyedek
Python Version: 3.8
"""


import logging
import socket
from threading import Thread
import math




class ConnectAndDownload(object):
    """

    """


    def __init__(self, target, thread_no):
        """
        Initializes the class
        :param target: the target string, which contains both the host and the file directory
        """

        self.host, self.file = target.split('/', 1)  # obtain host and file, both will be used in HTTP Requests
        self.thread_no = int(thread_no)

        # GET and HEAD request strings; host, file and range as args
        self.__GET = lambda byte_range: f"GET /{self.file} HTTP/1.1\r\nHost: {self.host}\r\nRange: bytes={byte_range}\r\n\r\n"
        self.__HEAD = f"HEAD /{self.file} HTTP/1.1\r\nHost: {self.host}\r\n\r\n"



    def _get_request(self, byte_range=None, port=80):
        """
        Sends a GET request to the host initialized, opens socket -> requests -> receives response -> closes socket
        :param byte_range: Range for the GET request, in terms of bytes
        :param port: Port number where the connection will be held, default 80
        :return: the HTTP response
        """
        client = socket.socket()  # create socket
        client.connect((self.host, port))  # connect to the host at port 80
        request_string = self.__GET(byte_range)  # create the GET request string from tha above function
        client.send(request_string.encode("utf-8"))  # send request
        response = self._receive_data(client=client)  # receive response
        client.close()  # close socket

        message, header_dict, content = self._get_info(response)

        return message, header_dict, content


    def _head_request(self, port=80):
        """
        Sends a HEAD request to the host initialized, opens socket -> requests -> receives response -> closes socket
        :param port: Port number where the connection will be held, default 80
        :return: the HTTP response
        """
        client = socket.socket()  # create socket
        client.connect((self.host, port))  # connect to the host at port 80
        request_string = self.__HEAD  # create the HEAD request string from tha above function
        client.send(request_string.encode("utf-8"))  # send request
        response = self._receive_data(client=client)  # receive response
        client.close()  # close socket

        message, header_dict, _ = self._get_info(response)

        return message, header_dict



    @staticmethod
    def _get_info(response):

        header, content = response.split("\r\n\r\n", 1)

        temp = [i.split(": ") for i in header.split("\r\n")]
        message, header_dict = temp[0][0], dict(temp[1:])

        return message, header_dict, content


    @staticmethod
    def _receive_data(client, decode=True):
        """
        Recieves HTTP response 1024 bytes at a time in a for loop, until no data is recieved
        :param client: The socket (client) that the response will be recieved from
        :param decode: The response comes in bytes, hence the user can specify for the incoming bytes to be decoded in utf-8
        :return: the HTTP response
        """

        response = b""
        while True:
            r = client.recv(1024)
            if not r:
                break
            response += r

        return response.decode("utf-8") if decode else response





    def _download(self):
        """
        Downloads the given file from host. First, a HEAD request is made. The HTTP message is analyzed and the next move is made with the message
        in mind. If it's OK, then a GET request is made and the contents of the file are written to a txt file. If it's Partial Content, the partial
        content is downloaded in similar fashion. If the range is not satisfied, then an error is displayed on the console, no other requests are
        made. Finally in similar fashion, if any other is obtained, an error is displayed on console. After these conditions, the download attempt
        moves to the next file.
        """

        message, header_dict = self._head_request()  # make HEAD request

        # check the message
        if message == "HTTP/1.1 200 OK":

            content_length = int(header_dict["Content-Length"])
            n_div_k = math.floor(content_length/self.thread_no)
            first_n = content_length - self.thread_no * n_div_k
            bytes_per_thread = [n_div_k + 1] * first_n + [n_div_k] * (self.thread_no - first_n)


            # print(content_length, self.thread_no, bytes_per_thread)


            contents = self._download_parallel(bytes_per_thread)

            file_name = self.file.split("/")[-1]

            with open("test/" + file_name, "w") as out_file:
                for i in range(self.thread_no):
                    out_file.write(contents[i])
                out_file.close()



            print(f"DOWNLOADED: File downloaded with the name {file_name}.")

        else:
            print("FAILED: File not found.")




    def _download_parallel(self, bytes_per_thread):

        logging.basicConfig(format="(%(asctime)s.%(msecs)02d) %(message)s", level=logging.INFO,
                            datefmt="%H:%M:%S")

        threads = list()
        contents = dict()
        byte_ranges = list()

        start_byte = 0

        for index, byte in zip(range(self.thread_no), bytes_per_thread):
            end_byte = start_byte + byte - 1
            byte_range = f"{start_byte}-{end_byte}"
            byte_ranges.append(byte_range)
            t = Thread(target=self.__thread_process, args=(index, byte_range, contents))
            threads.append(t)

            start_byte = end_byte + 1

        logging.info(f"Starting {self.thread_no} Threads")
        for thread in threads:
            thread.start()

        for index, thread in enumerate(threads):
            thread.join()
            logging.info(f"Download Completed on Thread {index} | Byte Range: {byte_ranges[index]} | Length: {bytes_per_thread[index]}")


        return contents



    def __thread_process(self, index, byte_range, contents):
        contents[index] = self._get_request(byte_range=byte_range)[-1]



