
vec3 mesh_lighting(vec3 vertex,  vec3 normal, vec3 lightPos, vec3 colour) {

  vec3 result;

  vec3 lightDir = normalize(lightPos - vertex);
  vec3 viewDir  = normalize(-vertex);
  vec3 angle = normalize(-reflect(lightDir, normal));

  float amb = 0.3;
  float diff = max(dot(normal, lightDir), 0.0);

  float spec = 0.5 * pow(max(dot(angle, viewDir), 0.0), 16);
  spec = clamp(spec, 0.0, 1.0);

  result = colour * vec3(amb + diff + spec);

  return result;
}
