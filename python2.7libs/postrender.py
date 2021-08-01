import pathlib

path = str(pathlib.Path(__file__).parent.absolute())

#script_path = os.path.dirname(os.path.realpath(__file__))
# Initialize
#path = "Test"
path = path[:-14] + "/lib/"
path = path.replace("\\", "/")

debug = open("G:\\output.txt", "w")
debug.write("Start Debug")

debug.write(path)
debug.write("End Debug")
debug.close()

f = open(path + "done.txt", "w")
f.close()
