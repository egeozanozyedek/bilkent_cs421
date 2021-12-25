"""
Author: Ege Ozan Ozyedek
Python Version: 3.8
"""


import sys
import socket
import threading
from ConnectAndDownload import ConnectAndDownload


class ParallelFileDownloader(ConnectAndDownload):

    def __init__(self, index_file, connection_count):

        super().__init__(index_file, None)

        print(f"\nIndex File URL: {index_file}\nParalell Connections to be Established: {connection_count}")

        message, content, header_dict, _ = super()._get_request()
        self.target_list = content.strip().split("\n")  # create the target list by splitting the content by next lines

        print(f"Index file downloaded.\n{len(self.target_list)} files found in the index.")

        print(self.target_list)



    def _download_parallel(self, target):

        # connect and download instances with different ranges

        pass


    def start_downloads(self):

        print("\n|----------------------Starting Download Attempts----------------------|\n")

        i = 1
        for target in self.target_list:
            self._download_parallel(target)
            print(f"{i}. Attempting to download target {target}.")

            i += 1
            print()



def main():
    """
    The main function, obtains the command line arguments and passes them to the correct places.
    """

    args = sys.argv[1:]  # get all args except the file name
    index_file, connection_count = args[0], args[1]
    print(args[0], args[1])
    PFD = ParallelFileDownloader(index_file, connection_count)






if __name__ == '__main__':
    main()