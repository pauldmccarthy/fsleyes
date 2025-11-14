FROM ubuntu:24.04
LABEL org.opencontainers.image.authors="Paul McCarthy pauldmccarthy@gmail.com"

ENV PYTHON_VERSION="3.14"
ENV WXPYTHON_VERSION="4.2.4"
ENV DEBIAN_FRONTEND="noninteractive"
ENV LANG="en_GB.UTF-8"
ENV MAMBA_ROOT_PREFIX="/mamba/"

ADD scripts/install_system_deps.sh /scripts/install_system_deps.sh
ADD scripts/install_python_deps.sh /scripts/install_python_deps.sh
ADD scripts/install_dcm2niix.sh    /scripts/install_dcm2niix.sh

RUN /bin/bash /scripts/install_system_deps.sh
RUN /bin/bash /scripts/install_python_deps.sh
RUN /bin/bash /scripts/install_dcm2niix.sh

ENV PATH=/dcm2niix:$PATH
CMD eval "$(/mamba/bin/micromamba shell hook --shell posix)"