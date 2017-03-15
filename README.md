Remove unwanted span tags from epub files

# Usage

## cli

```bash
cleanepub.py --help
usage: cleanepub.py [-h] --source SOURCE --destination DESTINATION [--batch]
                    [--verbose]

cleanepub.py

optional arguments:
  -h, --help            show this help message and exit
  --source SOURCE, -s SOURCE
                        path to the input epub file which needs to be processed
  --destination DESTINATION, -d DESTINATION
                        path where to write the processed epub
  --batch, -b           batch mode. if specified, SOURCE & DESTINATION should be folder path
  --verbose, -v         Verbose mode
```