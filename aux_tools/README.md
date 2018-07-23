To use the MultiprocessTool, please complete the following steps:
1) instanciate an a multiprocess tool:
			mpt = MultiprocessTool()

2) Chunk inputed data into a list of chunks of data for the MultiprocessTool to run (the data inputed should be a list of rows or a pandas dataframe) :
			
			chunked_data = mpt.data_chunker( inputted_data, #chunksize)

3) Run the multiple processes on the data:

			result = mpt.run_multiprocess(function_name, chunked_data, *args)