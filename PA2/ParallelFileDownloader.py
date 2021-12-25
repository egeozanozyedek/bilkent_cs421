"""
Author: Ege Ozan Ozyedek
Python Version: 3.8
"""


import sys
from ConnectAndDownload import ConnectAndDownload


class ParallelFileDownloader(ConnectAndDownload):

    def __init__(self, index_file, thread_no):

        print(f"\nIndex File URL: {index_file}\nParalell Connections to be Established: {thread_no}")

        super().__init__(index_file, thread_no)




    def __call__(self, *args, **kwargs):

        message, _, content = super()._get_request()

        if message == "HTTP/1.1 200 OK":
            self.target_list = content.strip().split("\n")  # create the target list by splitting the content by next lines

            print(f"Index file downloaded.\n{len(self.target_list)} files found in the index.")

            print(self.target_list)

            self._download_all()

        else:
            print("FAILED: Index file not found.")


    def _download_all(self):

        print("\n|----------------------Starting Download Attempts----------------------|\n")

        i = 1
        for target in self.target_list:

            CAD = ConnectAndDownload(target, self.thread_no)
            print(f"{i}. Attempting to download target {target}.")
            CAD._download()


            i += 1
            print()



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
