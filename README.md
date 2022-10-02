# mptcp-experiment

This project simulate and evalute MPTCP with various options on dual conectivity infrastructure. This experiment use two path one is NR and the other one is LTE; simulation of NR is done by ns3-mmwave module and simulation of LTE is done by official mudle of ns-3.

Here is the small list of what options are evaluted:
* Various congection controll algorithm
* Various path manager mechanism
* Various scheduler algorithms
* Different distances
* Different file size
* etc...

Simulation is done with the help of DCE.

## Integrate ns3-mmwave with ns-3
First of all, all of these instructions are done in ubunut 16.
Since this integration is comes with so much problems; there is two repository that are fixed bugs and integration procedure problems:
https://github.com/sod-lol/ns-3-dev-git
https://github.com/sod-lol/ns-3-dce

Each dce version is integrate with specific version of ns3-mmwave and all of versions that could be intergated is integrated and completed in each branch in the above repositories. and for intergration with two repositories with each an another following commands should run(we integrate ns3-mmwave V5.0):

```bash
mkdir playground
cd playground/
git clone https://github.com/sod-lol/ns-3-dev-git
mkdir install
git clone https://github.com/sod-lol/ns-3-dce
cd ns-3-dev-git/
sudo add-apt-repository ppa:ubuntu-toolchain-r/test
sudo apt update
sudo apt install g++-7 -y
sudo apt install g++-7 gcc-7 -y
rm -rf /usr/bin/gcc
rm -rf /usr/bin/g++
ln -s /usr/bin/gcc-7 /usr/bin/gcc
ln -s /usr/bin/g++-7 /usr/bin/g++
CXXFLAGS_EXTRA="-O3";sudo -H ./waf configure -d optimized --prefix=$HOME/playground/install
CXXFLAGS_EXTRA="-O3" sudo -H ./waf build
./waf install
cd ..
```
At this point we successfully built and installed ns3-mmwave with ns-3.

For enabling MPTCP in DCE we should build specific branch of libos:
```bash
git clone https://github.com/libos-nuse/net-next-nuse -b mptcp_trunk_libos --depth=1
sudo git config --global url."https://github.com/".insteadOf git://github.com/
cd net-next-nuse/
```

Copy .config file to net-next-nuse folder and after that execute following commands:
```bash
apt install bc
rm -rf /usr/bin/g++
rm -rf /usr/bin/gcc
ln -s /usr/bin/g++-5 /usr/bin/g++
ln -s /usr/bin/gcc-5 /usr/bin/gcc
make library ARCH=lib -j 8
cp arch/lib/tools/libsim-linux-4.1.0.so .
cd ..
```

Now we should build and install DCE:
```bash
rm -rf /usr/bin/gcc
rm -rf /usr/bin/g++
ln -s /usr/bin/gcc-7 /usr/bin/gcc
ln -s /usr/bin/g++-7 /usr/bin/g++
cd ns-3-dce/
CXXFLAGS_EXTRA="-O3" sudo -H ./waf configure --with-ns3=$HOME/playground/install  --enable-opt --enable-kernel-stack=$HOME/playground/net-next-nuse/arch --prefix=$HOME/playground/install
CXXFLAGS_EXTRA="-O3" sudo -H ./waf build
CXXFLAGS_EXTRA="-O3" sudo -H ./waf install
cd ..
```

After installing DCE there is one more step to enable MPTCP in DCE:
```bash
cp net-next-nuse/*.so install/bin_dce/
cd install/bin_dce/
rm -rf liblinux.so
ln -s libsim-linux-4.1.0.so liblinux.so
cd ../..
```

At this point we successfully installed and integrated ns3-mmwave with ns-3 and also enabled MPTCP in DCE. Now we can run mmwave example:
```bash
cd ns-3-dce/
CXXFLAGS_EXTRA="-O3" sudo -H ./waf --enable-opt --run dce-example-mptcp-mmwave
```

## PTools
PTools is simple tool that written specific for this project; The reason why this tool created is that because each single simulation takes so much time(around 3 ~ 5 h) it would be tedious that all of options and vrious senarios run sequentialy, and it was esential that all of simulaition run in background because each time ssh disconnected from the server the whole simulation should run again.

PTools run on python3.7, so make sure python3.7 installed and after that install fastapi with pip.

PTools service can run by the following command:
```bash
./setup-service.sh
```
And also can be remove:
```bash
./setup-service.sh k
```

Sending task to PTools deamon can be done by serveral ways but the easiest one is sending task that written in json file; here is the example of json file:
```json
[{
    "process_name": "scalable_binder_default",
    "process_directory": "/root/playground/ns-3-dce-6",
    "process_binary": "./waf",
    "process_example_name": "first-scenario",
    "process_identity": "04216daa-7e8f-4b39-a72e-5a3ab4ef6866",
    "process_depend_on": "8a6985ba-2040-4043-8e45-3d2d2c3f2d5d",
    "process_binary_options": "--enable-opt --run \"first-scenario --ccAlgo=scalable --pathM=binder --scheAlgo=default\"",
    "nice_value": -20,
    "ionice_type": 1,
    "ionice_value": 0,
    "cpu_affinity": [],
    "scheduler_type": "-r",
    "scheduler_value": 99,
    "pre_script": {
        "use_script": true,
        "script_path": "/root/playground/ns-3-dce-6/prescript.py",
        "script_use_shell": false,
        "pass_args": ""
    },
    "post_script": {
        "use_script": true,
        "script_path": "/root/playground/ns-3-dce-6/post_process.py",
        "script_use_shell": false,
        "pass_args": "scalable lte-mmwave2"
    }
}]
```
The above json simply created by taskgenerator script. For sending the tasks to daemon following command should work:
```bash
python3.7 ptools.py -t task_list.json
```

