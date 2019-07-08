#!/usr/bin/env python3

import time
import logging
import argparse
import configparser
import os.path
import os

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer
from sypht.client import SyphtClient

from abr import ABRClient

LOG_FMT = '%(name)s [%(process)d]: %(asctime)s: %(levelname)s: %(message)s'

class SyphtFSEventHandler(FileSystemEventHandler):
    def __init__(self, sypht_client, abr_client, output_dir,
            extensions={".pdf"}, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.sypht_client = sypht_client
        self.abr_client = abr_client
        self.output_dir = output_dir
        self.extensions = extensions
        self.logger = logging.getLogger(type(self).__name__)
    def on_created(self, event):
        self.logger.info("Received create event for %s.", event.src_path)
        if event.is_directory or \
                os.path.splitext(event.src_path)[1] not in self.extensions:
            self.logger.info("Skipping %s.", event.src_path)
            return
        try:
            self.process(event.src_path)
        except Exception as e:
            self.logger.error("Could not process %s. Exception occurred: %s", 
                    event.src_path, e)
    def process(self, filename):
        with open(filename, "rb") as f:
            fid = self.sypht_client.upload(f, fieldsets=["document"])
            self.logger.info("Sent %s to Sypht.", os.path.basename(filename))
        results = self.sypht_client.fetch_results(fid)
        doc_date = results.get("document.date", None)
        doc_abn = results.get("document.supplierABN", None)
        if doc_date is None:
            self.logger.warning("Could not obtain date from document. Skipping")
            return
        if doc_abn is None:
            self.logger.warning("Could not obtain ABN from document. Skipping")
            return
        self.logger.info("Document date: %s, supplier ABN: %s.", 
                doc_date, doc_abn)
        supplier_name = self.abr_client.lookup_name(doc_abn)
        if supplier_name is None:
            self.logger.warning("Could not obtain supplier name. Skipping")
            return
        supplier_name = self.abr_client.remove_suffixes(supplier_name)
        self.logger.info("Supplier name: %s.", supplier_name)
        new_filename = self.get_name(doc_date, supplier_name,
                os.path.splitext(filename)[1])
        self.logger.info("Moving %s to %s.", filename, new_filename)
        os.rename(filename, new_filename)
    def get_name(self, doc_date, supplier_name, ext):
        i = 0
        while True:
            suffix = "" if i == 0 else " {}".format(i)
            filename = "{} {}{}{}".format(doc_date, supplier_name, suffix, ext)
            filename = os.path.join(self.output_dir, filename)
            if not os.path.exists(filename):
                return filename
            i += 1

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Automatically renames \
        documents in a watched directory according to the extracted date and \
        supplier name. The date and supplier ABN are extracted using the Sypht \
        API, and the supplier name is derrived from the ABN using the \
        Australian Business Register's web services.")
    parser.add_argument("config", help="the configuration file")
    args = parser.parse_args()

    config = configparser.ConfigParser()
    config.read(args.config)

    logging.basicConfig(filename=config.get("Logging", "Output"), filemode="a", 
            level=config.get("Logging", "Level"), format=LOG_FMT)

    sypht_client = SyphtClient(config.get("APIs", "Sypht_CID"), 
            config.get("APIs", "Sypht_Secret"))
    abr_client = ABRClient(config.get("APIs", "ABR_GUID"))

    event_handler = SyphtFSEventHandler(sypht_client, abr_client, 
            config.get("Directories", "Output"))
    observer = Observer()
    observer.schedule(event_handler, config.get("Directories", "Input"))
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
