Cme-hw
==============

Core monitoring engine (CME) hardware package.  This package is used to interface with 
the transducer bus on a Raspberry Pi-based CME.

Runs under Python versions: 2.7+.

You can use the package stand-alone after installation, or you can run it as a deployed
package on end-use CME hardware.  Instructions for both are below.

Look in `requirements.txt` to find the dependent packages. 

Stand-Alone Development
-----------------------

**Prerequisites**

* Python 2.7+
* Virtualenv (`pip install virtualenv`)


Clone the Cme-hw project repository to a machine that will support the underlying hardware interface
packages.  Generally this means that you'll need a Raspberry Pi platform with a basic
Raspbian, Minibian, or Alpine Linux kernel and OS running (called "cme-dev" below).  Note that you
must either add an SSH public key to your GitLab profile from the development machine, or copy an
existing SSH public key to the development machine in order to use `git` to clone the project.

```bash
root@cme-dev[~:501] $ git clone git@10.252.64.224:Avalanche/Cme-hw.git
```

Create a virtual environment for the package.  Generally you can keep this within the
same folder as the top-level Cme-hw project.   

```bash
root@cme-dev[~/Cme-hw:502] $ virtualenv cme_hw_venv
```

Activate the virtual environment.

```bash
root@cme-dev[~/Cme-hw:503] $ source cme_hw_venv/bin/activate
```

Install the dependent packages.

```bash
(cme_hw_venv)root@cme-dev[~/Cme-hw:504] $ pip install -r requirements.txt
```

Run the package.

```bash
(cme_hw_venv)root@cme-dev[~/Cme-hw:505] $ python -m cmehw
```

**Note:** See the docker files in the `build` folder for various docker image options.  The `cme-hw-dev.docker`
can be used to generate an Alpine Linux based container for easier Cme-hw development.

**Note:** The packaged version of `python-rrdtool` that is currently available for 
Raspbian/Minibian does NOT support `rrdcached`, so in order to run Cme-hw on a
Raspbian/Minibian system you have to build `python-rrdtool` from newer sources.


Runtime Use
---------------
The Cme-hw package is meant to run under its own docker container on a Cme host system.  See the `build` folder for the various
dockerfile scripts used to generate the Cme-hw container image.

The basic process for building the docker container image is:

1. Create a basic Alpine Linux-based container with Python 2, pip, virtualenv, rrdtool, and bash installed.

    See `build/base-alpine-python.docker`.

2. Create another container image based on the one created above which will be used to build the Python Cme-hw application.  This will add all the necessary build chain tools and libraries to link up the Cme-hw dependencies.  Once the image is built, run it using the Cme-hw project source files as input and it will generate Python wheels for use in the Cme-hw runtime container.

    See `build/build-alpine-python.docker`.

3. Create a final container image also based on the first one created above which will be used for running the built Cme-hw application.  It will be built using the Python wheels generated from the builder image in step 2, above, and when it runs it launches the Cme-hw application.

    See `build/cme-hw-run.docker`.

