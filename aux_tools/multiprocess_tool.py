import multiprocess as mp
import pandas as pd
import logging
import numpy as np
import math

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class MultiprocessTool(object):
    """MultiprocessTool run a function on multiple cores, by taking the number of cores (defaults to 2) when the class is instanciated.
    To run a passed in function you must run the run_multiprocess function passing in the function as the first argument, the a list of data
    to process separated in chunks (or batches) as the second argument. Finally as the third argument *args can be passed in, that will be
    read as a tuple of arguments, then available in the function that is to be run with multiple processes."""

    """
  USAGE: within function which creates the MultiprocessTool instance please declare the "self.lock" instance variable as global, so that it is accessible throughout the processes.
  The same thing goes with global_last_id.
  """

    # Initialization of MuliprocessTool class
    def __init__(self, num_of_processes=2):
        super(MultiprocessTool, self).__init__()
        global global_last_id
        global_last_id = mp.Value('i', 0)
        self.num_of_processes = num_of_processes

        lock = mp.Lock()
        self.lock = lock

    def get_lock(self):
        return lock

    # Splits inputted data into chunks
    def data_chunker(self, data, chunksize):
        try:
            chunked_data = np.array_split(data, math.ceil(len(data) / float(chunksize)))
        except Exception as error:
            logger.info('Could not split dataframe, as it is empty', error)
            chunked_data = [data]
        return chunked_data

    def update_num_of_processes(self, num_of_processes):
        self.num_of_processes = num_of_processes

    # Run passed in function by mapping it to multiple cores as frames of data
    # and reducing it to outputted result.

    #FUNCTION NOT WORKING!
    def run_multiprocess_dataless(self, func, *args):
        pool = mp.Pool(processes=self.num_of_processes)
        funclist = []
        if len(args) > 0:
            f = pool.apply_async(func, args)
            funclist.append(f)
        else:
            f = pool.apply_async(func)
            funclist.append(f)
        for idx, f in enumerate(funclist):
            print(f)
            print(f.get())
        pool.close()
        pool.join()

    #Takes data as a list of dataframes or values or dictionarys or tuple (run through data_chunker first)
    def run_multiprocess(self, func, data, *args):
        pool = mp.Pool(processes=self.num_of_processes)

        funclist = []
        if len(args) > 0:
            for intermediate_df in data:
                f = pool.apply_async(func, [intermediate_df, args])

                funclist.append(f)
        else:
            for intermediate_df in data:
                f = pool.apply_async(func, [intermediate_df])
                funclist.append(f)

        result = pd.DataFrame()

        for idx, f in enumerate(funclist):
            print(f)
            result = result.append(f.get())  # timeout in 10 seconds

        pool.close()
        pool.join()

        return result

