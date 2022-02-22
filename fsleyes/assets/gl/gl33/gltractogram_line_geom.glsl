/*
 * Geometry shader for rendering GLTractogram instances.
 * Turns lines into rectangles of arbitrary width.
 */
#version 330

layout (lines) in;
layout (triangle_strip, max_vertices=4) out;

/*
 * Vertex data - passed straight through to
 * fragment shader.
 */
{% for dtype in passThru %}
in  {{ dtype }} geomData{{ loop.index0 }}[];
out {{ dtype }} fragData{{ loop.index0 }};
{% endfor %}

/* Vertex position and normal, passed
 * through to fragment shader to
 *  calculate lighting.
 */
out vec3 fragVertex;
out vec3 fragNormal;

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
  vec3 offset;
  vec3 projstart;
  vec3 projend;

  /*
   * Project the vector onto the viewing plane,
   * so we can figure out an offset to position
   * the rectangle corners (so the rectangle
   * corners are 90 degrees).
   */
  projstart = start - camera * dot(start, camera);
  projend   = end   - camera * dot(end,   camera);
  offset    = projend - projstart;
  offset    = normalize(cameraRotation * offset) * lineWidth / 2;

  // Lighting is not currently applied
  // to line geometry, but we should
  // be able to calculate the normal
  // as being orthogonal to the
  // rectangle representing the line.
  // fragNormal = normalize(cross(start - offset, start - end));
  fragNormal = vec3(0, 0, 0);

  {% for _ in passThru %}
  fragData{{ loop.index0 }} = geomData{{ loop.index0 }}[0];
  {% endfor %}

  fragVertex  = start + offset; gl_Position = vec4(fragVertex, 1); EmitVertex();
  fragVertex  = start - offset; gl_Position = vec4(fragVertex, 1); EmitVertex();

  {% for _ in passThru %}
  fragData{{ loop.index0 }} = geomData{{ loop.index0 }}[1];
  {% endfor %}

  fragVertex  = end + offset; gl_Position = vec4(fragVertex, 1); EmitVertex();
  fragVertex  = end - offset; gl_Position = vec4(fragVertex, 1); EmitVertex();

  EndPrimitive();

}
