"""
Author: Ege Ozan Ozyedek
Python Version: 3.8
"""

import logging
import sys
from HTTPConnectAndDownload import HTTPConnectAndDownload


class ParallelFileDownloader(HTTPConnectAndDownload):
    """
    This class, when given a valid index file, downloads all target files in the index file in parallel. It is the child class of
    HTTPConnectAndDownload, and uses its methods for downloads and requests.
    """

    def __init__(self, index_file, thread_no):
        """
        Initializes the parent class, and logs a message for the user
        :param index_file: The index file address which contains all files to be downloaded
        :param thread_no: Number of parallel threads
        """

        super().__init__(index_file, thread_no)

        logging.info(f"\nIndex File URL: {index_file}\nParalell Connections to be Established: {thread_no}")


    def __call__(self, *args, **kwargs):

        message, _, content = super()._get_request() # send a GET request to obtain index file contents

        if message == "HTTP/1.1 200 OK":
            self.target_list = content.strip().split("\n")  # create the target list by splitting the content by next lines

            logging.info(f"Index file downloaded.\n{len(self.target_list)} files found in the index.")

            self._download_all()  # download all target files in the index file

        else:
            logging.info("FAILED: Index file not found.")  # Failed to find index file, abort



    def _download_all(self):
        """
        Downloads all target files in the given index file. Each target file is assigned to a HTTPConnectAndDownload object, then the methods of said
        class is used to download in parallel.
        """

        logging.info("\n|----------------------Starting Download Attempts----------------------|\n")

        i = 1
        for target in self.target_list:

            CAD = HTTPConnectAndDownload(target, self.thread_no)
            logging.info(f"{i}. Attempting to download target {target} \u2193")
            CAD._download()
            i += 1
            logging.info("\n\n")



def main():
    """
    The main function, obtains the command line arguments and passes them to the correct places.
    """

    args = sys.argv[1:]  # get all args except the file name
    index_file, connection_count = args[0], args[1]
    PFD = ParallelFileDownloader(index_file, connection_count)
    PFD()




if __name__ == '__main__':
    main()
