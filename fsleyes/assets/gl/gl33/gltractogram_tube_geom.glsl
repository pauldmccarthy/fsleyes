/*
 * Geometry shader for rendering GLTractogram instances.
 * Turns lines into tubes/cylinders.
 */
#version 330

layout (lines) in;
layout (triangle_strip, max_vertices=22) out;

/*
 * Vertex data, pssed straight
 * through to fragment shader.
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
 * Vertex position and normal,
 * passed to fragment shader
 * to calculate lighting.
 */
out vec3 fragVertex;
out vec3 fragNormal;


/*
 * Tube width scaling factors along x/y
 * axesa - must be defined in terms of
 * normalised device coordinates
 * (i.e. after MVP has been applied).
 */
uniform vec2 lineWidth;

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
  float angle;
  float cosa;
  float sina;
  vec3  offset;
  vec3  scaledOffset;
  for (int i = 0; i <= res; i++) {
    angle = 6.283185307179586 * (float(i) / resolution);
    cosa  = cos(angle);
    sina  = sin(angle);

    // Offset from the line at the current angle,
    // on the plane perpendicular to the line.
    offset       = normalize(((normalx * cosa) + (normaly * sina)));
    scaledOffset = offset * vec3(lineWidth, 0) / 2;

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

    fragVertex  = start + scaledOffset;
    fragNormal  = offset;
    gl_Position = vec4(fragVertex, 1);
    EmitVertex();

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

    fragVertex  = end + scaledOffset;
    fragNormal  = offset;
    gl_Position = vec4(fragVertex, 1);
    EmitVertex();
  }
  EndPrimitive();
}
