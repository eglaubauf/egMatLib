import sys
import os

script_path = os.path.dirname(os.path.realpath(__file__))
#Initialize
path = script_path[:-14] + "/lib/"
path = path.replace("\\", "/")

f = open(path + "done.txt", "w+")
f.close()
