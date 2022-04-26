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
{% if colourMode == 'orientation' %}
in  vec3 geomOrient[];
out vec3 fragOrient;
{% elif colourMode == 'vertexData' %}
in  float geomVertexData[];
out float fragVertexData;
{% endif %}

{% if colourMode == 'imageData' or clipMode == 'imageData' %}
in  vec3 geomVertex[];
out vec3 fragVertexWorld;
{% endif %}

{% if clipMode == 'vertexData' %}
in  float geomClipVertexData[];
out float fragClipVertexData;
{% endif %}

/* Vertex position and normal, passed
 * through to fragment shader to
 * calculate lighting.
 */
out vec3 fragVertex;
out vec3 fragNormal;

/*
 * Line width scaling factors along x/y
 * axesa - must be defined in terms of
 * normalised device coordinates
 * (i.e. after MVP has been applied).
 */
uniform vec2 lineWidth;

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
  offset    = normalize(cameraRotation * offset) * vec3(lineWidth, 0) / 2;

  // Lighting is not currently applied
  // to line geometry, but we should
  // be able to calculate the normal
  // as being orthogonal to the
  // rectangle representing the line.
  // fragNormal = normalize(cross(start - offset, start - end));
  fragNormal = vec3(0, 0, 0);

  {% if colourMode == 'orientation' %}
  fragOrient = geomOrient[0];
  {% elif colourMode == 'vertexData' %}
  fragVertexData = geomVertexData[0];
  {% endif %}

  {% if colourMode == 'imageData' or clipMode == 'imageData' %}
  fragVertexWorld = geomVertex[0];
  {% endif %}

  {% if clipMode == 'vertexData' %}
  fragClipVertexData = geomClipVertexData[0];
  {% endif %}

  fragVertex  = start + offset; gl_Position = vec4(fragVertex, 1); EmitVertex();
  fragVertex  = start - offset; gl_Position = vec4(fragVertex, 1); EmitVertex();

  {% if colourMode == 'orientation' %}
  fragOrient = geomOrient[1];
  {% elif colourMode == 'vertexData' %}
  fragVertexData = geomVertexData[1];
  {% endif %}

  {% if colourMode == 'imageData' or clipMode == 'imageData' %}
  fragVertexWorld = geomVertex[1];
  {% endif %}

  {% if clipMode == 'vertexData' %}
  fragClipVertexData = geomClipVertexData[1];
  {% endif %}

  fragVertex  = end + offset; gl_Position = vec4(fragVertex, 1); EmitVertex();
  fragVertex  = end - offset; gl_Position = vec4(fragVertex, 1); EmitVertex();

  EndPrimitive();

}
