/*
 * Fragment shader for the VoxelSelection annotation.
 */
#version 120

{% if textureIs2D %}
uniform sampler2D tex;
{% else %}
uniform sampler3D tex;
{% endif %}

uniform vec4 colour;
varying vec3 fragTexCoord;

void main(void) {

  float texValue;

  {% if textureIs2D %}
  texValue = texture2D(tex, fragTexCoord.xy).r;
  {% else %}
  texValue = texture3D(tex, fragTexCoord).r;
  {% endif %}

  if (texValue != 0) {
    gl_FragColor = colour;
  }
  else {
    discard;
  }
}
