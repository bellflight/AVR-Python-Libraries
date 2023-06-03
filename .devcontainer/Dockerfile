FROM docker.io/nikolaik/python-nodejs:python3.11-nodejs19-bullseye

WORKDIR /work
ENV PRE_COMMIT_HOME .cache/pre-commit

# install pre-reqs for pyside
RUN apt-get update -y \
 && apt-get install gnupg2 libegl1-mesa libgl1 libxkbcommon-x11-0 libdbus-1-3 -y

# update npm
RUN npm install -g npm
# install vscode-task-runner
RUN pip install vscode-task-runner
