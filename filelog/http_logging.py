import os

def generate_filestructure():
    if(not os.path.exists(os.getcwd()+"/http_logging")):
        os.makedirs(os.getcwd()+"/http_logging/")
        

    
