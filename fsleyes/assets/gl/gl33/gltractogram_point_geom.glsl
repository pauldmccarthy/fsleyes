/*
 * Geometry shader for rendering GLTractogram instances.
 * Turns individual streamline points into 2D polygons.
 */
#version 330

layout (points) in;
layout (triangle_strip, max_vertices=26) out;

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

/*
 * Not set.
 */
out vec3 fragVertex;
out vec3 fragNormal;

/*
 * Horizontal/vertical width / scaling factors
 */
uniform float xscale;
uniform float yscale;

/* Angular resolution */
uniform int resolution;

void main(void) {

  int   i;
  vec3  vertex;
  int   res    = clamp(resolution, 3, 10);
  vec3  origin = gl_in[0].gl_Position.xyz;
  float delta  = 6.283185307179586 / res;
  float angle  = delta;

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

  // avoid the initial calls to sin(0)/cos(0)
  gl_Position = vec4(origin.x, origin.y + yscale, origin.z, 1);
  EmitVertex();
  gl_Position.xyz = origin;
  EmitVertex();

  for (i = 1; i < res; i++) {
    vertex.xyz = origin.xyz;
    vertex.x  += sin(angle) * xscale;
    vertex.y  += cos(angle) * yscale;
    angle      = angle + delta;

    gl_Position.xyz = vertex;
    EmitVertex();
    gl_Position.xyz = origin;
    EmitVertex();
  }
  gl_Position.xyz = vec3(origin.x, origin.y + yscale, origin.z);
  EmitVertex();

  EndPrimitive();
}
