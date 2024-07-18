# Parsnip

## Background

[Zeek](https://github.com/zeek/zeek.git) is an open source network security monitoring tool. It is highly customizable and users can introduce custom scripts and protocol parsers to enhance the data they receive from Zeek. CISA publishes several Zeek packages for ICS protocol parsing. These can be found [here](https://github.com/zeek/zeek.git).

These packages are written in one of two languages: BinPAC or Spicy. These languages are used only for Zeek parser development thus creating a steep learning curve for anyone interested in developing a parser. Parsnip seeks to lower the barrier of entry for parser creation by leveraging more familiar structures such as a Graphical User Interface(GUI) and JSON.

## Introduction
Parsnip is specifically designed to be applied towards developing Industrial Control Systems (ICS) protocol parsers but can be applied to any protocol.

The Parsnip ecosystem consists of three parts:
1. A GUI interface designed provide a visual representation of a protocol's packet structure
2. JSON files in an intermediate language (IL) that is fed into the backend. This intermediate language is made up of a set of JSON structures using keywords for each key-value pair to indicate it's type.
3. A backend that performs processing on the parsnip IL files and outputs the spicy, zeek and event files necessary for a parser

## Setup
Parsnip has been tested with Ubuntu 22.04 and 24.04.

### GUI
Install Prerequisites:

**Method 1**

```bash
sudo apt update
sudo apt install docker.io
```

Add the current user to the docker group:

```bash
sudo usermod -a -G docker $USER
```

**Restart your computer to activate docker and set up the user within the docker group.**

**Method 2**

```bash
#!/bin/bash

# Install Docker Key
sudo apt update
sudo apt install ca-certificates curl
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc

# Add the repository to sources
# Note: need to change VERSION_CODENAME to UBUNTU_CODENAME if running an Ubuntu derivative
echo \
    "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \
    $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
    sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

sudo apt update
sudo apt install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
```

Allow a non-root user to use Docker

```bash
sudo apt install uidmap
dockerd-rootless-setuptool.sh install
```

### Backend
Install Prerequisites:

#### Ubuntu 22.04

```bash
sudo apt install python3 python3-pip graphviz-dev
```

```bash
pip3 install rustworkx matplotlib pygraphviz pydot
```

#### Ubuntu 24.04

```bash
sudo apt install python3 python3-pip graphviz-dev python3-matplotlib python3-pygraphviz python3-pydot
```

Install Rustworkx as system package:

```bash
sudo pip3 install rustworkx --break-system-packages
```

#### Zeek
Zeek (version &geq; 6.1.0):
The easiest way is to use the following docker container: ghcr.io/mmguero/zeek:master. Refer to [the repository](https://github.com/mmguero/zeek-docker/pkgs/container/zeek) for more information on usage.

## Getting Started
### Running the GUI

From the parsnip/frontend folder:
```bash
./start_webServer.sh
```

This will drop the user into a bash session running within a docker container.

From there run:
```bash
cd app
python3 app.py
```

Users should now be able to access the frontend in a web browser at: http://127.0.0.1:5000.

Refer to the documentation in the parsnip/docs folder and the next section for more information on the GUI.

### Basic Example
This example shows how to implement a simple protocol using Parsnip.

#### Protocol Information
The MySimpleProtocol protocol runs over TCP port 8888.

A protocol message for our simple protocol consists of a two byte header and a variable length body.
The first byte of the header consists of two 4-bit bitfields. The first four bits represent the protocol version. The last four bits represent the message type. A message type of 0 represents a message for the server. A message type of 1 represents a message for the client. The second byte of the header consists of the length of the packet as an unsigned 8-bit integer. The body consists of a series a bytes where the length of the body is specified by the length field.

A test PCAP of MySimpleProtocol is available in the docs/traces folder of this repository.

#### Constructing the Protocol in Parsnip
When users navigate to the Parsnip frontend using a browser, they will be greeted by the following page:

![Parsnip front page](./images/front.png)

##### Protocol Configuration

Begin by going to the Parser Configuration Page:

![Parser configuration page](./images/empty_config.png)

Press the "Edit Parser Configuration" button and enter the information shown:

![Parser configuration partial](./images/partial_config.png)

Users will need to return to this screen later to specify the Entry Point Structure. After users press the "Save Configuration" button, they should navigate to the "Protocol Ports" tab as shown:

![Parser protocol ports page](./images/empty_ports.png)

Press the "Add Port" button and enter the information shown:

![Add TCP Port](./images/add_port.png)

After a user presses the "Add Port" the port should now be listed as a protocol port as shown:

![TCP Port added](./images/port_added.png)

##### Adding Structures
When working within the frontend, it is best to take a bottom-up approach to defining structures.

For MySimpleProtocol, start by defining the message type enumeration.

First, navigate to the Enums page through the "View/Edit Components" menu as shown:

![Enums Navigation](./images/enums_navigation.png)

Next, press the "Add Enum" button and enter the information shown in the next two images:

![messageType information part 1](./images/messageType_info_1.png)

![messageType information part 2](./images/messageType_info_2.png)

Press the "Add Enum" button to save the enum. The updated information should appear as shown:

![Updated Enum information](./images/updated_enum_page.png)

Next, navigate to the Bitfields page through the "View/Edit Components" menu as shown:

![Enums Navigation](./images/bitfields_navigation.png)

Press the "Add Bitfield" button and enter the information shown in the next two images:

![messageType information part 1](./images/headerBits_info_1.png)

![messageType information part 2](./images/headerBits_info_2.png)

Press the "Add Bitfield Structure" to save the bitfield. The updated information should appear as shown:

![Updated Bitfield Information](./images/updated_bitfields_page.png)

Finally, build the "Object" structures. Navigate to the Objects page through the "View/Edit Components" menu as shown:

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

That is the end of adding structures. Next users should update the configuration with the entry point.

##### Update Configuration

Now that the entry point object is defined, return to the Parser Configuration Page as shown:

![Configuration update](./images/config_before_update.png)

Press the "Edit Parser Configuration" button and set the Parser Entry Point value to the "Message" object as shown:

![Updating Entry Point](./images/finalize_config.png)

Press the "Save Configuration" button to save the updated configuration.

##### Review
Use the frontend to review the parser and look for potential issues. Navigate to the Review page. The page automatically runs checks when loaded. The output should appear as shown:

![Review Results](./images/review_page.png)

As the screenshot shows, there are now Switch/Choice types in the parser, but no other errors or warnings are present.

##### Download the Parsnil files
Press the "Export Parsnip Files" link to download a zip file with the Parsnip Intermediate Language files.

### Running the Backend
Once the Parsnip IL files have been generated by the frontend, users should receive a zip file called "parsnip.zip" which contains a folder with a random string of characters for its name (e.g., 08f4789d-6915-4067-8939-4994c55acbae). Unzip the folder into its own folder. Once that zip file has been unzipped, copy the path to the random string folder as the "input_folder" for the following command.

To build the parser, run from the parsnip/backend folder, replacing input_folder and output_folder as appropriate:
```bash
python3 main.py input_folder output_folder
```

For example,
```bash
python3 main.py ~/Downloads/parsnip/08f4789d-6915-4067-8939-4994c55acbae ~/MyParser
```

The parser code files should now be located in the output_folder directory.

Compile and package as usual. At minimum, Zeek version 6.1.0 is required to take full advantage of all features.

As listed as a current limitation, the user will need to manually update the permissions on the testing/scripts/get-zeek-env file in the output folder to add execution permissions.

### Running the Parser with Zeek

There are multiple ways to run the resulting parser using Zeek. Below is an example of one way to do it.

#### Zkg Install for Testing with a Zeek docker container

##### Initiating a git Repository
In order to use the zkg utility the parser must be part of an up to date (i.e., not dirty) git repository.

The following commands can be used to initialize the repository, replacing output_folder as appropriate:
```bash
cd output_folder
echo "*.log" > .gitignore
git init .
git add -A
git commit -m "Initial Commit"
```

For example,
```bash
cd ~/MyParser
echo "*.log" > .gitignore
git init .
git add -A
git commit -m "Initial Commit"
```

##### Running the Zeek Docker Container
Next, start the zeek container with the parser folder mounted, replacing output_folder and mount_folder (specified by full path) as appropriate:
```bash
docker run -t -i -P --rm -v output_folder:mount_folder:rw --entrypoint /bin/bash ghcr.io/mmguero/zeek:master
```

For example,
```bash
docker run -t -i -P --rm -v $HOME/MyParser:/root/MyParser:rw --entrypoint /bin/bash ghcr.io/mmguero/zeek:master
```

##### Installing the parser
Inside the docker container, navigate to the mounted folder (specified in the previous command) and run the following:
```bash
zkg install .
```

##### Running the parser
Assuming the parser has installed via the previous step, the parser can be run using the following command, replacing pcap_path with the path to a pcap file to test:
```bash
zeek -Cr pcap_path local
```

For example:
```bash
zeek -Cr /root/MyParser/example/test.pcapng local
```

## Syntax Information
Refer to [syntax.md](syntax.md) for more information about writing a parser using Parsnip.
