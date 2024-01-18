# Parsnip

## \*\*\* NOTICE \*\*\*
Parsnip is currently in an alpha release state. It is currently intended for those familiar with zeek packaging and parser testing.

## Overview
Parsnip is a program developed to assist the parsing of ICS protocols using the open source network security monitoring tool [Zeek](https://github.com/zeek/zeek.git).

The Parsnip ecosystem consists of three parts:
1. A GUI interface designed provide a visual representation of a protocol's packet structure
2. JSON files in an intermediate language "parsnil" that is fed into the backend
3. A backend that performs processing on the parsnil files and outputs the spicy, zeek and event files necessary for a parser

## Project Structure

* backend: folder containing the code for the backend; used for processing parsnil files to create zeek parsers
* docs: folder containing project documentation
* frontend: folder containing the code for the web frontend; used for creating parsnil files
* LICENSE.txt: code license file
* NOTICE.txt: code notice file
* README.md: this file

## Documentation

Please refer to [docs/parsnip.md](docs/parsnip.md) for more information on using Parsnip.

## Known Limitations
* Automatic packaging is a work in progress. However, using `zkg create` works.
* Choices actions can currently only point to objects, not other types such as integers.