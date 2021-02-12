/*
 * This file provides functions for applying a simple Phong lighting model.
 * These functions are used by the glmesh and glvolume 3D fragment shaders.
 *
 * Author: Paul McCarthy <pauldmccarthy@gmail.com>
 */

/*
 * Apply the Phong lighting model to the given colour.
 */
vec3 phong_lighting(vec3 vertex, vec3 normal, vec3 lightPos, vec3 colour) {

  vec3 result;

  if (!gl_FrontFacing)
    normal = -normal;

  vec3 lightDir = normalize(lightPos - vertex);
  vec3 viewDir  = normalize(-vertex);
  vec3 angle    = normalize(reflect(lightDir, normal));

  float amb  = 0.5;
  float diff = clamp(dot(normal, lightDir), 0.0, 1.0);
  float spec = clamp(pow(max(dot(angle, viewDir), 0.0), 64), 0.0, 1.0);

  result = colour * vec3(amb + diff + spec);

  return result;
}

/*
 * Estimate the intensity gradient at a specific location within a volume.
 * Surface normals for volume lighting are based on intensity gradients.
 */
vec3 volume_gradient(vec3      texCoord,
                     sampler3D imageTexture,
                     float     stepSize) {

  vec3 xstep = vec3(stepSize, 0, 0);
  vec3 ystep = vec3(0, stepSize, 0);
  vec3 zstep = vec3(0, 0, stepSize);

  float xback = texture3D(imageTexture, texCoord - xstep).x;
  float xfwd  = texture3D(imageTexture, texCoord + xstep).x;
  float yback = texture3D(imageTexture, texCoord - ystep).x;
  float yfwd  = texture3D(imageTexture, texCoord + ystep).x;
  float zback = texture3D(imageTexture, texCoord - zstep).x;
  float zfwd  = texture3D(imageTexture, texCoord + zstep).x;

  return vec3(xback - xfwd, yback - yfwd, zback - zfwd) / (2 * stepSize);
}

