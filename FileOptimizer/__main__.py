import argparse
from .main import optimiseDir

def main():
   parser = argparse.ArgumentParser();
   parser.add_argument('input', nargs='*', help='input file');
   parser.add_argument('-s', '--silent', action='store_true', help='run without output print');
   args = parser.parse_args();
   deduped_input = []
   for inputfile in args.input:
      if inputfile not in deduped_input:
         deduped_input.append(inputfile);
   for inputfile in deduped_input:
      optimiseDir(inputfile, silentMode=args.silent)

if __name__ == "__main__":
   main()
