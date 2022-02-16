/*
 * Geometry shader for rendering GLTractogram instances.
 * Turns lines into tubes/cylinders.
 */
#version 330

layout (lines) in;
layout (triangle_strip, max_vertices=40) out;

/*
 * Line orientation vector. Passed
 * straight through to fragment shader.
 */
in  vec3 geomOrient[];
out vec3 fragOrient;

/*
 * Line/cylinder width - must be defined
 * in terms of normalised device coordinates
 * (i.e. after MVP has been applied).
 */
uniform float lineWidth;

/*
 * Cylinder resolution - it will be drawn
 * with resolution * 2 triangles.
 */
uniform int resolution;

void main(void) {

  vec3 start = gl_in[0].gl_Position.xyz;
  vec3 end   = gl_in[1].gl_Position.xyz;
  vec3 line  = normalize(end - start);

  /*
   * clamp resolution at 10, to ensure that
   * this shader will never exceed max_vertices.
   */
  int res = clamp(resolution, 3, 10);

  /*
   * Find two vectors which define the
   * plane perpendicular to the line.
   * First one is from the cross product
   * of the line and an arbitrary vector.
   */
  vec3 normalx = cross(line, vec3(1, 0, 0));
  if (length(normalx) == 0) {
    normalx = cross(line, vec3(0, 1, 0));
  }
  normalx = normalx;

  /*
   * Second is from the cross product of
   * the line and trhe first vector.
   */
  vec3 normaly = cross(line, normalx);

  /*
   * Generate a series of vertices around both
   * line ends, by rotating around the line
   * <resolution> times.
   */
  for (float i = 0; i < res; i++) {
    float angle = 6.283185307179586 * (i / (resolution - 1));
    float cosa  = cos(angle);
    float sina  = sin(angle);

    // Offset from the line at the current angle,
    // on the plane perpendicular to the line.
    vec3 offset = normalize(((normalx * cosa) + (normaly * sina))) * lineWidth;

    fragOrient  = geomOrient[0];
    gl_Position = vec4(start + offset, 1);
    EmitVertex();
    fragOrient  = geomOrient[1];
    gl_Position = vec4(end   + offset, 1);
    EmitVertex();
  }
  EndPrimitive();
}
