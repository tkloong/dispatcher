This program is based on [libsvm tool](https://github.com/cjlin1/libsvm/blob/master/tools/grid.py). It is used for dispatching jobs, either on local computer or on remote servers that enable password-less ssh login.

# Requirement

python 3.7.2

# Arguments

1. **--host**: host configuration path. If not specified, local workers will be responsible for all the jobs.

2. **--job**: job configuration path.

3. **--num_local_workers**: number of local workers. You can set  Default: 1

# How to run

1. Modify host configuration file. The configuration file should look like this.

```
<username>@<server_ip1>
<username>@<server_ip2>
<username>@<server_ip3>
```

2. Modify job configuration file. Each line corresponding to a shell command. The program will automatically dispatch jobs to the local workers and the hosts specified in the host configuration file.

Now, the configuration file should look like this.

```
python3 demo.py -n 5
python3 demo.py -n 2
python3 demo.py -n 3
python3 demo.py -n 6
python3 demo.py -n 1
python3 demo.py -n 4
```

# Demo

```
$ python3 dispatcher.py --num_local_workers 4 --job jobs.config
```
