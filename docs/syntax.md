# Introduction

Parsnip is an intermediary language for the spicy framework that provides an easier approch to developing zeek protocol parsers.

Parsnip consists of a frontend graphical user interface (GUI) and a backend processor. The frontend GUI allows the user to enter the information needed to create the Parsnip files without working directly with the JSON files used by Parsnip. The frontend supports JSON snapshot files that maintain a record of the data entered. The backend takes the JSON Parsnip files and generates spicy and zeek script files that can be used to build a parser in Zeek.

# Parts of a Parser Definition
Notes:

* All file paths in Parsnip Syntax notes are relative to the Parsnip parser directory

## Parser Configuration
### General Parser Configuration
#### Parsnip Version
Used to indicate which version of parsnip is being used. Current version: 1.0.

* Frontend Information
    - Implied to be version 1.0
* Snapshot Syntax
    - Top Level Element: "ParsnipVersion"
* Parsnip Syntax
    - general/config.json: "ParsnipVersion"

Parsnip Example:
```JSON
"ParsnipVersion": "1.0"
```

#### Protocol Name
The name of the protocol. It should only consist of capital letters and underscores (e.g., HART_IP).

* Frontend Information
    - Parser Configuration -> General Parser Configuration -> Protocol Name
* Snapshot Syntax
    - Top Level Element: "Protocol"
* Parsnip Syntax
    - general/config.json: "Protocol"

Parsnip Example:
```JSON
"Protocol": "HART_IP"
```

#### Parser Entry Point
The [object](#structures_object) that serves as the initial entry point for parsing the protocol.

* Frontend Information
    - Parser Configuration -> General Parser Configuration -> Parser Entry Point
* Snapshot Syntax
    - Top Level Element: "EntryPoint"
    - Unscoped Object Name (e.g., Message)
* Parsnip Syntax
    - general/config.json: "EntryPoint"
    - Scoped Object Name (e.g., "general.Message")

Parsnip Example:
```JSON
"EntryPoint": "general.Message"
```

#### Uses Layer 2
Specifies if the protocol is built upon Ethernet (true) rather than TCP or UDP (false).

* Frontend Information
    - Currently not implemented
* Snapshot Syntax
    - Top Level Element: "usesLayer2"
* Parsnip Syntax
    - general/config.json: "usesLayer2"

Parsnip Example:
```JSON
"usesLayer2": false
```

#### Ethernet Protocol Number
If the protocol uses Ethernet instead of UDP or TCP, then this element specifies the Ethernet Protocol Number that specifies this protocol.

* Frontend Information
    - Currently not implemented
* Snapshot Syntax
    - Top Level Element: "ethernetProtocolNumber"
* Parsnip Syntax
    - general/config.json: "ethernetProtocolNumber"

Parsnip Example:
```JSON
"ethernetProtocolNumber": 34980
```

#### Uses TCP
Specifies if the protocol is built upon TCP.

* Frontend Information
    - Parser Configuration -> General Parser Configuration -> UsesTCP?
* Snapshot Syntax
    - Top Level Element: "usesTCP"
* Parsnip Syntax
    - general/config.json: "usesTCP"

Parsnip Example:
```JSON
"usesTCP": true
```

#### Uses UDP
Specifies if the protocol is built upon UDP.

* Frontend Information
    - Parser Configuration -> General Parser Configuration -> UsesUDP?
* Snapshot Syntax
    - Top Level Element: "usesUDP"
* Parsnip Syntax
    - general/config.json: "usesUDP"

Parsnip Example:
```JSON
"usesUDP": true
```

Note: Either usesTCP and usesUDP for non layer 2 protocols must be true. Both may also be true.

#### Copyright Holder
The copyright holder name (e.g., Battelle Energy Alliance).

* Frontend Information
    - Currently not implemented
* Snapshot Syntax
    - Top Level Element: "copyrightHolder"
* Parsnip Syntax
    - Currently not implemented

#### Copyright Contact Email
The copyright holder email.

* Frontend Information
    - Currently not implemented
* Snapshot Syntax
    - Top Level Element: "copyrightContactEmail"
* Parsnip Syntax
    - Currently not implemented

#### License
The license that the parser is being released under.

* Frontend Information
    - Currently not implemented
* Snapshot Syntax
    - Top Level Element: "license"
* Parsnip Syntax
    - Currently not implemented

#### <a name="conversionFile"></a>Conversion File
Base64 encoded file contents that will be used to generate a C++ file used to do custom type conversions within the parser. If no conversionFile variable is set, a skeleton version of the file will be generated based on the defined [User Types](#userTypes). This file can be found at analyzer/&lt;lower_case_parser_name&gt;_conversion.cc in the generated output directory.

* Frontend Information
    - Currently not implemented
* Snapshot Syntax
    - Top Level Element: "conversionFile"
* Parsnip Syntax
    - general/config.json: "conversionFile"

Parsnip Example:
```JSON
"conversionFile": "Ly8gUHV0IHNvbWV0aGluZyBwcm9mb3VuZCBoZXJlLi4uCi8vIFB1dCBzb21ldGhpbmcgdXNlZnVsIGhlcmUuLi4="
```

File Contents Example:
```cpp
#include <string>
#include <iostream>
#include <algorithm>
#include <random>
#include <hilti/rt/libhilti.h>
#include <spicy/rt/libspicy.h>

namespace ETHERCAT_CONVERSION
{
#define ID_LEN 9

    std::string generateId() {
        std::stringstream ss;
        for (auto i = 0; i < ID_LEN; i++) {
            // Generate a random char
            std::random_device rd;
            std::mt19937 gen(rd());
            std::uniform_int_distribution<> dis(0, 255);
            const auto rc = dis(gen);

            // Hex representaton of random char
            std::stringstream hexstream;
            hexstream << std::hex << rc;
            auto hex = hexstream.str();
            ss << (hex.length() < 2 ? '0' + hex : hex);
        }
        return ss.str();
    }

    std::string packedBytesConversion(const hilti::rt::Bytes &data)    {
        std::string returnValue;
        // TODO: Useful stuff
        return returnValue;
    }
}
```

#### Signature File
Base64 encoded file contents that will be used to generate the dpd.sig Zeek file.

* Frontend Information
    - Currently not implemented
* Snapshot Syntax
    - Top Level Element: "signatureFile"
* Parsnip Syntax
    - general/config.json: "signatureFile"

Parsnip Example:
```JSON
"signatureFile": "IyBGaXggTWUhCnNpZ25hdHVyZSBkcGRfcGFyc2VyX3RjcCB7CiAgaXAtcHJvdG8gPT0gdGNwCiAgcGF5bG9hZCAvXltceDAwLVx4ZmZdezJ9LwogIGVuYWJsZSAiUEFSU0VSX1RDUCIKfQ=="
```

### Protocol Ports
A list of TCP/UDP ports used by the protocol.

* Frontend Information
    - Parser Configuration -> Protocol Ports
* Snapshot Syntax
    - Top Level Element: "Ports"
    - Array of objects which include:
        * "protocol": "tcp" or "udp"
        * "port": Port number
* Parsnip Syntax
    - general/config.json: "Ports"
    - Array of objects which include:
        * "protocol": "tcp" or "udp"
        * "port": Port number

Parsnip Example:
```JSON
"Ports": [
    {
        "protocol": "tcp",
        "port": 8080
    },
    {
        "protocol": "tcp",
        "port": 8880
    }
]
```

### <a name="userTypes"></a>User Types
User types are used to define data types that are not natively supported by Parsnip but are used in the protocol being parsed. Each user type is accompanied by a conversion function written in C++ which processes bytes and returns a native type based on their values.

* Frontend Information
    - Parser Configuration -> User Types
* Snapshot Syntax
    - Top Level Element: "CustomFieldTypes"
    - Array of objects which include:
        * "name": typename to use as field types
        * "interpretingFunction": name of the C++ function used to convert from bytes to a known type
        * "returnType": a known c++ type (e.g., string")
* Parsnip Syntax
    - general/config.json: "CustomFieldTypes"
    - Array of objects which include:
        * "name": typename to use as field types
        * "interpretingFunction": name of the C++ function used to convert from bytes to a known type
        * "returnType": a known c++ type (e.g., string")

The interpreting functions will need to be defined in the [Conversion File](#conversionFile) value eventually.

Parsnip Example:
```JSON
"CustomFieldTypes": [
    {
        "name": "PackedBytes",
        "interpretingFunction": "packedBytesConversion",
        "returnType": "string"
    }
]
```

## Scopes
Structures can be grouped into one or more scopes. The default scope is the "general" scope.

A list of scopes are provided in the general/config.json file in the Parsnip file structure. The scope of a structure can be specified using the "scope" keyword in the entry.

## Structures
Structures contain all the objects necessary to fully construct and parse a protocol. Supported structures are `Bitfields`, `Switches`, `Enums`, and `Objects`.

* Snapshot Syntax
    - Top Level Element: "Structures"
    - Object which includes the following optional values:
        * "Bitfields": an array of [Bitfields](#structures_bitfields)
        * "Enums": an array of [Enums](#structures_enums)
        * "Objects" an array of [Objects](#structures_objects)
        * "Switches" an array of [Choices](#structures_choices)
* Parsnip Syntax
    - Spread across the following files:
        * &lt;scope&gt;/bitfields.json
        * &lt;scope&gt;/enums.json
        * &lt;scope&gt;/objects.json
        * &lt;scope&gt;/switches.json
    - Each file contains an array of objects representing the associated structures.

### <a name="dependency_info"></a>Dependency Information
Dependencies are applicable to objects and switches. ## TODO: DEFINE DEPENDENCIES ## The variables in each dependency are:

* "name": The name of dependency that allows it to be referenced within the structure
    - Must only contain upper and lower case letters, underscores, and numbers
    - May not begin with a number
    - Convention is camel case (i.e., thisIsMyValue)
* "type": The data type of the field (primitive or structure type)
* One of:
#TODO: Link primative types to list of possisble types. Fix throughout
    - "size": If the type is primitive (i.e. it doesn't require a referenceType to a structure), then this is the size of the item in bits.
    - Combination:
        * "refernceType": If the type requires a reference to a structure, then this is used instead of size.
        * "scope": The scope of the structure
* "description" (optional): Description of the field
* "notes" (optional): Additional notes about the field
* "endianness" (optional): Byte order of the structure
    - options are "big" or "little"
    - defaults to "big"

Parsnip Examples:
```JSON
{
    "name": "command",
    "type": "enum",
    "referenceType": "FunctionTypes",
    "scope": "general"
},
{
    "name": "dataLength",
    "description": "Length of the data",
    "notes": "Protocol limits this to 12 bits overall",
    "type": "uint",
    "size": 16
}
```

### <a name="field_info"></a>Field/Action Information
Fields are used to define what each portion of an object or action contains. There can be any number of fields defined within an object and one action for every option in a switch. The order they are listed in the array will determine the order they are expected in the packet when parsing.

The variables in a field are:

* "name": The name used to define the field.
    - Must only contain upper and lower case letters, underscores, and numbers
    - May not begin with a number
    - Convention is camel case (i.e., thisIsMyValue)
* "description": Used to describe what the field is used for in the context of the command.
* "type": Defines the type of data carried in the field that is expected to be parsed. More details in [Data Types](#dataTypes).
* One of:
    - "size": If the type is primative (i.e. it doesn't require a referenceType to a structure) then this is the size of the field in bits. It is best practice to the field size a multiple of 8. If two fields meet outside of a multiple of 8 then try using a bitfield described below.
    - Combination:
        * "referenceType": If the type requires a reference to a structure then this is used instead of size.
        * "elementType": Required if the type is "list". Defines the data type of the list elements.
        * "scope": The scope of the structure
* "notes": The notes field is used to provide any additional context. It is good practice to provide documentation on where the field is defined. This field is ignored by the backend.

Parsnip Examples:
```JSON
{
    "name": "pollingAddressDevice",
    "description": "Polling Address of Device",
    "type": "uint",
    "size": 8,
    "notes": "refer to the Data Link Layer Specification"
},
{
    "name": "loopCurrentMode",
    "description": "Loop Current Mode",
    "type": "enum",
    "referenceType": "LoopCurrentModeCodes",
    "scope": "general",
    "notes": "refer to Common Table 16, Loop Current Modes"
}
```

#### Extended Field Options
##### <a name="providing_input"></a>Providing Input
Sometimes referenced types require input. If the reference type is an "object", inputs are passed using the "inputs" value. If the reference type is a "switch", the main input is passed using the "input" value and additional values are passed in using the "additionalInputs" array value. The order of the inputs must match the order of the dependencies. Values referring to previously defined fields are preceded by "self."

Parsnip Examples:
```JSON
{
    "name": "command",
    "description": "Command Data",
    "type": "switch",
    "referenceType": "Command16Switch",
    "input": {
        "source": "self.commandNumber"
    },
    "additionalInputs": [
        {
            "source": "self.byteCount"
        },
        {
            "source": "messageType"
        }
    ]
},
{
    "name": "packetContents",
    "description": "Device-Specific Status",
    "notes": "refer to appropriate device-specific document for detailed information",
    "type": "object",
    "referenceType": "ReadAdditionalDeviceStatusContents",
    "inputs": [
        {
            "source": "byteCount"
        },
        {
            "source": "messageType"
        }
    ]
}
```

##### Conditional Field
Sometimes a field might exist conditionally based on if a flag is set or if a value exists. In the event where this conditional statement can be represented by a single if statement, we've added an optional "conditional" variable that can be placed in any command field.

The "conditional" variable is set to one of the following:

* An object containing three values "indicator", "operator", and "value".
    - The "indicator" value refers to the field which contains the value to check against.
    - The "operator" value refers to one of the options provided in the table below.
    - The "value" value stores the value to compare against the indicator. It must match the type of the indicator value.
* An "and" array of objects. Note, not currently implemented in the frontend.
* An "or" array of objects. Note, not currently implemented in the frontend.

    | Operator | Name                  |
    |----------|-----------------------|
    | =        | Equal                 |
    | !=       | Not Equal             |
    | >        | Greater Than          |
    | <        | Less Than             |
    | >=       | Greater Than or Equal |
    | <=       | Less Than or Equal    |


Parsnip Examples:
```JSON
{
    "name": "slot0DeviceVariableCode",
    "description": "Slot 0: Device Variable Code",
    "conditional":
    {
        "indicator": "byteCount",
        "operator": ">=",
        "value": 1
    },
    "type": "uint",
    "size": 8
},
{
    "name": "filenameData",
    "description": "",
    "notes": "",
    "type": "object",
    "referenceType": "FilenameValue",
    "scope": "general",
    "conditional":
    {
        "and": [
            {
                "indicator": "dataLength",
                "operator": ">",
                "value": 14
            },
            {
                "indicator": "dataLength",
                "operator": "<",
                "value": 526
            }
        ]
    }
}
```

##### Until Fields
The "until" variable is a field variable for list types that contains

* "conditionType": The type of condition (dictates which other values exist)
    - Options:
        * "ENDOFDATA": Continue until no more data is present
        * "COUNT": A specific number of values will be read
* "indicator" (required if using "COUNT"): location that holds the number of elements to read
* "minus" (optional if using "COUNT"): Subtract a constant number of entries from the indicator

Parsnip Examples:
```JSON
{
    "name": "data",
    "type": "list",
    "elementType": "uint",
    "size": 8,
    "until": {
        "conditionType": "COUNT",
        "indicator": "dataLength",
        "minus": 2
    }
},
{
    "name": "commands",
    "type": "list",
    "elementType": "object",
    "referenceType": "CommandPDU",
    "scope": "general",
    "until": {
        "conditionType": "ENDOFDATA"
    }
}

```

### <a name="structures_enums"></a>Enumerations
Enumerations are used to represent a range of named values with a constant integer.

Mandatory Values:

* "name": The name of the enum, used to reference the enum
    - Must only contain upper and lower case letters, underscores, and numbers
    - May not begin with a number
    - Convention is Pascal Case (i.e., ThisIsMyName)
* "size": The number of bits used to represent the values
* "fields": An array of field (value) structures. See below for more information.

Optional Values:

* "reference": Specification reference information
* "notes": Other notes that might assist anyone working on the protocol

Enumeration Fields:
An array of key value pairs used in the enumeration as well as some extra details to assist in parsing. The variables in each enumeration field are:

* "name": The key used in the enumeration
    - Convention is all caps with underscores between words (i.e., ENUM_VALUE)
* "loggingValue": The information that will appear for logging as the protocol gets parsed
* "value": The integer value that the name is paired with
* "notes" (optional): Notes that might assist anyone working on the protocol

Additional Information:

* Frontend Information
    - View/Edit Components -> Enums
* Snapshot Syntax
    - Sub Element of "Structures": "Enums"
* Parsnip Syntax
    - &lt;scope&gt;/enums.json:

Parsnip Example:
```JSON
"Structures": {
    "Enums": [
        {
            "name": "WriteProtectCodes",
            "reference": "Common Table Specification TS20183 version 26.0 Table 7",
            "notes": "",
            "size": 8,
            "fields": [
                {
                    "name": "NO",
                    "loggingValue": "No",
                    "value": 0,
                    "notes": ""
                },
                {
                    "name": "YES",
                    "loggingValue": "Yes",
                    "value": 1,
                    "notes": ""
                },
                {
                    "name": "NOTUSED",
                    "loggingValue": "Not Used",
                    "value": 250,
                    "notes": ""
                },
                {
                    "name": "NONE",
                    "loggingValue": "None",
                    "value": 251,
                    "notes": ""
                },
                {
                    "name": "UNKNOWN",
                    "loggingValue": "Unknown",
                    "value": 252,
                    "notes": ""
                },
                {
                    "name": "SPECIAL",
                    "loggingValue": "Special",
                    "value": 253,
                    "notes": ""
                }
            ]
        }
    ]
}
```

### <a name="structures_bitfields"></a>Bitfields
A bitfield is a type where the values are dependent on a range of bits or individual bits rather than a number of bytes.

Mandatory Values:

* "name": The name of the bitfield, used to reference the bitfield
    - Must only contain upper and lower case letters, underscores, and numbers
    - May not begin with a number
    - Convention is Pascal Case (i.e., ThisIsMyName)
* "size": The number of bits used to represent the values
* "fields": An array of field (value) structures. See below for more information.

Optional Values:

* "reference": Specification reference information
* "notes": Other notes that might assist anyone working on the protocol
* "endianness": Byte order of the structure
    - options are "big" or "little"
    - defaults to "big"

Bitfield Fields:
An array of key value pairs used to define what each bit in the bitfield represents. The variables in each bitfield field are:

* "name": The key used in the enumeration
    - Convention is camel case (i.e., thisIsMyValue)
* "type": Type the bits should be interpreted as
    - Options:
        * "uint": unsigned integer
        * "bool": boolean value (i.e, true or false)
        * "void": ignore this part of the bitfield (useful for documenting unused/reserved bits)
* "bits": One or more bits of the bitfield (after converted to big endian order) used for the field
    - Single bit: "&lt;bit&gt;" (i.e., 11)
    - Bit range: "&lt;lowerBit&gt;..&lt;lowerBit&gt;" (i.e., 0..3)
    - Unused bits may be ignored
* "description" (optional): Description of the field
* "notes" (optional): Notes that might assist anyone working on the protocol

Additional Information:

* Frontend Information
    - View/Edit Components -> Bitfields
* Snapshot Syntax
    - Sub Element of "Structures": "Bitfields"
* Parsnip Syntax
    - &lt;scope&gt;/bitfields.json:

Parsnip Example:
```JSON
"Structures": {
    "Bitfields": [
        {
            "name": "Delimiter",
            "reference": "",
            "notes": "",
            "size": 8,
            "endianness": "big",
            "fields": [
                {
                    "name": "addressType",
                    "description": "Address Type",
                    "notes": "",
                    "type": "enum",
                    "referenceType": "AddressType",
                    "scope": "general",
                    "bits": "7"
                },
                {
                    "name": "expansionBytes",
                    "description": "",
                    "notes": "",
                    "type": "uint",
                    "bits": "5..6"
                },
                {
                    "name": "physicalLayerType",
                    "description": "",
                    "notes": "",
                    "type": "enum",
                    "referenceType": "PhysicalLayerType",
                    "scope": "general",
                    "bits": "3..4"
                },
                {
                    "name": "frameType",
                    "description": "",
                    "notes": "",
                    "type": "enum",
                    "referenceType": "FrameType",
                    "scope": "general",
                    "bits": "0..2"
                }
            ]
        }
    ]
}
```

### <a name="structures_objects"></a>Objects
Parsnip at its core is object oriented. An object is a basic unit in the language that contains a mix of fields and other objects.

Mandatory Values:

* "name": The name of the object, used to reference the object
    - Must only contain upper and lower case letters, underscores, and numbers
    - May not begin with a number
    - Convention is Pascal Case (i.e., ThisIsMyName)
* "size": The number of bits used to represent the values
* "fields": An array of field (value) structures. See [Field Information](#field_info) for more information on the format of each field.

Optional Values:

* "reference": Specification reference information
* "notes": Other notes that might assist anyone working on the protocol
* "endianness": Byte order of the structure
    - options are "big" or "little"
    - defaults to "big"
* "logIndependently": Boolean value that indicates whether or not the object should be logged in a seperate log file (defaults to false)
* "logWithParent": Boolean value that indicates whether or not the object should be logged as part of the parent object
    - Not implemented in the front end, implied true
* "scope": Specifies the scope the object should be associated with
* "dependsOn": Array of input that the object depends on. See [Dependency Information](#dependency_info) for more information on dependency information.

Additional Information:

* Frontend Information
    - View/Edit Components -> Bitfields
* Snapshot Syntax
    - Sub Element of "Structures": "Bitfields"
* Parsnip Syntax
    - &lt;scope&gt;/bitfields.json:

Parsnip Example:
```JSON
"Structures": {
    "Objects": [
        {
            "name": "Message",
            "reference": "",
            "notes": "",
            "logIndependently": false,
            "fields": [
                {
                    "name": "header",
                    "description": "Protocol Header",
                    "notes": "",
                    "type": "object",
                    "referenceType": "Header"
                },
                {
                    "name": "body",
                    "description": "Protocol Body",
                    "notes": "",
                    "type": "object",
                    "referenceType": "Body",
                    "inputs": [
                        {
                            "source": "self.header.messageID"
                        },
                        {
                            "source": "self.header.messageType.messageType"
                        }
                    ]
                }
            ]
        }
    ]
}
```

```JSON
"Structures": {
    "Objects": [
        {
            "name": "ReadPrimaryVariable",
            "reference": "Universal Command specification TS20127 version 7.2 Section 6.2",
            "notes": "",
            "logIndependently": false,
            "scope":"universal_commands",
            "dependsOn": [
                {
                    "name": "byteCount",
                    "type": "uint",
                    "size": 8
                },
                {
                    "name": "messageType",
                    "type": "enum",
                    "referenceType": "MessageType"
                }
            ],
            "fields": [
                {
                    "name": "primaryVariableUnits",
                    "description": "Primary Variable Units",
                    "type": "enum",
                    "size": 8,
                    "referenceType": "EngineeringUnitCodes"
                },
                {
                    "name": "primaryVariable",
                    "description": "Primary Variable",
                    "type": "float",
                    "size": 32
                }
            ]
        }
    ]
}
```

### <a name="structures_choices"></a>Choices

Choices (switches) are a structure used when an object field could contain many different possibilities based on a value elsewhere in the packet. A common example is when the body of a packet could contain different fields based on the command number listed in the header.

Mandatory Values:

* "name": The name of the choice structure, used to reference the choice
    - Must only contain upper and lower case letters, underscores, and numbers
    - May not begin with a number
    - Convention is Pascal Case (i.e., ThisIsMyName)
* "dependsOn": The dependency that the switch will depend on when picking from the associated options. See [Dependency Information](#dependency_info) for more information on dependency information.
* "options": An array of option structures. See below for more information.

Optional Values:

* "additionalDependsOn": An array of additional dependencies. See [Dependency Information](#dependency_info) for more information on dependency information.
* "default": The default action to take if an option is not triggered. This defaults to a "void" action of do nothing. The contents are the same as the contents of an action in an object as outlined below. Note: this is not currently implemented in the front end.

Options:

An array of key value pairs used to take a course of action based on the input. The variables in each option are:

* "value": A valid value, based on the type specified in the "dependsOn" variable to compare against
* "action": The action to take if the value passed in matches the value specified. See [Field Information](#field_info) for more information on the format of the action.
    - Best practice is to only place objects under the action object to maintain readability unless there is only one field that needs to be parsed in the case

Additional Information:

* Frontend Information
    - View/Edit Components -> Choices
    - Currently limited to enum types for the "dependsOn" variable
* Snapshot Syntax
    - Sub Element of "Structures": "Switches"
* Parsnip Syntax
    - &lt;scope&gt;/switches.json:

Parsnip Example:
```JSON
"Structures": {
    "Switches": [
        {
            "name": "Command8Switch",
            "dependsOn": {
                "name": "commandNumber",
                "type": "uint",
                "size": 8
            },
            "additionalDependsOn": [
                {
                    "name": "byteCount",
                    "type": "uint",
                    "size": 8
                },
                {
                    "name": "messageType",
                    "type": "enum",
                    "referenceType": "MessageType",
                    "scope": "general"
                }
            ],
            "options": [
                {
                    "value": 0,
                    "action": {
                        "name": "readUniqueIdentifier",
                        "type": "object",
                        "referenceType": "ReadUniqueIdentifier",
                        "inputs": [
                            {
                                "source": "byteCount"
                            },
                            {
                                "source": "messageType"
                            }
                        ]
                    }
                },
                {
                    "value": 1,
                    "action": {
                        "name": "readPrimaryVariable",
                        "type": "object",
                        "referenceType": "ReadPrimaryVariable",
                        "inputs": [
                            {
                                "source": "byteCount"
                            },
                            {
                                "source": "messageType"
                            }
                        ]
                    }
                }
            ]
        }
    ]
}

```

# <a name="dataTypes"></a>Data Types
## Basic Types TODO: Primative or Basic Type? Fix throughout. Pick one & stick to it

Parsnip supports:

* unsigned integers (uint)
* integers (int)
* boolean values (bool)
    - only in bitfields
* bytes
* float values (float)
* void

<!--
### Boolean Values

Boolean Values take the first bit of any sized field to determine whether the value is true or false. To setup a boolean field set the `type` as `bool`.

Parsnip Example:
```JSON
# bool Field

{
    "name": "Name",
    "description": "Description",
    "type": "bool",
    "size": 8
}
```
-->

### Bytes

Bytes are used to store raw, opaque data. To use them in a parsnip field, set the "type" variable to "byte" and specify the "size" to the number of expected bits (Number of bytes * 8).

Parsnip Example:
```JSON
{
    "name": "variableName",
    "description": "",
    "type": "byte",
    "size": 64
}
```

The above field represents a field that contains 8 bytes of data.

### Float Values

Real numbers are used to store floating point numbers with double precision. To use them in a parsnip field, set the "type" variable to "float" and specify the "size" to the number of expected bits (32 or 64).

Parsnip Example:
```JSON
# Float Field

{
    "type": "float",
    "description": "Description",
    "name": "Name",
    "size": 32
}
```

### Unsigned and Signed Integers

Parsnip supports unsigned integers and signed integers of various sizes.
To define an unsinged integer field set the "type" variable as "uint" and define the number of bits that the uint field contains in the "size" variable.

```JSON
{
    "name": "Name",
    "description": "Description",
    "type": "uint",
    "size": 16
}
```

The above field contains a two byte unsigned integer value ranging from 0-65536.

Likewise for an integer, you set the "type" variable to "int" and then define the "size" variable.

```JSON
{
    "name": "Name",
    "description": "Description",
    "type": "int",
    "size": 16
}
```

### Void
The void type is used to demonstrate a lack of fields. The best use of void is often in the options of a switch statement where a case has meaning but does not generate any extra fields.

```JSON
"options":[
    {
        "value": "SESSION_CLOSE",
        "action": {
            "name": "sessionClose",
            "type": "void"
        }
    }
]
```

## Addresses

Address fields can handle either IPv4 or IPv6 addresses and will determine which type of address is being used based off of the fieldSize defined in the field. For an IPv4 address, set "type" as "addr" and "size" as "32".

```JSON
{
    "name": "Name",
    "description": "Description",
    "type": "addr",
    "size": 32
}
```

Likewise, for a IPv6 field, set "type" as "addr" and "size" as "64" or "128".

```JSON
{
    "name": "Name",
    "description": "Description",
    "type": "addr",
    "size": 64
}
```
## Parsnip Types - TODO:Clarify that these are reference to other pre-defined parsing types

* enumerations (enum)
* bitfield (bits)
* switches (switch)
* objects (object)

### Bitfields   

A bitfield is a type where the values are dependent on a range of bits or individual bits rather than a number of bytes.

Parsnip Example:
```JSON
{
    "name": "delimiter",
    "description": "",
    "notes": "",
    "type": "bits",
    "referenceType": "Delimiter",
    "scope": "general"
}
```

While defining fields in an object, you can set a field to be a bitfield by setting the "type" to "bits" and adding the variables "referenceType" and "scope" which will be set to the same name and scope as the bitfield structure.

### Enumerations

Enumerations are used to represent a range of named values with a constant integer.

Parsnip Example:
```JSON
{
    "name": "writeProtectCode",
    "description": "Write Protect Code. The Write Protect Code must return 251, None, when write protect is not implemented by a device.",
    "type": "enum",
    "referenceType": "WriteProtectCodes",
    "scope": "general",
    "notes": "see Common Table 7, Write Protect Codes"
}

```

While defining fields in an object, you can set a field to be an enumeration by setting the "type" to "enum" and adding the variables "referenceType" and "scope" which will be set to the same name and scope as the enum structure.

### List
Lists are arrays of items and are used to store a set of items. Lists require "until" information to be provided to specify when to stop processing items.

Parsnip Example:
```JSON
{
    "name": "data",
    "description": "",
    "notes": "",
    "type": "list",
    "elementType": "uint",
    "size": 8,
    "until": {
        "conditionType": "COUNT",
        "indicator": "mailboxSize",
        "minus": 10
    }
}
```

### Objects

Objects are used to enable the reuse of fields and set a hierarchy in the command structure.

Parsnip Examples:
```JSON
{
    "name": "header",
    "description": "Protocol Header",
    "notes": "",
    "type": "object",
    "referenceType": "Header"
},
{
    "name": "body",
    "description": "Protocol Body",
    "notes": "",
    "type": "object",
    "referenceType": "Body",
    "inputs": [
        {
            "source": "self.header.messageID"
        },
        {
            "source": "self.header.messageType.messageType"
        }
    ]
}
```

While defining fields in an object, you can set a field to be an object by setting the "type" to "object" and adding the variables "referenceType" and "scope" which will be set to the same name and scope as the object structure.

### Switches

Sometimes a field can have many different possibilities based on a value in an earlier field. To handle this use switches.

Parsnip Example:
```JSON
{
    "name": "command",
    "description": "Command Data",
    "type": "switch",
    "referenceType": "Command8Switch",
    "input": {
        "source": "self.commandNumber"
    },
    "additionalInputs": [
        {
            "source": "self.byteCount"
        },
        {
            "source": "messageType"
        }
    ]
}
```

While defining the field, you can set a field to be a switch by setting the "type" to "switch" and adding the variable "referenceType" which will be set to the same name as the switch structure. The "input" field will contain a "source" variable that is set to the field that switch cases are based on. If any other variables are needed for the individual cases to function you can pass those into the switch using the "additionalInputs" array with each member containing a similar source variable. For more on passing/referencing values look [here](#providing_input).

Copyright 2024, Battelle Energy Alliance, LLC All Rights Reserved