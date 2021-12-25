"""
Author: Ege Ozan Ozyedek
Python Version: 3.8
"""


import sys
import socket


class FileDownloader(object):
    """
    The file downloder class, which first obtains the target list given an index file, and then attempts
    to download the files in said target list. The socket library is used, and HTTP GET and HEAD calls are
    utilized to obtain the file/information about the file.
    """


    def __init__(self, target, index_range=None, index_file=False):
        """
        Initializes the class
        :param target: the target string, which contains both the host and the file directory
        :param index_range: An index range, which when specified is passed on as an HTTP request to the host
        :param index_file: Identifies whether the given target is an index file or not, if it is, it obtains the target list
        """

        self.host, self.file = target.split('/', 1)  # obtain host and file, both will be used in HTTP Requests

        self.index_range = index_range  # either the given range input or None
        if index_range:
            self.lower_index, self.upper_index = self.index_range.split("-")

        # GET request string, takes host, file and range as args
        self.GET = lambda h, f, r: f"GET /{f} HTTP/1.1\r\nHost: {h}\r\nRange: bytes={r}\r\n\r\n"
        # HEAD request string, takes host, file and range as args
        self.HEAD = lambda h, f: f"HEAD /{f} HTTP/1.1\r\nHost: {h}\r\n\r\n"

        self.target_list = None
        self.index_file = None

        # if this is an index file, we send a GET request right away and obtain a target list to download files from
        if index_file:

            self.index_file = True
            self.index_range = index_range

            print(f"\nIndex File URL: {target}")

            if self.index_range:
                print(f"Input Byte Range: {self.lower_index} - {self.upper_index}")

            client = socket.socket()  # create socket
            client.connect((self.host, 80))  # connect to the host at port 80
            request_string = self.GET(self.host, self.file, None)  # create the GET request string from tha above function, specified range to None
            client.send(request_string.encode("utf-8"))  # send request
            response = self._receive_data(client=client, decode=True)  # receive response
            client.close()  # close socket
            header, content = response.split("\r\n\r\n", 1)  # split the respons with the mandatory empty line that divides content and header
            self.target_list = content.strip().split("\n")  # create the target list by splitting the content by next lines

            print(f"Index file downloaded.\n{len(self.target_list)} files found in the index.")


    def get_request(self, port=80):
        """
        Sends a GET request to the host initialized, opens socket -> requests -> receives response -> closes socket
        :param port: Port number where the connection will be held, default 80
        :return: the HTTP response
        """
        client = socket.socket()  # create socket
        client.connect((self.host, port))  # connect to the host at port 80
        request_string = self.GET(self.host, self.file, self.index_range)  # create the GET request string from tha above function
        client.send(request_string.encode("utf-8"))  # send request
        response = self._receive_data(client=client, decode=True)  # receive response
        client.close()  # close socket
        return response


    def head_request(self, port=80):
        """
        Sends a HEAD request to the host initialized, opens socket -> requests -> receives response -> closes socket
        :param port: Port number where the connection will be held, default 80
        :return: the HTTP response
        """
        client = socket.socket()  # create socket
        client.connect((self.host, port))  # connect to the host at port 80
        request_string = self.HEAD(self.host, self.file)  # create the HEAD request string from tha above function
        client.send(request_string.encode("utf-8"))  # send request
        response = self._receive_data(client=client, decode=True)  # receive response
        client.close()  # close socket
        return response


    @staticmethod
    def _receive_data(client, decode=False):
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

        return response if not decode else response.decode("utf-8")


    @staticmethod
    def _get_info(header):
        """
        Small method to turn the header into a dictionary and obtain the status message
        :param header: the header string
        :return: the HTTP status message and the header in dictionary format
        """
        temp = [i.split(": ") for i in header.split("\r\n")]
        return temp[0][0], dict(temp[1:])


    def _download(self):
        """
        Downloads the given file from host. First, a HEAD request is made. The HTTP message is analyzed and the next move is made with the message
        in mind. If it's OK, then a GET request is made and the contents of the file are written to a txt file. If it's Partial Content, the partial
        content is downloaded in similar fashion. If the range is not satisfied, then an error is displayed on the console, no other requests are
        made. Finally in similar fashion, if any other is obtained, an error is displayed on console. After these conditions, the download attempt
        moves to the next file.
        """

        response = self.head_request()  # make HEAD request
        header, _ = response.split("\r\n\r\n", 1)  # get header
        message, header_dict = self._get_info(header)  # obtain the message, and header as a dictionary for future use

        # check the message
        if message == "HTTP/1.1 200 OK":

            content_length = header_dict["Content-Length"]

            if self.index_range is not None and int(content_length) <= int(self.lower_index):
                print(f"COULD NOT DOWNLOAD: File could not be downloaded, file size is smaller than start index (size = {content_length}).")
                return


            response = self.get_request()
            header, content = response.split("\r\n\r\n", 1)
            _, header_dict = self._get_info(header)


            # download the data nb
            file_name = self.file.split("/")[-1]
            with open(file_name, "w") as text_file:
                text_file.write(content)

            content_length = header_dict["Content-Length"]
            if self.index_range is not None:
                upper = int(self.lower_index) + int(content_length) - 1
                info_str = f"(range = {self.lower_index} - {upper})"
            else:
                info_str = f"(size = {content_length})"


            print(f"DOWNLOADED: File downloaded with the name {file_name} {info_str}.")

        else:
            print("FAILED: File not found.")


    def start_downloads(self):
        """
        The target list gets iterated over and an attempt to download the file is made. The same class is used to download these files, but they are
        not index files so this is not entered in the constructor. They download the file and their purpose is met.
        """

        # this loop only runs if this instance of the class is responsible for the index file
        if self.index_file:

            print("\n|----------------------Starting Download Attempts----------------------|\n")

            i = 1
            for target in self.target_list:
                downloader = FileDownloader(target, self.index_range)
                print(f"{i}. Attempting to download target {target}.")
                downloader._download()
                i += 1
                print()



def main():
    """
    The main function, obtains the command line arguments and passes them to the correct places.
    """

    args = sys.argv[1:]  # get all args except the file name
    target = args[0]
    index_range = args[1] if len(args) > 1 else None

    downloader = FileDownloader(target, index_range, index_file=True)
    downloader.start_downloads()


if __name__ == '__main__':
    main()

