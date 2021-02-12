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
