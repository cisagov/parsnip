# Parsnip

## Background

[Zeek](https://github.com/zeek/zeek.git) is an open source network security monitoring tool. It is highly customizable and users can introduce custom scripts and protocol parsers to enhance the data they recieve from Zeek. CISA publishes several Zeek packages for ICS protocol parsing. These can be found [here](https://github.com/zeek/zeek.git).

These packages are written in one of two languages: BinPAC or Spicy. These languages are used only for Zeek parser development thus creating a steep learning curve for parser development. Parsnip seeks to lower the barrier of entry for parser creation by leveraging more familiar structures such as a Graphical User Interface(GUI) and JSON.

## Introduction
Parsnip is a program developed to assist the parsing of ICS protocols.

The Parsnip ecosystem consists of three parts:
1. A GUI interface designed provide a visual representation of a protocol's packet structure
2. JSON files in an intermediate language "parsnil" that is fed into the backend
3. A backend that performs processing on the parsnil files and outputs the spicy, zeek and event files necessary for a parser

## Setup
Parsnip has been tested with Ubuntu 22.04.

### GUI
Install Prerequisites:

```bash
sudo apt update
sudo apt install docker.io
```

Add the current user to the docker group:

```bash
sudo usermod -a -G docker $USER
```

**Restart your computer to activate docker and set up the user within the docker group.**

### Backend
Install Prerequisites:

```bash
sudo apt install python3 python3-pip graphviz-dev
```

```bash
pip3 install networkx matplotlib pygraphviz pydot
```

## Getting Started
### Running the GUI

From the icsnpp-parsnip folder:
```bash
./start_webServer.sh
```

This will drop you into a bash session running within the docker container.

From there run:
```bash
cd app
python3 app.py
```

You should now be able to access the frontend in a web browser at: http://127.0.0.1:5000.

Refer to the documentation in the icsnpp-parsnip folder and the next session for more information on the GUI.

### Basic Example
For this example, we are going to implement a relatively simple protocol using Parsnip.

#### Protocol Information
The MySimpleProtocol protocol runs over TCP port 8888.

A protocol message for our simple protocol consists of a two byte header and a variable length body.
The first byte of the header consists of two 4-bit bitfields. The first four bits represent the protocol version. The last four bits represent the message type. A message type of 0 represents a message for the server. A message type of 1 represents a message for the client. The second byte of the header consists of the length of the packet as an unsigned 8-bit integer. The body consists of a series a bytes where the length of the body is specified by the length field.

#### Constructing the Protocol in Parsnip
When you go to the Parsnip frontend using a browser, you will be greeted by the following page:

![Parsnip front page](./images/front.png)

##### Protocol Configuration

We begin by going to the Parser Configuration Page:

![Parser configuration page](./images/empty_config.png)

Press the "Edit Parser Configuration" button and enter the information shown:

![Parser configuration partial](./images/partial_config.png)

We will return to this screen later to specify the Entry Point Structure. After you press the "Save Configuration" button, navigate to the "Protocol Ports" tab as shown:

![Parser protocol ports page](./images/empty_ports.png)

Press the "Add Port" button and enter the information shown:

![Add TCP Port](./images/add_port.png)

After you press the "Add Port" the port should now be listed as a protocol port as shown:

![TCP Port added](./images/port_added.png)

##### Adding Structures
When working within the frontend, it is best to take a bottom-up approach to defining structures.

For our protocol, we will start by defining the message type enumeration.

First, navigate to the Enums page through the "View/Edit Components" menu as shown:

![Enums Navigation](./images/enums_navigation.png)

Next, press the "Add Enum" button and enter the information shown in the next two images:

![messageType information part 1](./images/messageType_info_1.png)

![messageType information part 2](./images/messageType_info_2.png)

Press the "Add Enum" button to save the enum. The updated information should appear as shown:

![Updated Enum information](./images/updated_enum_page.png)

Next, navigate to the Bitfields page through the "View/Edit Components" menu as shown:

![Enums Navigation](./images/bitfields_navigation.png)

Press the "Add Bitfield" button and enter the information shown in the next two image:

![messageType information part 1](./images/headerBits_info_1.png)

![messageType information part 2](./images/headerBits_info_2.png)

Press the "Add Bitfield Structure" to save the bitfield. The updated information should appear as shown:

![Updated Bitfield Information](./images/updated_bitfields_page.png)

Finally, we will build our "Object" structures. Navigate to the Objects page through the "View/Edit Components" menu as shown:

![Objects Navigation](./images/objects_navigation.png)

First, press the "Add Object" button and enter the information shown:

![Body Information](./images/body_info.png)

Press the "Add Object" button to save the object. Next, press the "View Fields" link for the Body object. Then press the "Add Field" button and enter the information shown:

![Body Field Information](./images/body_data_info.png)

Press the "Add Field" button to save the information. The updated information should appear as shown:

![Updated Body Information](./images/updated_body_fields.png)

Navigate back to the Objects page again. Press the "Add Object" button on the Object page again and enter the information shown:

![Header Information](./images/header_info.png)

Press the "Add Object" button to save the object. Next, press the "View Fields" link for the Header object. Then press the "Add Field" button and enter the information shown:

![Header Bits Information](./images/header_headerBits_info.png)

Press the "Add Field" button to save the information. Press the "Add Field" button again on the Header Fields page and enter the information shown:

![Header Length Information](./images/header_length_info.png)

Press the "Add Field" button to save the information. The updated information should appear as shown:

![Updated Body Information](./images/updated_header_fields.png)

Navigate back to the Objects page again. Press the "Add Object" button on the Object page again and enter the information shown:

![Message Information](./images/message_info.png)

Press the "Add Object" button to save the object. The updated information should appear as shown:

![Updated Objects](./images/updated_objects_page.png)

Next, press the "View Fields" link for the Message object. Then press the "Add Field" button and enter the information shown:

![Message Header Information](./images/message_header_info.png)

Press the "Add Field" button to save the information. Press the "Add Field" button again on the Message Fields page and enter the information shown:

![Message Body Information](./images/message_body_info.png)

Press the "Add Field" button to save the information. The updated information should appear as shown:

![Updated Message](./images/updated_message_fields.png)

That is the end of adding structures. Next we will update the configuration with the entry point.

##### Update Configuration

Now that we have our entry point object defined, we return to the Parser Configuration Page as shown:

![Configuration update](./images/config_before_update.png)

We again press the "Edit Parser Configuration" button and set the Parser Entry Point value to the "Message" object as shown:

![Updating Entry Point](./images/finalize_config.png)

Press the "Save Configuration" button to save the updated configuration.

##### Review
We will have the frontend review the parser and look for potential issues. Navigate to the Review page. The page automatically runs checks when loaded. The output should appear as shown:

![Review Results](./images/review_page.png)

We see that there are now Switch/Choice types in the parser, but no other errors or warnings are present.

##### Download the Parsnil files
Press the "Export Parsnip Files" link to download a zip file with the Parsnil files.

### Running the Backend
Once a "parsnil" file has been generated by the frontend, you should receive a zip file called "parsnip.zip" which contains a folder with a random string of characters for its name (e.g., 08f4789d-6915-4067-8939-4994c55acbae). Unzip the folder into its own folder. Once that zip file has been unzipped, copy the path to the random string folder as your "input_folder" for the following command.

To build the parser, run from the icsnpp-spicy-generator folder, replacing input_folder and output_folder as appropriate:
```bash
python3 main.py input_folder output_folder
```

For example,
```bash
python3 main.py ~/Downloads/parsnip/08f4789d-6915-4067-8939-4994c55acbae ~/MyParser
```

The parser code files should now be located in the output_folder directory.

## Syntax Information
Refer to [syntax.md](syntax.md) for more information about writing a parser using Parsnip.