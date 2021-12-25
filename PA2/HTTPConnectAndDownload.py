"""
Author: Ege Ozan Ozyedek
Python Version: 3.8
"""


import logging
import socket
from threading import Thread
import math




class HTTPConnectAndDownload:
    """
    This class manages HTTP GET and HEAD requests, and also downloads files in parallel using threading. Only the socket library
    is used for connection to the server and to acquire data.
    """


    def __init__(self, target, thread_no):
        """
        Initializes the class
        :param target: the target string, which contains both the host and the file directory
        :param thread_no: number of threads to be utilized for this connection
        """

        self.host, self.file = target.split('/', 1)  # obtain host and file, both will be used in HTTP Requests
        self.thread_no = int(thread_no)

        # GET and HEAD request strings; host, file and range as args
        self.__GET = lambda byte_range: f"GET /{self.file} HTTP/1.1\r\nHost: {self.host}\r\nRange: bytes={byte_range}\r\n\r\n"
        self.__HEAD = f"HEAD /{self.file} HTTP/1.1\r\nHost: {self.host}\r\n\r\n"

        # logging for console
        logging.basicConfig(format="%(message)s", level=logging.INFO)



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

        message, header_dict, content = self._get_info(response)  # get info such as the header and content

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

        message, header_dict, _ = self._get_info(response) # get info such as the header and content

        return message, header_dict



    @staticmethod
    def _get_info(response):
        """
        Given a response from the server to the request, this method obtains the content and header seperately. It also seperates the message
        and creates a dictionary out of the header.
        :param response: The response for the GET/HEAD request sent over the socket to the server.
        :return: The HTTP message, the header in dictionary format, and the content of the file
        """

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
        in mind. If it's OK, then the parallel download method is used to send GET requests in parallel and download the file. If any other message
        is obtained, an error is displayed on console. After these conditions, the download attempt moves to the next file.
        """

        message, header_dict = self._head_request()  # make HEAD request

        # check the message
        if message == "HTTP/1.1 200 OK":

            content_length = int(header_dict["Content-Length"])

            # below is a bunch of math necessary for the given condition in the assignment, here we decide on the byte ranges
            n_div_k = math.floor(content_length/self.thread_no)
            first_n = content_length - self.thread_no * n_div_k
            bytes_per_thread = [n_div_k + 1] * first_n + [n_div_k] * (self.thread_no - first_n)

            # download the files in target, using threading
            contents = self._download_parallel(bytes_per_thread)


            # write to file
            file_name = self.file.split("/")[-1]
            with open("test/" + file_name, "w") as out_file:
                for i in range(self.thread_no):
                    out_file.write(contents[i])
                out_file.close()

            logging.info(f"DOWNLOADED \u2713 : File downloaded successfully. | File Name: {file_name} | Content Length : {content_length}")

        else:
            logging.info("FAILED \u02DF : File not found.")




    def _download_parallel(self, bytes_per_thread):
        """
        This method downloads the contents of the target file in parallel. Using the given bytes per thread, byte ranges are determined and threads
        are assigned. Then, each thread sends a GET request, with the determined range of bytes. Then the contents of these requests are stored in a
        dictionary for writing later.
        :param bytes_per_thread: A list that contains information on how many bytes each thread has to download
        :return: the contents of the file, downloaded parallel
        """

        # initialize needed data structures
        threads = list()
        contents = dict()
        byte_ranges = list()

        # start from 0th byte
        start_byte = 0

        # initialize threads and also calculate the byte ranges
        for i, byte in zip(range(self.thread_no), bytes_per_thread):

            end_byte = start_byte + byte - 1
            byte_range = f"{start_byte}-{end_byte}"
            byte_ranges.append(byte_range)
            start_byte = end_byte + 1

            t = Thread(target=self.__thread_process, args=(i, byte_range, contents))
            threads.append(t)


        # start thread processes
        logging.info(f"--Starting {self.thread_no} Threads--")
        for thread in threads:
            thread.start()

        # wait for all threads to end, print affirmation
        for i, thread in enumerate(threads):
            thread.join()
            logging.info(f"\u00B7 Download Completed on Thread {i} | Byte Range: {byte_ranges[i]} | Length: {bytes_per_thread[i]}")


        return contents



    def __thread_process(self, i, byte_range, contents):
        """
        This method is the thread process, which simply sends a GET request and then collects the content of the request to a dictionary
        :param i: Thread index
        :param byte_range: The assigned byte range for the thread
        :param contents: the mutable contents dictionary
        """

        contents[i] = self._get_request(byte_range=byte_range)[-1]



