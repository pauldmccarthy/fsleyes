/*
 * Fragment shader for colouring GLTractogram instances,
 * where streamlines are coloured according to their
 * orientation.
 */
#version 120

uniform vec4  xColour;
uniform vec4  yColour;
uniform vec4  zColour;
uniform float colourScale;
uniform float colourOffset;


/* Streamline orientation corresponding to this fragment. */
varying vec3 fragData;

void main(void) {

  vec4 colour = fragData.x * xColour +
                fragData.y * yColour +
                fragData.z * zColour;
  colour.a    = (xColour.a +
                 yColour.a +
                 zColour.a) / 3;

  colour.xyz = colour.xyz * colourScale + colourOffset;

  gl_FragColor = colour;
}
