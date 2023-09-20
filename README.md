# apollo-hr-agent

# prepare running env

* The docker way

```
# build docker dev container, it will auto install all the packages in requirements.txt
make build

# start a shell from dev container
make shell
```

* The pip way

```
pip install -r requirements.txt
```

# how to use

```
# for 1st time, use following command for creating a new config file
# it will default be saved as {user}.json via your inputed user name
python apollo.py init --username <user> --password <password> --company <company>

# test your config file 
python apollo.py --config user test

# for other usage
python apollo.py --help
```
