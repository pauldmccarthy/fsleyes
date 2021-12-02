FROM ubuntu:18.04
MAINTAINER Paul McCarthy <pauldmccarthy@gmail.com>

ENV PY_VERSION       "python3.10"
ENV PY_PACKAGES      "python3-pip python3.10-venv"
ENV PY_VENV          "python3.10 -m venv"
ENV WXPYTHON_VERSION "wxPython-4.1.1"
ENV DEBIAN_FRONTEND  "noninteractive"
ENV LANG             "en_GB.UTF-8"

ADD scripts/install_system_deps.sh /scripts/install_system_deps.sh
ADD scripts/install_python.sh      /scripts/install_python.sh
ADD scripts/compile_wxpython4.sh   /scripts/compile_wxpython4.sh
ADD scripts/install_python_deps.sh /scripts/install_python_deps.sh
ADD scripts/install_dcm2niix.sh    /scripts/install_dcm2niix.sh

RUN /bin/bash /scripts/install_system_deps.sh
RUN /bin/bash /scripts/install_python.sh
RUN /bin/bash /scripts/compile_wxpython4.sh
RUN /bin/bash /scripts/install_python_deps.sh
RUN /bin/bash /scripts/install_dcm2niix.sh

ENV PATH /dcm2niix/:$PATH
