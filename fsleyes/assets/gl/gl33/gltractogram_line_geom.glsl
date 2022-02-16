/*
 * Geometry shader for rendering GLTractogram instances.
 * Turns lines into rectangles of arbitrary width.
 */
#version 330

layout (lines) in;
layout (triangle_strip, max_vertices=4) out;

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

/* Not used */
uniform int resolution;

/*
 * Camera direction vector, and a rotation matrix
 * which rotates 90 degrees about that vector.
 * Used to position vertices on the rectangle
 * that is used to represent each line.
 */
uniform vec3 camera;
uniform mat3 cameraRotation;


void main(void) {

  vec3 start = gl_in[0].gl_Position.xyz;
  vec3 end   = gl_in[1].gl_Position.xyz;
  vec3 line  = normalize(end - start);
  vec3 offset;

  /*
   * Project the vector onto the viewing plane,
   * so we can figure out an offset to position
   * the rectangle corners (so the rectangle
   * corners are 90 degrees).
   */
  line   = line - (camera * dot(line, camera));
  offset = normalize(cameraRotation * line) * lineWidth / 2;

  fragOrient  = geomOrient[0];
  gl_Position = vec4(start - offset, 1); EmitVertex();
  gl_Position = vec4(start + offset, 1); EmitVertex();
  fragOrient  = geomOrient[1];
  gl_Position = vec4(end   - offset, 1); EmitVertex();
  gl_Position = vec4(end   + offset, 1); EmitVertex();
  EndPrimitive();

}
