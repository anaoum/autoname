# Autoname
Automatically renames PDF documents in a watched directory according to the extracted date and supplier name. The date and supplier ABN are extracted using the Sypht API, and the supplier name is derived from the ABN using the Australian Business Register's web services.

## Requirements
* Python 3
  * zeep
  * sypht
  * watchdog
* Sypht API access (client ID and client secret)
* Australian Business Register Web Services access (GUID)

The python dependencies can be easily installed with pip:
```bash
pip install zeep sypht watchdog
```

## Configuration
The script requires a configuration file to run. An example is included in the repo:
```ini
[Directories]
Input = /path/to/watched/folder
Output = /path/to/output/folder

[APIs]
Sypht_CID = FIXME
Sypht_Secret = FIXME
ABR_GUID = FIXME

[Logging]
Output = /dev/stderr
Level = INFO
```
Other than the logging settings, you will need to change all the values.

## Running
```bash
./autoname.py /path/to/config.ini
```
The script will watch all files in the configured Input directory and move them to the configured Output directory with the appropriate name. If the script cannot determine the date of the document or the supplier name, it will leave the document in the input directory.

## Motivation

I keep a paper-free home. When I receive paper documents (most commonly invoices), I scan them using my Fujitsu ScanSnap iX1500 and store the digitised documents in Dropbox. The scanner is great and can get through documents quite quickly. The most time consuming part is renaming all the files so that they have a somewhat meaningful name. I typically use the format of `DATE<space>SUPPLIER.pdf`. The goal of autoname.py is to save time whenever I scan documents by automatically naming files.

## Limitations

* Only processes PDFs
* Does not process files already existing in input folder.
