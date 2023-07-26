#!/bin/bash

set -e

##########################################################
# The setup_ssh scrip does the following:
#
#  - Sets up key-based SSH login, and
#    installs the private keys, so
#    we can connect to servers.
#
#  - Configures git, and adds the
#    upstream repo as a remote
#
# (see https://docs.gitlab.com/ce/ci/ssh_keys/README.html)
#
# NOTE: It is assumed that non-docker
#       executors are already configured
#       (or don't need any configuration).
##########################################################


if [[ -f /.dockerenv ]]; then

  # We have to use different host names to connect
  # to the docker daemon host on mac as opposed
  # to on linux.
  #
  # On linux (assuming the docker job is running
  # with --net=host), we can connect via
  # username@localhost.
  #
  # On mac, we have to connect via
  # username@host.docker.internal
  if [[ "$CI_RUNNER_TAGS" == *"macOS"* ]]; then
    if [[ "$FSL_HOST" == *"@localhost" ]]; then
      FSL_HOST=${FSL_HOST/localhost/host.docker.internal}
    fi
  fi

  apt-get update -y                           || yum -y check-update                     || true;
  apt-get install -y git rsync openssh-client || yum install -y git rsync openssh-client || true;

  eval $(ssh-agent -s);
  mkdir -p $HOME/.ssh;

  echo "$SSH_PRIVATE_KEY_FSL_DOWNLOAD" > $HOME/.ssh/id_fsl_download;

  chmod go-rwx $HOME/.ssh/id_*;
  ssh-add $HOME/.ssh/id_fsl_download;

  ssh-keyscan ${FSL_HOST##*@} >> $HOME/.ssh/known_hosts;

  touch $HOME/.ssh/config;

  echo "Host fsldownload"                            >> $HOME/.ssh/config;
  echo "    HostName ${FSL_HOST##*@}"                >> $HOME/.ssh/config;
  echo "    User ${FSL_HOST%@*}"                     >> $HOME/.ssh/config;
  echo "    IdentityFile $HOME/.ssh/id_fsl_download" >> $HOME/.ssh/config;

  echo "Host *"                                      >> $HOME/.ssh/config;
  echo "    IdentitiesOnly yes"                      >> $HOME/.ssh/config;

  git config --global user.name  "Gitlab CI";
  git config --global user.email "gitlabci@localhost";

  if [[ `git remote -v` == *"upstream"* ]]; then
      git remote remove upstream;
  fi;
  git remote add upstream "$UPSTREAM_URL:$UPSTREAM_PROJECT";
fi
