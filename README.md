# Parsnip

## \*\*\* NOTICE \*\*\*
Parsnip is currently in a beta release state and is intended for early adopters. Users may experience issues, bugs and missing features. Those experiencing difficulties with Parsnip should create a GitHub issue.

## Overview
Parsnip is a program developed to assist in the parsing of protocols using the open source network security monitoring tool [Zeek](https://github.com/zeek/zeek.git). Parsnip is specifically designed to be applied towards developing Industrial Control Systems (ICS) protocol parsers but can be applied to any protocol.

The Parsnip ecosystem consists of three parts:
1. A GUI interface designed provide a visual representation of a protocol's packet structure
2. JSON files in an intermediate language (IL) that is fed into the backend. This intermediate language is made up of a set of JSON structures using keywords for each key-value pair to indicate it's type. 
3. A backend that performs processing on the parsnip IL files and outputs the spicy, zeek and event files necessary for a parser

## Project Structure

* backend: folder containing the code for the backend; used for processing parsnip IL files to create zeek parsers
* docs: folder containing project documentation
* frontend: folder containing the code for the web frontend; used for creating parsnip IL files
* LICENSE.txt: code license file
* NOTICE.txt: code notice file
* README.md: this file

## Documentation

Please refer to [docs/parsnip.md](docs/parsnip.md) for more information on using Parsnip.

## Known Limitations
* Package creation may have some file permission issues. If a package does not install, check that the files in the testing/scripts directory are executable.
* Choices actions can currently only point to objects, not other types such as integers.
* Frontend functionality is limited. Specifically AND and OR conditionals, layer 2 parsing and the minus keyword need to be implemented in the intermediate language.
* Self-recursive types with multiple switches are not properly handled. This will be fixed in a later release.
* Zeek btest in the created package is limited to a basic availability test. Functionality for expanding btests has not been added.

# Why is this repository private? #

|                                       |                                        |
| ------------------------------------- | -------------------------------------- |
| **Repository made private on:**       | Jan 3, 2024                           |
| **Private status approved by:**       | [@h-m-f-t](https://github.com/h-m-f-t)     |
| **Private exception reason:**         | Pending approval to open source from INL |
| **Repository contents:**              | ADD ME |
| **Planned repository deletion date:** | N/A                                    |
| **Responsible contacts:**             | [@rare-candies](https://github.com/rare-candies) |

See our [development guide](https://github.com/cisagov/development-guide#readme)
for more information about our [private repository
policy](https://github.com/cisagov/development-guide/blob/develop/open-source-policy/practice.md#private-repositories).
