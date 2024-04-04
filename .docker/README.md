FSLeyes docker images
=====================

This directory contains a set of Dockerfiles which define Docker images that
are used for FSLeyes testing. These images are available on the Docker hub at
https://hub.docker.com/u/pauldmccarthy/

These images are no longer in use:
 - `fsleyes-py37-wxpy4-gtk3`
 - `fsleyes-py38-wxpy4-gtk3`

These images can be re-built via CI jobs on the fsl/fsleyes/fsleyes GitLab
repository. To build/update an image by hand, follow these steps:


```sh
cd .docker/fsleyes-py310-wxpy4-gtk3
docker build -t pauldmccarthy/fsleyes-py310-wxpy4-gtk3 -f Dockerfile ..
docker login
docker push pauldmccarthy/fsleyes-py310-wxpy4-gtk3
```


The projects which use these docker images are hosted at:

 - https://git.fmrib.ox.ac.uk/fsl/fslpy/
 - https://git.fmrib.ox.ac.uk/fsl/fsleyes/widgets/
 - https://git.fmrib.ox.ac.uk/fsl/fsleyes/props/
 - https://git.fmrib.ox.ac.uk/fsl/fsleyes/fsleyes/
